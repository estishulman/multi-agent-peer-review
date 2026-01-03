import os
import pytest
from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.LLM.synthesis_client import AnswerSynthesisClient
from peer_review_mcp.orchestrator.central_orchestrator import CentralOrchestrator
from peer_review_mcp.tools.polishing_engine import PolishingEngine
from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer


def test_gemini_client_disabled(monkeypatch):
    # Ensure no real network call: stub generate
    monkeypatch.setattr("peer_review_mcp.LLM.gemini_client.GeminiClient.generate", lambda self, prompt: '{"use_peer_review": true}')
    monkeypatch.setenv("DISABLE_LLM", "1")
    gc = GeminiClient()
    # calling generate should not raise and should return a string
    out = gc.generate("any")
    assert isinstance(out, str)


def test_synthesis_client_format_and_call(monkeypatch):
    # stub client.generate
    class StubClient:
        def generate(self, prompt):
            assert "Review points" in prompt
            return "synth answer"

    sc = AnswerSynthesisClient(StubClient())
    out = sc.synthesize(question="q", review_points=["a", "b"])
    assert "synth answer" == out




def test_polishing_engine_parses(monkeypatch):
    # stub reviewer to return a ReviewResult-like object
    class FakeReviewer:
        def review(self, question, answer, mode):
            class R:
                items = ["- fix this", "• another"]
            return R()

    pe = PolishingEngine()
    # replace reviewers
    pe.reviewers = [FakeReviewer()]
    comments = pe.review_for_polish(question="q", answer="a")
    assert len(comments) == 2
    assert all(hasattr(c, 'text') for c in comments)


def test_gemini_reviewer_parsing(monkeypatch):
    # pass a stub client with generate
    class StubClient:
        def generate(self, prompt):
            return "- one\n- two"

    gr = GeminiReviewer(StubClient())
    res = gr.review(question="q", mode="validate")
    assert hasattr(res, 'items')
    # In validate mode, items should now be dicts with classification
    assert len(res.items) == 2
    assert all(isinstance(item, dict) and 'text' in item for item in res.items)
    assert res.items[0]['text'] == "one"
    assert res.items[1]['text'] == "two"


def test_central_orchestrator_phase_b_decision():
    co = CentralOrchestrator()
    # many review points -> should polish
    should, reason = co._decide_phase_b(review_points_count=6, quality_score=0.95)
    assert should is True
    # low quality score -> should polish
    should, reason = co._decide_phase_b(review_points_count=1, quality_score=0.5)
    assert should is True
    # good enough
    should, reason = co._decide_phase_b(review_points_count=1, quality_score=0.95)
    assert should is False
