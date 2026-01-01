import os
from peer_review_mcp.orchestrator.central_orchestrator import CentralOrchestrator


def test_decide_phase_a_env_skip_and_force(monkeypatch):
    co = CentralOrchestrator()

    monkeypatch.setenv("SKIP_PEER_REVIEW", "1")
    val, reason = co._decide_phase_a("anything")
    assert val is False
    assert reason == "skipped_by_env"
    monkeypatch.delenv("SKIP_PEER_REVIEW", raising=False)

    monkeypatch.setenv("FORCE_PEER_REVIEW", "1")
    val, reason = co._decide_phase_a("anything")
    assert val is True
    assert reason == "forced_by_env"
    monkeypatch.delenv("FORCE_PEER_REVIEW", raising=False)

