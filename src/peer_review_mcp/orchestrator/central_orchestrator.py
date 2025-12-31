import json
import logging
from dataclasses import dataclass, field
from typing import Optional, List

from peer_review_mcp.tools.validate_tool import validate_tool
from peer_review_mcp.tools.answer_tool import answer_tool
from peer_review_mcp.tools.baseline_answer_tool import BaselineAnswerTool
from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.prompts.phase_a_decision import PHASE_A_DECISION_PROMPT


logger = logging.getLogger(__name__)


@dataclass
class ResponseMetadata:
    review_points_count: int
    quality_score: float
    processing_time_ms: int
    used_peer_review: bool
    warnings: List[str] = field(default_factory=list)


@dataclass
class APIResponse:
    answer: str
    meta: ResponseMetadata
    debug: Optional[dict] = None  # not returned to user; can be used internally


class CentralOrchestrator:
    """
    Hybrid Orchestrator:
    - Decision #1: Use peer review (phase A) or baseline
    - If peer review: always run validate_tool -> answer_tool
    - Decision #2 (future): whether to run phase B (polish) - hook only for now
    """

    def __init__(self):
        self.baseline_tool = BaselineAnswerTool()
        self.decision_llm = GeminiClient()

    async def process(self, *, question: str, debug: bool = False) -> dict:
        import time
        t0 = time.time()
        decision_log: list[str] = []

        use_peer_review, reason = self._should_run_phase_a(question=question)
        decision_log.append(f"phase_a_decision: {use_peer_review} ({reason})")

        if not use_peer_review:
            answer = self.baseline_tool.answer(question=question)
            ms = int((time.time() - t0) * 1000)

            meta = ResponseMetadata(
                review_points_count=0,
                quality_score=0.0,
                processing_time_ms=ms,
                used_peer_review=False,
                warnings=[],
            )

            # debug not returned to user; log only
            logger.info("CentralOrchestrator decision_log=%s", decision_log)

            return {"answer": answer}

        # Phase A: validate then answer (always both)
        validation = validate_tool(question)
        review_points = validation.get("items", [])
        decision_log.append(f"review_points_count: {len(review_points)}")

        answer_result = answer_tool(question=question, review_points=review_points)
        answer = answer_result["answer"]

        # Quality score hook (simple for now; later we’ll replace with assessor)
        quality_score = self._heuristic_quality_score(review_points_count=len(review_points))
        decision_log.append(f"quality_score_heuristic: {quality_score}")

        # Phase B hook (not implemented yet)
        # should_polish = self._should_run_phase_b(...)
        # if should_polish: answer = polish_tool(...)

        ms = int((time.time() - t0) * 1000)
        meta = ResponseMetadata(
            review_points_count=len(review_points),
            quality_score=quality_score,
            processing_time_ms=ms,
            used_peer_review=True,
            warnings=[],
        )

        logger.info("CentralOrchestrator decision_log=%s", decision_log)

        # External response (clean): only answer
        return {"answer": answer}

    def _should_run_phase_a(self, *, question: str) -> tuple[bool, str]:
        # 1) rules fast-pass
        rule_use, rule_reason = self._rule_based_phase_a(question)
        if rule_use is not None:
            return rule_use, f"rules:{rule_reason}"

        # 2) LLM decision for borderline cases
        prompt = PHASE_A_DECISION_PROMPT.format(question=question)
        raw = self.decision_llm.generate(prompt)

        try:
            data = json.loads(raw.strip())
            use_peer_review = bool(data.get("use_peer_review", False))
            reason = str(data.get("reason", "")).strip() or "llm decision"
            return use_peer_review, f"llm:{reason}"
        except Exception:
            # Fail-safe: if LLM output is malformed, default to peer review for safety
            return True, "llm_output_parse_failed_default_peer_review"

    def _rule_based_phase_a(self, question: str) -> tuple[Optional[bool], str]:
        q = question.lower().strip()

        # Very short/simple questions -> baseline
        if len(q) < 40:
            return False, "very_short_question"

        # High-risk keywords -> peer review
        high_risk = [
            "architecture", "scal", "security", "protocol", "websocket",
            "distributed", "consistency", "load balancer", "reverse proxy",
            "race condition", "concurrency", "performance", "tls", "wss", "ws",
        ]
        if any(k in q for k in high_risk):
            return True, "high_risk_keywords"

        # If question has multiple requirements markers -> borderline (use LLM)
        multi_markers = [" and ", " vs ", " compare", " tradeoff", " pros", " cons", " edge case", " pitfalls"]
        if sum(1 for m in multi_markers if m in q) >= 2:
            return None, "borderline_multi_requirement"

        # Default borderline -> LLM decides
        return None, "borderline_default"

    def _heuristic_quality_score(self, *, review_points_count: int) -> float:
        # Simple heuristic placeholder:
        # more review points => likely lower initial quality
        if review_points_count <= 2:
            return 0.95
        if review_points_count <= 5:
            return 0.88
        if review_points_count <= 8:
            return 0.80
        return 0.72
