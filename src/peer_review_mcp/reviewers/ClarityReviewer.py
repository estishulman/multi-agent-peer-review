from .base import BaseReviewer
from ..models.review_result import ReviewResult, ReviewMode
from ..LLM.gemini_client import GeminiClient
from ..prompts.clarity_validation import CLARITY_VALIDATION_PROMPT
import json
import logging

logger = logging.getLogger(__name__)


class ClarityReviewer(BaseReviewer):

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

    def _parse_items(self, text: str) -> list[dict | str]:
        """Try to parse as JSON first, fallback to bullet list."""
        try:
            return self._parse_json_items(text)
        except Exception:
            return self._parse_bullet_list(text)

    def _parse_json_items(self, text: str) -> list[dict]:
        """Parse JSON array of review points with classification."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        data = json.loads(text.strip())
        if not isinstance(data, list):
            raise ValueError(f"Expected list, got {type(data)}")
        return data

    def _parse_bullet_list(self, text: str) -> list[dict]:
        """Fallback: parse bullet list and create dict structure."""
        return [
            {
                "text": line.strip("-• ").strip(),
                "risk_type": "edge_cases",
                "severity": "medium",
                "confidence": 0.75,
            }
            for line in text.splitlines()
            if line.strip()
        ]
