from ..reviewers.base import BaseReviewer
from ..models.review_result import ReviewResult, ReviewMode
from ..LLM.gemini_client import GeminiClient
from ..prompts.validation import VALIDATION_PROMPT
from ..prompts.polishing import POLISHING_PROMPT
import json
import logging

logger = logging.getLogger(__name__)


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
            # For validate mode, answer parameter contains context_summary
            context_text = answer if answer else "(No context)"
            prompt = VALIDATION_PROMPT.format(question=question, answer=context_text)

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
        try:
            # Extract JSON from response
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            data = json.loads(text.strip())
            if not isinstance(data, list):
                logger.warning("Expected JSON array, got: %s", type(data))
                return self._fallback_parse(text)

            return data
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse JSON from reviewer: %s", e)
            return self._fallback_parse(text)

    def _fallback_parse(self, text: str) -> list[dict]:
        """Fallback: parse bullet list and create dict structure."""
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
