from typing import Union, List, Optional
from peer_review_mcp.tools.synthesis_engine import SynthesisEngine
from peer_review_mcp.models.review_point import ReviewPoint

_engine = SynthesisEngine()


async def answer_tool(
    *,
    question: str,
    context_summary: Optional[str] = None,
    review_points: Union[List[ReviewPoint], List[str]] = None,
) -> dict:
    """
    Internal tool: takes question + context_summary + review points and returns synthesized answer.

    Args:
        question: The user's question
        context_summary: Optional short summary of relevant context (not full conversation)
        review_points: List of ReviewPoint objects or strings with issues/insights

    Returns:
        Dictionary with 'answer' key containing the synthesized response
    """
    if review_points is None:
        review_points = []

    # Convert ReviewPoint objects to strings if needed
    review_point_texts = []
    for point in review_points:
        if isinstance(point, ReviewPoint):
            review_point_texts.append(point.text)
        else:
            review_point_texts.append(str(point))

    return await _engine.answer(
        question=question,
        context_summary=context_summary,
        review_points=review_point_texts,
    )


