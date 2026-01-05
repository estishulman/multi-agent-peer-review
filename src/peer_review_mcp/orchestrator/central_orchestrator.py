import time
import logging
from typing import Optional, List

from peer_review_mcp.tools.validate_tool import validate_tool
from peer_review_mcp.tools.answer_tool import answer_tool
from peer_review_mcp.tools.polishing_engine import PolishingEngine
from peer_review_mcp.models.review_point import ReviewPoint

from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.prompts.polish_synthesis import POLISH_SYNTHESIS_PROMPT

logger = logging.getLogger(__name__)


class CentralOrchestrator:
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
        self.polishing_engine = PolishingEngine()
        self.polish_llm = GeminiClient()

    async def process(self, *, question: str, context_summary: Optional[str] = None) -> dict:
        t0 = time.time()
        decision_log: list[str] = []

        logger.info("Starting process for new question: %s", question[:100])

        # Phase A – validation + synthesis
        review_points, synthesis = self._run_phase_a(
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
        confidence = synthesis.get("confidence", 0.8)
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
            answer = self._run_phase_b(
                question, answer, context_summary, decision_log
            )

        processing_time_ms = int((time.time() - t0) * 1000)
        self._log_decision_trace(decision_log, processing_time_ms)

        return {
            "answer": answer,
            "meta": {
                "used_peer_review": True,
                "confidence": confidence,
                "review_points_count": len(review_points),
                "polishing_applied": should_polish,
            },
        }

    # Phase A

    def _run_phase_a(
        self,
        question: str,
        context_summary: Optional[str],
        decision_log: list[str],
    ) -> tuple[List[ReviewPoint], Optional[dict]]:
        logger.debug("Running Phase A for question: %s", question[:100])

        # Step 1: validation
        review_points: list[ReviewPoint] = []
        try:
            validation = validate_tool(question, context_summary)
            review_points = validation.get("items", [])
            if not isinstance(review_points, list):
                review_points = []
        except Exception:
            logger.exception("validate_tool failed")
            review_points = []

        decision_log.append(f"review_points_count: {len(review_points)}")

        # Step 2: synthesis
        try:
            synthesis = answer_tool(
                question=question,
                context_summary=context_summary,
                review_points=review_points,
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

        if model_requested_polish:
            return True, "model_requested_polish"

        if model_confidence < 0.85:
            return True, "low_model_confidence"

        if review_points_count >= 6:
            return True, "many_review_points"

        return False, "good_enough"

    # Phase B execution
    
    def _run_phase_b(
        self,
        question: str,
        answer: str,
        context_summary: Optional[str],
        decision_log: list[str],
    ) -> str:
        logger.debug("Running Phase B polishing")

        comments = self.polishing_engine.review_for_polish(
            question=question,
            answer=answer,
            context_summary=context_summary,
        )
        decision_log.append(f"polish_comments_count: {len(comments)}")

        if not comments:
            return answer

        formatted = "\n".join(f"- {c.text}" for c in comments)

        prompt = POLISH_SYNTHESIS_PROMPT.format(
            question=question,
            answer=answer,
            comments=formatted,
            context=context_summary if context_summary else "(No previous context)",
        )

        polished = self.polish_llm.generate(prompt).strip()
        return polished or answer

    
    # Helpers
    
    def _heuristic_quality_score(self, review_points_count: int) -> float:
        if review_points_count <= 2:
            return 0.95
        if review_points_count <= 5:
            return 0.88
        if review_points_count <= 8:
            return 0.80
        return 0.72

    def _log_decision_trace(self, decision_log: list[str], processing_time_ms: int):
        logger.info(
            "Decision trace: %s | processing_time_ms: %d",
            " | ".join(decision_log),
            processing_time_ms,
        )
