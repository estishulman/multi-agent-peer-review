from peer_review_mcp.tools.synthesis_engine import SynthesisEngine

_engine = SynthesisEngine()


def answer_tool(*, question: str, review_points: list[str]) -> dict:
    """
    Internal tool: takes question + review points and returns synthesized answer.
    """
    return _engine.answer(
        question=question,
        review_points=review_points,
    )
