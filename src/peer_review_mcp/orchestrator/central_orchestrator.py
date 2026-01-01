import json
import time
from dataclasses import dataclass, field
from typing import Optional, List

from peer_review_mcp.tools.validate_tool import validate_tool
from peer_review_mcp.tools.answer_tool import answer_tool
from peer_review_mcp.tools.baseline_answer_tool import BaselineAnswerTool
from peer_review_mcp.tools.polishing_engine import PolishingEngine

from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.prompts.phase_a_decision import PHASE_A_DECISION_PROMPT
from peer_review_mcp.prompts.polish_synthesis import POLISH_SYNTHESIS_PROMPT



# =========================
# Public response models
# =========================

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
    debug: Optional[dict] = None


# =========================
# Central Orchestrator
# =========================

class CentralOrchestrator:
    """
    Hybrid Orchestrator

    Phase 0: Decide baseline vs peer review
    Phase A: validate -> answer (always together)
    Phase B: optional polishing
    """

    def __init__(self):
        self.baseline_tool = BaselineAnswerTool()
        self.decision_llm = GeminiClient()

        self.polishing_engine = PolishingEngine()
        self.polish_llm = GeminiClient()

    # ---------------------
    # Public entrypoint
    # ---------------------

    async def process(self, *, question: str, debug: bool = False) -> dict:
        t0 = time.time()
        decision_log: list[str] = []

        # Phase 0 – baseline vs peer review
        use_peer_review, reason = self._decide_phase_a(question)
        decision_log.append(f"phase_a_decision: {use_peer_review} ({reason})")

        if not use_peer_review:
            answer = self.baseline_tool.answer(question=question)
            self._log(decision_log)
            return {"answer": answer}

        # Phase A – validation + synthesis
        review_points, answer = self._run_phase_a(question, decision_log)

        # Quality assessment (heuristic for now)
        quality_score = self._heuristic_quality_score(len(review_points))
        decision_log.append(f"quality_score_heuristic: {quality_score}")

        # Phase B – optional polishing
        should_polish, polish_reason = self._decide_phase_b(
            review_points_count=len(review_points),
            quality_score=quality_score,
        )
        decision_log.append(f"phase_b_decision: {should_polish} ({polish_reason})")

        if should_polish:
            answer = self._run_phase_b(question, answer, decision_log)

        self._log(decision_log)

        return {"answer": answer}

    # =====================
    # Phase A
    # =====================

    def _run_phase_a(self, question: str, decision_log: list[str]):
        validation = validate_tool(question)
        review_points = validation.get("items", [])
        decision_log.append(f"review_points_count: {len(review_points)}")

        result = answer_tool(
            question=question,
            review_points=review_points,
        )

        return review_points, result["answer"]

    def _decide_phase_a(self, question: str) -> tuple[bool, str]:
        rule_decision, reason = self._rule_based_phase_a(question)
        if rule_decision is not None:
            return rule_decision, f"rules:{reason}"

        prompt = PHASE_A_DECISION_PROMPT.format(question=question)
        raw = self.decision_llm.generate(prompt)

        try:
            data = json.loads(raw.strip())
            return bool(data.get("use_peer_review")), "llm_decision"
        except Exception:
            return True, "llm_parse_failed_default_peer_review"

    def _rule_based_phase_a(self, question: str) -> tuple[Optional[bool], str]:
        q = question.lower().strip()

        if len(q) < 40:
            return False, "very_short_question"

        high_risk = [
            "architecture", "scal", "security", "protocol", "websocket",
            "distributed", "load balancer", "reverse proxy",
            "race condition", "concurrency", "performance", "tls", "wss",
        ]
        if any(k in q for k in high_risk):
            return True, "high_risk_keywords"

        return None, "borderline"

    # =====================
    # Phase B
    # =====================

    def _decide_phase_b(self, *, review_points_count: int, quality_score: float):
        if review_points_count >= 6:
            return True, "many_review_points"
        if quality_score < 0.9:
            return True, "low_quality_score"
        return False, "good_enough"

    def _run_phase_b(self, question: str, answer: str, decision_log: list[str]) -> str:
        logger.info(">>> ENTERED PHASE B <<<")
        comments = self.polishing_engine.review_for_polish(
            question=question,
            answer=answer,
        )
        decision_log.append(f"polish_comments_count: {len(comments)}")

        if not comments:
            return answer

        formatted = "\n".join(f"- {c.text}" for c in comments)

        prompt = POLISH_SYNTHESIS_PROMPT.format(
            question=question,
            answer=answer,
            comments=formatted,
        )

        polished = self.polish_llm.generate(prompt).strip()
        return polished or answer

    # =====================
    # Utilities
    # =====================

    def _heuristic_quality_score(self, review_points_count: int) -> float:
        if review_points_count <= 2:
            return 0.95
        if review_points_count <= 5:
            return 0.88
        if review_points_count <= 8:
            return 0.80
        return 0.72

    def _log(self, decision_log: list[str]):
        logger.info("CentralOrchestrator decision_log=%s", decision_log)
