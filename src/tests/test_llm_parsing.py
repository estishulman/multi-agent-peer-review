from peer_review_mcp.orchestrator.central_orchestrator import CentralOrchestrator


def test_decide_phase_a_parses_json(monkeypatch, stub_llm):
    co = CentralOrchestrator()
    # ensure env gates do not interfere
    monkeypatch.delenv("SKIP_PEER_REVIEW", raising=False)
    monkeypatch.delenv("FORCE_PEER_REVIEW", raising=False)

    stub_llm('{"use_peer_review": false}')

    val, reason = co._decide_phase_a("some question that is not short and not high risk")
    assert val is False
    assert reason == "llm_decision"


def test_decide_phase_a_parses_regex(monkeypatch, stub_llm):
    co = CentralOrchestrator()
    monkeypatch.delenv("SKIP_PEER_REVIEW", raising=False)
    monkeypatch.delenv("FORCE_PEER_REVIEW", raising=False)

    stub_llm('Here is the decision: use_peer_review: true')

    val, reason = co._decide_phase_a("some question that is not short and not high risk")
    assert val is True
    assert reason == "llm_regex_decision"


def test_decide_phase_a_unparseable_defaults_to_peer_review(monkeypatch, stub_llm):
    co = CentralOrchestrator()
    monkeypatch.delenv("SKIP_PEER_REVIEW", raising=False)
    monkeypatch.delenv("FORCE_PEER_REVIEW", raising=False)

    stub_llm('nonsense output that is not JSON and has no keyword')

    val, reason = co._decide_phase_a("some question that is not short and not high risk")
    assert val is True
    assert reason.startswith("llm_parse_failed")
