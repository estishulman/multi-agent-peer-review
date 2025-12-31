from google import genai
from ..config import GEMINI_API_KEY, DEFAULT_MODEL

class GeminiClient:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return response.text

