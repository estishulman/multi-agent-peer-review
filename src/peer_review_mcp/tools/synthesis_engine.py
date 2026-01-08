from typing import Optional
from ..prompts.answer_synthesis import ANSWER_SYNTHESIS_PROMPT
from peer_review_mcp.LLM.chatgpt_client import ChatGPTClient
import json
import logging

logger = logging.getLogger(__name__)


class SynthesisEngine:  # Builds synthesis prompts, calls LLM to generate final answers, parses result
    # This engine is responsible for synthesizing answers using the provided clients.
    def __init__(self):
        # Initialize the ChatGPT client for generating responses.
        self.client = ChatGPTClient()

    async def answer(
        self,
        question: str,
        context_summary: Optional[str] = None,
        review_points: list[str] = None,
    ) -> dict:
        """
        Generate an answer based on the provided question, context, and review points.

        Args:
            question (str): The main question to be answered.
            context_summary (Optional[str]): A summary of the conversation context, if available.
            review_points (list[str]): Specific points to avoid in the answer.

        Returns:
            dict: A dictionary containing the generated answer, confidence score, and polish status.

        Note:
            The synthesizer attempts to parse an LLM response as JSON (keys: "answer", "confidence", "needs_polish").
            If parsing fails (rare), the raw text is returned with conservative defaults to allow processing to continue.
        """
        # Ensure review_points is initialized as an empty list if not provided
        if review_points is None:
            review_points = []

        # Format the review points into a bullet list for the prompt
        formatted_points = "\n".join(f"- {p}" for p in review_points)
        # Use the provided context summary or a default placeholder
        context_str = context_summary if context_summary else "(No previous context)"

        # Construct the prompt to send to the LLM
        prompt = f"""
        {ANSWER_SYNTHESIS_PROMPT}
        Conversation Context: {context_str}
        Question: {question}
        Review points to avoid: {formatted_points}
        """

        # Send the prompt to the LLM and retrieve the raw response
        raw = await self.client.generate_async(prompt)  # Timeout handling is managed by ChatGPTClient

        try:
            # Note: stripping code fences before json.loads is recommended, but
            # parsing is attempted directly; if it fails a defensive fallback is used.
            data = json.loads(raw)
            return {
                "answer": data["answer"],
                "confidence": float(data.get("confidence", 0.8)),
                "needs_polish": bool(data.get("needs_polish", False)),
            }
        except Exception:
            # Log an error and return a fallback response if parsing fails
            logger.exception("Failed to parse synthesis JSON, falling back to raw answer")
            return {
                "answer": raw.strip(),
                "confidence": 0.5,  # Default confidence for fallback
                "needs_polish": True,  # Assume polishing is needed
            }
