from peer_review_mcp.orchestrator.central_orchestrator import CentralOrchestrator
from peer_review_mcp.tools import validate_tool as validate_module
from peer_review_mcp.tools import answer_tool as answer_module


def test_run_phase_a_validate_tool_exception(monkeypatch):
    co = CentralOrchestrator()

    # Make validate_tool raise
    monkeypatch.setattr(
        "peer_review_mcp.orchestrator.central_orchestrator.validate_tool",
        lambda q, context_summary=None: (_ for _ in ()).throw(Exception("validate failed")),
    )

    # Stub answer_tool to return a known answer
    monkeypatch.setattr(
        "peer_review_mcp.orchestrator.central_orchestrator.answer_tool",
        lambda question, context_summary, review_points: {"answer": "synth"},
    )

    decision_log = []
    # When validate_tool fails, review_points should be empty
    review_points, synthesis = co._run_phase_a("some question", None, decision_log)
    assert review_points == []
    assert synthesis["answer"] == "synth"
    assert any("review_points_count: 0" in s for s in decision_log)

