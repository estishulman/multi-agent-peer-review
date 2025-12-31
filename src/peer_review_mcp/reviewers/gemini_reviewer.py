from ..reviewers.base import BaseReviewer
from ..models.review_result import ReviewResult, ReviewMode
from ..LLM.gemini_client import GeminiClient
from ..prompts.validation import VALIDATION_PROMPT
from ..prompts.polishing import POLISHING_PROMPT


class GeminiReviewer(BaseReviewer):

    def __init__(self, client: GeminiClient):
        self.client = client

    def review(
        self,
        *,
        question: str,
        answer: str | None = None,
        mode: ReviewMode
    ) -> ReviewResult:

        if mode == "validate":
            prompt = VALIDATION_PROMPT.format(question=question)

        elif mode == "polish":
            if answer is None:
                raise ValueError("Polish mode requires an answer")
            prompt = POLISHING_PROMPT.format(
                question=question,
                answer=answer
            )

        else:
            raise ValueError(f"Unknown mode: {mode}")

        raw_text = self.client.generate(prompt)

        items = self._parse_items(raw_text)

        return ReviewResult(mode=mode, items=items)

    def _parse_items(self, text: str) -> list[str]:
        return [
            line.strip("-• ").strip()
            for line in text.splitlines()
            if line.strip()
        ]
