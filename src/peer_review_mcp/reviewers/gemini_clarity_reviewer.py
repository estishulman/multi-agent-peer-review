from ..reviewers.base import BaseReviewer
from ..models.review_result import ReviewResult, ReviewMode
from ..LLM.gemini_client import GeminiClient
from ..prompts.clarity_validation import CLARITY_VALIDATION_PROMPT


class GeminiClarityReviewer(BaseReviewer):

    def __init__(self, client: GeminiClient):
        self.client = client

    def review(
        self,
        *,
        question: str,
        answer: str | None = None,
        mode: ReviewMode
    ) -> ReviewResult:

        if mode != "validate":
            raise ValueError("Clarity reviewer supports validate mode only")

        prompt = CLARITY_VALIDATION_PROMPT.format(question=question)

        raw_text = self.client.generate(prompt)

        items = self._parse_items(raw_text)

        return ReviewResult(mode=mode, items=items)

    def _parse_items(self, text: str) -> list[str]:
        return [
            line.strip("-• ").strip()
            for line in text.splitlines()
            if line.strip()
        ]
