from typing import Optional
from ..LLM.gemini_client import GeminiClient
from ..prompts.answer_synthesis import ANSWER_SYNTHESIS_PROMPT


class AnswerSynthesisClient:
    def __init__(self, client: GeminiClient):
        self.client = client

    def synthesize(
        self,
        *,
        question: str,
        context_summary: Optional[str] = None,
        review_points: list[str] = None,
    ) -> str:
        if review_points is None:
            review_points = []

        formatted_points = "\n".join(
            f"- {p}" for p in review_points
        )

        # context_summary is already a formatted string
        context_str = context_summary if context_summary else "(No previous context)"

        prompt = f"""
{ANSWER_SYNTHESIS_PROMPT}

Conversation Context:
{context_str}

Question:
{question}

Review points to avoid:
{formatted_points}
"""

        return self.client.generate(prompt)
