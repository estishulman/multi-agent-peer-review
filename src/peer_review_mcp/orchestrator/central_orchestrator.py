import time
from dataclasses import dataclass, field
from typing import Optional, List
import logging

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
    Phase B: optional polishing

    Orchestrates a multi-phase peer review system:
    1. Validation: Identifies potential issues with the question
    2. Synthesis: Generates answer considering review points
    3. Polishing: Optional improvement pass based on quality metrics
    """

    def __init__(self):
        logger.info("CentralOrchestrator initialized")
        self.polishing_engine = PolishingEngine()
        self.polish_llm = GeminiClient()

    async def process(self, *, question: str, context_summary: Optional[str] = None) -> dict:
        """
        Main orchestration entry point.

        Args:
            question: The user's question
            context_summary: Optional short summary of relevant context (not full chat history!)
        """
        t0 = time.time()
        decision_log: list[str] = []

        logger.info("Starting process for new question: %s", question[:100])

        # Phase A – validation + synthesis (always run)
        review_points, answer = self._run_phase_a(question, context_summary, decision_log)

        # If answer is None, the system failed - let the client's agent handle it
        if answer is None:
            logger.warning("Phase A failed to generate answer, returning None for client fallback")
            processing_time_ms = int((time.time() - t0) * 1000)
            self._log_decision_trace(decision_log, processing_time_ms)
            return {
                "answer": None,
                "meta": {
                    "used_peer_review": False,
                    "review_points_count": len(review_points),
                    "quality_score": None,
                    "polishing_applied": False,
                    "processing_time_ms": processing_time_ms,
                    "error": "answer_generation_failed"
                },
            }

        # Quality assessment
        quality_score = self._heuristic_quality_score(len(review_points))
        decision_log.append(f"quality_score_heuristic: {quality_score}")
        logger.debug("Quality score calculated: %.2f", quality_score)

        # Phase B – optional polishing
        should_polish, polish_reason = self._decide_phase_b(
            review_points_count=len(review_points),
            quality_score=quality_score,
        )
        decision_log.append(f"phase_b_decision: {should_polish} ({polish_reason})")
        logger.debug("Phase B decision: polish=%s reason=%s", should_polish, polish_reason)

        if should_polish:
            answer = self._run_phase_b(question, answer, context_summary, decision_log)

        processing_time_ms = int((time.time() - t0) * 1000)
        self._log_decision_trace(decision_log, processing_time_ms)

        logger.info("Process complete in %dms", processing_time_ms)

        return {
            "answer": answer,
            "meta": {
                "used_peer_review": True,
                "review_points_count": len(review_points),
                "quality_score": quality_score,
                "polishing_applied": should_polish,
                "processing_time_ms": processing_time_ms
            },
        }

    def _run_phase_a(self, question: str, context_summary: Optional[str], decision_log: list[str]) -> tuple[List[ReviewPoint], str]:
        """Phase A: Validate question and generate answer with context awareness."""
        logger.debug("Running Phase A for question: %s", question[:100])

        # STEP 1: validate_tool gets QUESTION + CONTEXT_SUMMARY
        review_points = []
        try:
            validation = validate_tool(question, context_summary)
            review_points = validation.get("items", [])
            if not isinstance(review_points, list):
                logger.warning("validate_tool returned non-list items, defaulting to empty list")
                review_points = []
        except Exception as e:
            logger.exception("validate_tool failed in _run_phase_a: %s", str(e))
            review_points = []

        decision_log.append(f"review_points_count: {len(review_points)}")
        logger.debug("Phase A validation complete: %d review points", len(review_points))

        # STEP 2: answer_tool gets QUESTION + CONTEXT_SUMMARY + REVIEW_POINTS
        answer = None
        try:
            result = answer_tool(
                question=question,
                context_summary=context_summary,
                review_points=review_points,
            )
            answer = result.get("answer")
        except Exception as e:
            logger.exception("answer_tool failed in _run_phase_a: %s", str(e))
            decision_log.append(f"answer_tool_error: {type(e).__name__}")
            answer = None  # ← Fallback: הן None, האיגנט יענה בעצמו

        return review_points, answer

    def _decide_phase_b(self, *, review_points_count: int, quality_score: float) -> tuple[bool, str]:
        """Decide whether to apply polishing based on review and quality metrics."""
        if review_points_count >= 6:
            return True, "many_review_points"
        if quality_score < 0.9:
            return True, "low_quality_score"
        return False, "good_enough"

    def _run_phase_b(self, question: str, answer: str, context_summary: Optional[str], decision_log: list[str]) -> str:
        """Phase B: Polish answer based on review suggestions."""
        logger.debug("Running Phase B polishing")

        comments = self.polishing_engine.review_for_polish(
            question=question,
            answer=answer,
            context_summary=context_summary,
        )
        decision_log.append(f"polish_comments_count: {len(comments)}")
        logger.debug("Polish review complete: %d comments", len(comments))

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

    def _heuristic_quality_score(self, review_points_count: int) -> float:
        """Calculate quality score based on review points count."""
        if review_points_count <= 2:
            return 0.95
        if review_points_count <= 5:
            return 0.88
        if review_points_count <= 8:
            return 0.80
        return 0.72

    def _log_decision_trace(self, decision_log: list[str], processing_time_ms: int):
        """Log the full decision trace for debugging."""
        logger.info(
            "Decision trace: %s | processing_time_ms: %d",
            " | ".join(decision_log),
            processing_time_ms,
        )



