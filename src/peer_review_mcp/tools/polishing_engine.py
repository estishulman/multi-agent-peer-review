import logging
from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.models.polish_comment import PolishComment
from peer_review_mcp.reviewers.RiskReviewer import RiskReviewer
from peer_review_mcp.reviewers.base import BaseReviewer

logger = logging.getLogger(__name__)


class PolishingEngine:
    """
    Phase B - Polishing reviewers runner.
    Runs one or more reviewers in 'polish' mode and aggregates suggestions.
    Can be extended with additional reviewers (Claude, OpenAI, etc).
    """

    def __init__(self):
        client = GeminiClient()
        self.reviewers: list[BaseReviewer] = [
            RiskReviewer(client),
        ]
        logger.info("PolishingEngine initialized with %d reviewers", len(self.reviewers))

    def review_for_polish(self, *, question: str, answer: str, context_summary: str = None) -> list[PolishComment]:
        """
        Review answer for polish suggestions using configured reviewers.

        Args:
            question: Original user question
            answer: Generated answer to polish
            context_summary: Optional summary of relevant context

        Returns:
            List of PolishComment objects with improvement suggestions
        """
        comments: list[PolishComment] = []
        logger.debug("Starting polish review for question: %s", question[:100])

        for reviewer in self.reviewers:
            try:
                result = reviewer.review(
                    question=question,
                    answer=answer,
                    mode="polish",
                )
                for item in result.items:
                    text = item.strip() if isinstance(item, str) else str(item)
                    if text:
                        comments.append(PolishComment(text=text))
                logger.debug("Reviewer %s returned %d polish comments",
                           type(reviewer).__name__, len([c for c in result.items if c.strip()]))
            except Exception as e:
                logger.exception("Reviewer %s failed during polish review: %s",
                               type(reviewer).__name__, e)
                continue

        logger.info("Polish review complete: %d total comments", len(comments))
        return comments
