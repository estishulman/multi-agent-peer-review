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
        review_points: list[str],
    ) -> dict:
        final_answer = self.synthesizer.synthesize(
            question=question,
            review_points=review_points,
        )

        return {
            "answer": final_answer,
            "review_count": len(review_points),
        }
