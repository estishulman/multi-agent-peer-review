from typing import Optional
from ..LLM.gemini_client import GeminiClient
from ..LLM.synthesis_client import AnswerSynthesisClient
from ..tools.validation_engine import ValidationEngine

class SynthesisEngine:
    def __init__(self):
        gemini = GeminiClient()
        self.synthesizer = AnswerSynthesisClient(gemini)

    def answer(
        self,
        question: str,
        context_summary: Optional[str] = None,
        review_points: list[str] = None,
    ) -> dict:
        if review_points is None:
            review_points = []

        final_answer = self.synthesizer.synthesize(
            question=question,
            context_summary=context_summary,
            review_points=review_points,
        )

        return {
            "answer": final_answer,
            "review_count": len(review_points),
        }
