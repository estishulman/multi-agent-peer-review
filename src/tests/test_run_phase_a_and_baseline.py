from peer_review_mcp.orchestrator.central_orchestrator import CentralOrchestrator
from peer_review_mcp.tools import validate_tool as validate_module
from peer_review_mcp.tools import answer_tool as answer_module
from peer_review_mcp.tools.baseline_answer_tool import BaselineAnswerTool


def test_run_phase_a_validate_tool_exception(monkeypatch):
    co = CentralOrchestrator()

    # Make validate_tool raise
    monkeypatch.setattr(
        "peer_review_mcp.orchestrator.central_orchestrator.validate_tool",
        lambda q: (_ for _ in ()).throw(Exception("validate failed")),
    )

    # Stub answer_tool to return a known answer
    monkeypatch.setattr(
        "peer_review_mcp.orchestrator.central_orchestrator.answer_tool",
        lambda question, review_points: {"answer": "synth"},
    )

    decision_log = []
    review_points, answer = co._run_phase_a("some question", decision_log)
    assert review_points == []
    assert answer == "synth"
    assert any("review_points_count: 0" in s for s in decision_log)


def test_baseline_answer_tool_empty_llm_fallback(monkeypatch):
    # Stub GeminiClient.generate to return empty
    monkeypatch.setattr(
        "peer_review_mcp.LLM.gemini_client.GeminiClient.generate",
        lambda self, prompt: "",
    )

    tool = BaselineAnswerTool()
    out = tool.answer(question="Tell me about Python")
    assert out != ""  # fallback returns non-empty summary

    # Now ensure process returns baseline when rule-based decides so
    co = CentralOrchestrator()
    # Force rule-based to pick baseline
    monkeypatch.setattr(
        "peer_review_mcp.orchestrator.central_orchestrator.CentralOrchestrator._rule_based_phase_a",
        lambda self, q: (False, "very_short_question"),
    )

    res = __import__("asyncio").run(co.process(question="short"))
    assert res["meta"]["used_peer_review"] is False

