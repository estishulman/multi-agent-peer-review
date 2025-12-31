from ..LLM.gemini_client import GeminiClient
from ..prompts.answer_synthesis import ANSWER_SYNTHESIS_PROMPT


class AnswerSynthesisClient:
    def __init__(self, client: GeminiClient):
        self.client = client

    def synthesize(
        self,
        *,
        question: str,
        review_points: list[str],
    ) -> str:
        formatted_points = "\n".join(
            f"- {p}" for p in review_points
        )

        prompt = f"""
{ANSWER_SYNTHESIS_PROMPT}

Question:
{question}

Review points:
{formatted_points}
"""

        return self.client.generate(prompt)
