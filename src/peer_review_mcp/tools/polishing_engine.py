from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.models.polish_comment import PolishComment
from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer
from peer_review_mcp.reviewers.base import BaseReviewer


class PolishingEngine:
    """
    Phase B - Polishing reviewers runner.
    Runs one or more reviewers in 'polish' mode and aggregates suggestions.
    Future-proof: add more reviewers to self.reviewers list.
    """

    def __init__(self):
        client = GeminiClient()

        # Reuse existing reviewer infra. GeminiReviewer already supports mode="polish".
        self.reviewers: list[BaseReviewer] = [
            GeminiReviewer(client),
            # Future:
            # AnotherGeminiReviewer(client),
            # ClaudeReviewer(...),
            # OpenAIReviewer(...),
        ]

    def review_for_polish(self, *, question: str, answer: str) -> list[PolishComment]:
        comments: list[PolishComment] = []

        for reviewer in self.reviewers:
            result = reviewer.review(
                question=question,
                answer=answer,
                mode="polish",
            )
            # result.items is list[str] bullet-like suggestions
            for item in result.items:
                text = item.strip()
                if text:
                    comments.append(PolishComment(text=text))

        return comments
