import logging
from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer
from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.models.review_result import ReviewMode
from peer_review_mcp.reviewers.gemini_clarity_reviewer import GeminiClarityReviewer
from peer_review_mcp.models.review_point import ReviewPoint

logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Central validation engine.
    Aggregates multiple reviewers to identify potential issues with the question.
    Returns structured ReviewPoint objects with risk classification.
    """

    def __init__(self):
        client = GeminiClient()

        self.reviewers = [
            GeminiReviewer(client),
            GeminiClarityReviewer(client),
        ]
        logger.info("ValidationEngine initialized with %d reviewers", len(self.reviewers))

    def validate(self, question: str, context_summary: str = None) -> dict:
        """
        Validate a question by running multiple reviewers.
        Returns structured review points with risk classification.

        Args:
            question: The question to validate
            context_summary: Optional context about previous discussion
        """
        review_points: list[ReviewPoint] = []

        for reviewer in self.reviewers:
            try:
                result = reviewer.review(
                    question=question,
                    answer=context_summary,  # Pass context as "answer" to reviewers
                    mode="validate",
                )
                for item in result.items:
                    # Handle both dict (with classification) and string items
                    if isinstance(item, dict):
                        review_point = ReviewPoint(
                            text=item.get("text", str(item)),
                            risk_type=item.get("risk_type"),
                            severity=item.get("severity"),
                            confidence=item.get("confidence", 0.8),
                        )
                    else:
                        review_point = ReviewPoint(
                            text=item.strip() if isinstance(item, str) else str(item),
                            risk_type=None,
                            severity=None,
                            confidence=0.8,
                        )
                    review_points.append(review_point)
            except Exception as e:
                logger.exception("Reviewer %s failed during validation: %s",
                                type(reviewer).__name__, e)
                continue

        logger.info("Validation complete: %d review points found", len(review_points))
        return {
            "items": review_points,
            "count": len(review_points),
        }
