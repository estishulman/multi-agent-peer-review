import json
import time
from dataclasses import dataclass, field
from typing import Optional, List
import logging
import re
import os

from peer_review_mcp.tools.validate_tool import validate_tool
from peer_review_mcp.tools.answer_tool import answer_tool
from peer_review_mcp.tools.baseline_answer_tool import BaselineAnswerTool
from peer_review_mcp.tools.polishing_engine import PolishingEngine

from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.prompts.phase_a_decision import PHASE_A_DECISION_PROMPT
from peer_review_mcp.prompts.polish_synthesis import POLISH_SYNTHESIS_PROMPT



# add a module logger
logger = logging.getLogger(__name__)

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

    async def process(self, *, question: str) -> dict:
        t0 = time.time()
        decision_log: list[str] = []

        # Phase 0 – baseline vs peer review
        use_peer_review, reason = self._decide_phase_a(question)
        decision_log.append(f"phase_a_decision: {use_peer_review} ({reason})")

        if not use_peer_review:
            answer = self.baseline_tool.answer(question=question)
            # pass start time so _log can compute processing time
            self._log(decision_log, t0)
            #processing_time_ms = int((time.time() - t0) * 1000)

            return {
                "answer": answer,
                "meta": {
                    "used_peer_review": False,
                    #"processing_time_ms": processing_time_ms,
                },
            }
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

        # pass start time so _log can compute processing time
        self._log(decision_log, t0)
        processing_time_ms = int((time.time() - t0) * 1000)
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

    # =====================
    # Phase A
    # =====================

    def _run_phase_a(self, question: str, decision_log: list[str]):
        try:
            validation = validate_tool(question)
            review_points = validation.get("items", [])
        except Exception as e:
            logger.exception("validate_tool failed in _run_phase_a: %s", e)
            # Fallback: treat as no review points (safe) and continue
            validation = {"items": []}
            review_points = []
        decision_log.append(f"review_points_count: {len(review_points)}")

        result = answer_tool(
            question=question,
            review_points=review_points,
        )

        return review_points, result["answer"]

    def _decide_phase_a(self, question: str) -> tuple[bool, str]:
        # Check environment variables first
        skip_peer_review = os.getenv("SKIP_PEER_REVIEW", "0") == "1"
        force_peer_review = os.getenv("FORCE_PEER_REVIEW", "0") == "1"

        if skip_peer_review:
            logger.info("Skipping peer review due to SKIP_PEER_REVIEW=1")
            return False, "skipped_by_env"
        if force_peer_review:
            logger.info("Forcing peer review due to FORCE_PEER_REVIEW=1")
            return True, "forced_by_env"

        rule_decision, reason = self._rule_based_phase_a(question)
        if rule_decision is not None:
            return rule_decision, f"rules:{reason}"

        prompt = PHASE_A_DECISION_PROMPT.format(question=question)
        try:
            raw = self.decision_llm.generate(prompt)
        except Exception as e:
            logger.exception("LLM call failed in _decide_phase_a: %s", e)
            return True, f"llm_call_failed:{e}"

        logger.debug("phase_a raw LLM output: %s", raw)
        txt = (raw or "").strip()

        # 1) Try direct JSON parse
        data = None
        try:
            data = json.loads(txt)
        except Exception:
            # 2) Try to extract the first JSON object from the output
            m = re.search(r"{.*?}", txt, re.S)
            if m:
                try:
                    data = json.loads(m.group(0))
                except Exception:
                    data = None

        # If we have a parsed dict and the key exists, return it
        if isinstance(data, dict) and "use_peer_review" in data:
            return bool(data.get("use_peer_review")), "llm_decision"

        # 3) Fallback to regex search for `use_peer_review: true/false`
        m2 = re.search(r'"?use_peer_review"?\s*[:=]\s*(true|false)', txt, re.I)
        if m2:
            val = m2.group(1).lower() == "true"
            return val, "llm_regex_decision"

        # 4) Another fallback: look for yes/no near the key
        m3 = re.search(r'use_peer_review.*?(true|false|yes|no)', txt, re.I)
        if m3:
            v = m3.group(1).lower()
            if v in ("true", "yes"):
                return True, "llm_regex_decision"
            if v in ("false", "no"):
                return False, "llm_regex_decision"

        # 5) Give up, default to peer review (conservative) but log raw output for debugging
        logger.warning("phase_a decision parse failed; defaulting to peer_review. raw=%s", txt)
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

    # implement logging helper
    def _log(self, decision_log: list[str], start_time: Optional[float] = None):
        """Log the orchestrator decision trace with an optional processing time."""
        processing_time_ms = None
        if start_time is not None:
            try:
                processing_time_ms = int((time.time() - start_time) * 1000)
            except Exception:
                processing_time_ms = None

        logger.info(
            "CentralOrchestrator decision_log=%s processing_time_ms=%s",
            decision_log,
            processing_time_ms,
        )
