from typing import Optional
from ..prompts.answer_synthesis import ANSWER_SYNTHESIS_PROMPT
from peer_review_mcp.LLM.chatgpt_client import ChatGPTClient
import json
import logging

logger = logging.getLogger(__name__)


class AnswerSynthesisClient:
    def __init__(self, client: ChatGPTClient):
        self.client = client

    def synthesize(
        self,
        *,
        question: str,
        context_summary: Optional[str] = None,
        review_points: list[str] = None,
    ) -> dict:
        if review_points is None:
            review_points = []

        formatted_points = "\n".join(f"- {p}" for p in review_points)
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

        raw = self.client.generate(prompt)

        try:
            data = json.loads(raw)
            return {
                "answer": data["answer"],
                "confidence": float(data.get("confidence", 0.8)),
                "needs_polish": bool(data.get("needs_polish", False)),
            }
        except Exception:
            logger.exception("Failed to parse synthesis JSON, falling back to raw answer")
            return {
                "answer": raw.strip(),
                "confidence": 0.5,
                "needs_polish": True,
            }
