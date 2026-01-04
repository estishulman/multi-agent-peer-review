from typing import Optional
from peer_review_mcp.LLM.chatgpt_client import ChatGPTClient
from peer_review_mcp.LLM.synthesis_client import AnswerSynthesisClient


class SynthesisEngine:
    def __init__(self):
        chatgpt = ChatGPTClient()  # אם כבר החלפת ל-ChatGPTClient – עדכני כאן
        self.synthesizer = AnswerSynthesisClient(chatgpt)

    def answer(
        self,
        question: str,
        context_summary: Optional[str] = None,
        review_points: list[str] = None,
    ) -> dict:
        if review_points is None:
            review_points = []

        result = self.synthesizer.synthesize(
            question=question,
            context_summary=context_summary,
            review_points=review_points,
        )

        return {
            "answer": result["answer"],
            "confidence": result["confidence"],
            "needs_polish": result["needs_polish"],
            "review_count": len(review_points),
        }
