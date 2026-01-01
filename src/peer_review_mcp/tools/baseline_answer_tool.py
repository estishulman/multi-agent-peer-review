from peer_review_mcp.LLM.gemini_client import GeminiClient
from peer_review_mcp.prompts.baseline_answer import BASELINE_ANSWER_PROMPT


class BaselineAnswerTool:
    def __init__(self):
        self.client = GeminiClient()

    def answer(self, *, question: str) -> str:
        prompt = BASELINE_ANSWER_PROMPT.format(question=question)
        return self.client.generate(prompt)

