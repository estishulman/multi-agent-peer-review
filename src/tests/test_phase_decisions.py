from peer_review_mcp.orchestrator.central_orchestrator import CentralOrchestrator


def test_rule_based_phase_a_short_and_high_risk():
    co = CentralOrchestrator()

    # Short question -> no peer review
    decision, reason = co._rule_based_phase_a("short")
    assert decision is False
    assert reason == "very_short_question"

    # High risk keyword -> peer review
    decision, reason = co._rule_based_phase_a("This involves security and encryption architecture")
    assert decision is True
    assert reason == "high_risk_keywords"

    # Borderline -> None
    long_q = "This is a somewhat long question but not about high risk topics and should be borderline." * 2
    decision, reason = co._rule_based_phase_a(long_q)
    assert decision is None
    assert reason == "borderline"

