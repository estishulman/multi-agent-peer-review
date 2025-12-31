from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer
from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.models.review_result import ReviewMode
from peer_review_mcp.reviewers.gemini_clarity_reviewer import GeminiClarityReviewer


class ValidationEngine:
    """
    Central validation engine.
    Can aggregate multiple reviewers / LLMs in the future.
    """

    def __init__(self):
        client = GeminiClient()

        self.reviewers = [
            GeminiReviewer(client),
            GeminiClarityReviewer(client),
            # Future:
            # OpenAIReviewer(OpenAIClient()),
            # ClaudeReviewer(ClaudeClient()),
        ]

    def validate(self, question: str) -> dict:
        insights: list[str] = []

        for reviewer in self.reviewers:
            result = reviewer.review(
                question=question,
                answer=None,
                mode="validate",
            )
            insights.extend(result.items)

        return {
            "items": insights,
            "count": len(insights),
        }
