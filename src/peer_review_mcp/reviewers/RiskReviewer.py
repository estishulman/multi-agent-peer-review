from .base import BaseReviewer
from ..models.review_result import ReviewResult, ReviewMode
from ..LLM.gemini_client import GeminiClient
from ..prompts.validation import VALIDATION_PROMPT
from ..prompts.polishing import POLISHING_PROMPT
from ..llm_parsing import try_parse_json
import logging

logger = logging.getLogger(__name__)


class RiskReviewer(BaseReviewer):  # Reviewer that identifies risk/validation items and polish suggestions

    def __init__(self, client: GeminiClient):
        self.client = client

    async def review(
        self,
        *,
        question: str,
        answer: str | None = None,
        context_summary: str | None = None,
        mode: ReviewMode
    ) -> ReviewResult:

        if mode == "validate":
            context_text = context_summary if context_summary else "(No context)"
            prompt = VALIDATION_PROMPT.format(question=question, answer=context_text)

        elif mode == "polish":
            # In polish mode, an answer must be provided
            if answer is None:
                raise ValueError("Polish mode requires an answer")
            context_text = context_summary if context_summary else "(No context)"
            prompt = POLISHING_PROMPT.format(
                question=question,
                answer=answer,
                context=context_text,
            )

        else:
            # Raise an error for unsupported modes
            raise ValueError(f"Unknown mode: {mode}")

        # Generate raw text using the client based on the constructed prompt
        raw_text = await self.client.generate_async(prompt)
        return self._parse_result(raw_text, mode)  # Pass mode explicitly

    def _parse_result(self, raw_text: str, mode: ReviewMode) -> ReviewResult:
        """Parse the raw text result into structured review items."""
        items = self._parse_items(raw_text, mode)
        return ReviewResult(mode=mode, items=items)

    def _parse_items(self, text: str, mode: ReviewMode) -> list[dict | str]:
        """Parse items based on mode. Validate returns dicts, polish returns strings."""
        if mode == "validate":
            return self._parse_json_items(text)
        else:
            # Polish mode still uses bullet list format
            return [
                line.strip("-• ").strip()
                for line in text.splitlines()
                if line.strip()
            ]

    def _parse_json_items(self, text: str) -> list[dict]:
        """Parse JSON array of review points with classification."""
        data = try_parse_json(text)
        if not isinstance(data, list):
            if data is not None:
                logger.warning("Expected JSON array, got: %s", type(data))
            else:
                logger.warning("Failed to parse JSON from reviewer")
            return self._fallback_parse(text)

        return data

    def _fallback_parse(self, text: str) -> list[dict]:
        """Fallback: parse bullet list and create dict structure."""
        # Conservative defaults preserve a structured shape when JSON parsing fails.
        return [
            {
                "text": line.strip("-• ").strip(),
                "risk_type": "other",
                "severity": "medium",
                "confidence": 0.7,
            }
            for line in text.splitlines()
            if line.strip()
        ]
