import time
import logging
from typing import Optional, List

from peer_review_mcp.tools.validate_tool import validate_tool
from peer_review_mcp.tools.answer_tool import answer_tool
from peer_review_mcp.tools.polishing_engine import PolishingEngine
from peer_review_mcp.models.review_point import ReviewPoint

from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.LLM.limiter import configure_llm_concurrency
from peer_review_mcp.config import LLM_MAX_CONCURRENCY
from peer_review_mcp.prompts.polish_synthesis import POLISH_SYNTHESIS_PROMPT

logger = logging.getLogger(__name__)


class CentralOrchestrator:  # Orchestrates the multi-phase peer-review flow (validation, synthesis, polishing)
    """
    Hybrid Orchestrator

    Phase A: validate -> answer (always run)
    Phase B: optional polishing (decision uses model self-assessment)

    Orchestrates a multi-phase peer review system:
    1. Validation: Identifies potential issues with the question
    2. Synthesis: Generates answer considering review points
       + model confidence & polish recommendation
    3. Polishing: Optional improvement pass
    """

    def __init__(self):
        logger.info("CentralOrchestrator initialized")
        if LLM_MAX_CONCURRENCY:
            configure_llm_concurrency(LLM_MAX_CONCURRENCY)
        self.polishing_engine = PolishingEngine()
        self.polish_llm = GeminiClient()

    async def process(self, *, question: str, context_summary: Optional[str] = None) -> dict:
        """
        Orchestrates the multi-phase peer review process.

        Args:
            question: The question to process.
            context_summary: Optional context about previous discussion.

        Returns:
            A dictionary containing the final answer and metadata about the process.
            Metadata includes:
                - used_peer_review: Whether peer review was applied.
                - confidence: Model confidence in the answer.
                - review_points_count: Number of review points identified.
                - polishing_applied: Whether polishing was applied.
        """
        t0 = time.time()  # Start measuring the processing time for performance tracking
        decision_log: list[str] = []

        logger.info("Starting process for new question: %s", question[:100])  # Log the first 100 characters of the question to avoid overly long logs

        # Phase A – validation + synthesis
        review_points, synthesis = await self._run_phase_a(
            question, context_summary, decision_log
        )

        if synthesis is None:
            logger.warning("Phase A failed to generate answer")
            processing_time_ms = int((time.time() - t0) * 1000)
            self._log_decision_trace(decision_log, processing_time_ms)
            return {
                "answer": None,
                "meta": {
                    "used_peer_review": False,
                    "review_points_count": len(review_points),
                    "polishing_applied": False,
                    "error": "answer_generation_failed",
                },
            }

        answer = synthesis["answer"]
        confidence = synthesis.get("confidence", 0.8)  # Default confidence to 0.8 if not provided
        needs_polish = synthesis.get("needs_polish", False)

        decision_log.append(f"model_confidence: {confidence}")
        decision_log.append(f"model_requested_polish: {needs_polish}")

        # Heuristic quality score (still useful as a secondary signal)
        quality_score = self._heuristic_quality_score(len(review_points))
        decision_log.append(f"quality_score_heuristic: {quality_score}")

        # Phase B decision
        should_polish, polish_reason = self._decide_phase_b(
            review_points_count=len(review_points),
            quality_score=quality_score,
            model_confidence=confidence,
            model_requested_polish=needs_polish,
        )
        decision_log.append(f"phase_b_decision: {should_polish} ({polish_reason})")

        if should_polish:
            answer = await self._run_phase_b(
                question, answer, context_summary, decision_log
            )

        processing_time_ms = int((time.time() - t0) * 1000)
        self._log_decision_trace(decision_log, processing_time_ms)

        return {
            "answer": answer,
            "meta": {
                "used_peer_review": True,
                "review_points_count": len(review_points),
                "polishing_applied": should_polish,
            },
        }

    # Phase A

    async def _run_phase_a(
        self,
        question: str,
        context_summary: Optional[str],
        decision_log: list[str],
    ) -> tuple[List[ReviewPoint], Optional[dict]]:
        """
        Executes Phase A: validation and synthesis.

        Args:
            question: The question to validate and synthesize an answer for.
            context_summary: Optional context about previous discussion.
            decision_log: A list to record decisions made during the process.

        Returns:
            A tuple containing:
                - A list of ReviewPoint objects representing validation results.
                - A dictionary with synthesis results, including the generated answer.
        """
        logger.debug("Running Phase A for question: %s", question[:100])  # Log the first 100 characters of the question

        # Step 1: Validation
        # This step uses the validate_tool to analyze the question and context.
        # It identifies potential issues or weaknesses in the question and returns
        # a list of review points that highlight these issues.
        review_points: list[ReviewPoint] = []
        try:
            validation = await validate_tool(
                question, context_summary
            )  # Analyze the question and context asynchronously
            review_points = validation.get("items", [])  # Extract review points from the validation results
            if not isinstance(review_points, list):
                review_points = []  # Ensure review_points is a list
        except Exception:
            logger.exception("validate_tool failed")
            review_points = []

        decision_log.append(f"review_points_count: {len(review_points)}")

        # Step 2: Synthesis
        # This step uses the answer_tool to generate an answer based on the question,
        # context, and the review points identified in the validation step.
        # The synthesis process considers the review points to improve the quality
        # and relevance of the generated answer.
        try:
            synthesis = await answer_tool(
                question=question,
                context_summary=context_summary,
                review_points=review_points,  # Pass review points to the synthesis tool
            )
        except Exception:
            logger.exception("answer_tool failed")
            return review_points, None

        return review_points, synthesis

    # Phase B decision

    def _decide_phase_b(
        self,
        *,
        review_points_count: int,
        quality_score: float,
        model_confidence: float,
        model_requested_polish: bool,
    ) -> tuple[bool, str]:
        """
        Decide whether to proceed to Phase B (polishing).

        Args:
            review_points_count: Number of review points identified in Phase A.
            quality_score: Heuristic quality score based on review points.
            model_confidence: Confidence score from the synthesis model.
            model_requested_polish: Whether the model explicitly requested polishing.

        Returns:
            A tuple containing:
                - A boolean indicating whether to proceed to Phase B.
                - A string explaining the reason for the decision.
        """
        # Policy thresholds chosen to trade off quality vs latency/cost in production.
        if model_requested_polish:
            return True, "model_requested_polish"

        if model_confidence < 0.85:
            return True, "low_model_confidence"

        if review_points_count >= 8:
            return True, "many_review_points"

        return False, "good_enough"

    # Phase B execution

    async def _run_phase_b(
        self,
        question: str,
        answer: str,
        context_summary: Optional[str],
        decision_log: list[str],
    ) -> str:
        """
        Execute Phase B: polishing the answer.

        Args:
            question: The original question.
            answer: The synthesized answer to polish.
            context_summary: Optional context about previous discussion.
            decision_log: A list to record decisions made during the process.

        Returns:
            The polished answer, or the original answer if no polishing was applied.
        """
        logger.debug("Running Phase B polishing")

        comments = await self.polishing_engine.review_for_polish(
            question=question,
            answer=answer,
            context_summary=context_summary,
        )  # Generate polishing comments asynchronously
        decision_log.append(f"polish_comments_count: {len(comments)}")

        if not comments:
            return answer  # Return the original answer if no comments were generated

        formatted = "\n".join(f"- {c.text}" for c in comments)  # Format comments as a bullet list

        prompt = POLISH_SYNTHESIS_PROMPT.format(
            question=question,
            answer=answer,
            comments=formatted,
            context=context_summary if context_summary else "(No previous context)",
        )

        polished = await self.polish_llm.generate_async(
            prompt
        )  # Generate the polished answer asynchronously
        polished = polished.strip()
        return polished or answer  # Return the polished answer, or the original if polishing failed

    # Helpers

    def _heuristic_quality_score(self, review_points_count: int) -> float:
        # Heuristic mapping: more review points imply higher risk, so score drops.
        if review_points_count <= 2:
            return 0.95
        if review_points_count <= 5:
            return 0.88
        if review_points_count <= 8:
            return 0.80
        return 0.72

    def _log_decision_trace(self, decision_log: list[str], processing_time_ms: int):
        # Log the decision trace and the total processing time for debugging and analysis.
        logger.info(
            "Decision trace: %s | processing_time_ms: %d",
            " | ".join(decision_log),
            processing_time_ms,
        )
