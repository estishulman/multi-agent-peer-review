import logging
from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.models.polish_comment import PolishComment
from peer_review_mcp.reviewers.RiskReviewer import RiskReviewer
from peer_review_mcp.reviewers.base import BaseReviewer
from ..models.review_result import ReviewResult

logger = logging.getLogger(__name__)


class PolishingEngine:  # Runs polishing reviewers and aggregates polish suggestions
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

    async def review_for_polish(self, *, question: str, answer: str, context_summary: str = None) -> list[PolishComment]:
        """
        Review answer for polish suggestions using configured reviewers.

        Args:
            question: Original user question
            answer: Generated answer to polish
            context_summary: Optional summary of relevant context

        Returns:
            List of PolishComment objects with improvement suggestions

        Note:
            Reviewers in `polish` mode are expected to return a list of textual
            suggestions (strings). These are converted to `PolishComment` objects.
        """
        comments: list[PolishComment] = []  # Ensure type consistency
        logger.debug("Starting polish review for question: %s", question[:100])

        for reviewer in self.reviewers:
            try:
                # Each reviewer processes the question and answer to generate comments
                result = await reviewer.review(
                    question=question,
                    answer=answer,
                    context_summary=context_summary,
                    mode="polish"  # Explicitly specify mode
                )
                if isinstance(result, ReviewResult):
                    for item in result.items:
                        if isinstance(item, str):
                            comments.append(PolishComment(text=item))
                        else:
                            logger.warning("Unexpected item type in ReviewResult: %s", type(item))
                else:
                    logger.warning("Reviewer %s returned unexpected result type", reviewer.__class__.__name__)
            except Exception as e:
                logger.error("Reviewer %s failed: %s", reviewer.__class__.__name__, str(e))

        return comments
