import os
import pytest
from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.orchestrator.central_orchestrator import CentralOrchestrator
from peer_review_mcp.tools.polishing_engine import PolishingEngine
from peer_review_mcp.reviewers.RiskReviewer import RiskReviewer
from peer_review_mcp.tools.synthesis_engine import SynthesisEngine
from peer_review_mcp.models.review_result import ReviewResult


def test_gemini_client_disabled(monkeypatch):
    # Ensure no real network call: stub generate
    monkeypatch.setattr("peer_review_mcp.LLM.gemini_client.GeminiClient.generate", lambda self, prompt: '{"use_peer_review": true}')
    monkeypatch.setenv("DISABLE_LLM", "1")
    gc = GeminiClient()
    # calling generate should not raise and should return a string
    out = gc.generate("any")
    assert isinstance(out, str)


@pytest.mark.anyio
async def test_synthesis_engine_format_and_call(monkeypatch):
    # stub client.generate_async
    class StubClient:
        async def generate_async(self, prompt):
            assert "Review points" in prompt
            return '{"answer": "synth answer", "confidence": 0.9, "needs_polish": false}'

    engine = SynthesisEngine()
    engine.client = StubClient()
    out = await engine.answer(question="q", review_points=["a", "b"])
    assert out["answer"] == "synth answer"
    assert out["confidence"] == 0.9
    assert out["needs_polish"] is False




@pytest.mark.anyio
async def test_polishing_engine_parses(monkeypatch):
    # stub reviewer to return a ReviewResult-like object
    class FakeReviewer:
        async def review(self, question, answer, context_summary, mode):
            return ReviewResult(mode="polish", items=["- fix this", "• another"])

    pe = PolishingEngine()
    # replace reviewers
    pe.reviewers = [FakeReviewer()]
    comments = await pe.review_for_polish(question="q", answer="a")
    assert len(comments) == 2
    assert all(hasattr(c, 'text') for c in comments)


@pytest.mark.anyio
async def test_gemini_reviewer_parsing(monkeypatch):
    # pass a stub client with generate
    class StubClient:
        async def generate_async(self, prompt):
            return "- one\n- two"

    gr = RiskReviewer(StubClient())
    res = await gr.review(question="q", mode="validate", context_summary=None)
    assert hasattr(res, 'items')
    # In validate mode, items should now be dicts with classification
    assert len(res.items) == 2
    assert all(isinstance(item, dict) and 'text' in item for item in res.items)
    assert res.items[0]['text'] == "one"
    assert res.items[1]['text'] == "two"


def test_central_orchestrator_phase_b_decision():
    co = CentralOrchestrator()
    # many review points -> should polish
    should, reason = co._decide_phase_b(
        review_points_count=8,
        quality_score=0.95,
        model_confidence=0.95,
        model_requested_polish=False,
    )
    assert should is True
    # low model confidence -> should polish
    should, reason = co._decide_phase_b(
        review_points_count=1,
        quality_score=0.95,
        model_confidence=0.7,
        model_requested_polish=False,
    )
    assert should is True
    # good enough
    should, reason = co._decide_phase_b(
        review_points_count=1,
        quality_score=0.95,
        model_confidence=0.95,
        model_requested_polish=False,
    )
    assert should is False
