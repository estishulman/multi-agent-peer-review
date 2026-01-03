import logging
from openai import OpenAI
from ..config import CHATGPT_API_KEY, CHATGPT_MODEL

logger = logging.getLogger(__name__)


class ChatGPTClient:
    """Singleton client for OpenAI ChatGPT API. Ensures only one client instance is created."""
    _instance = None
    _client = None
    DEFAULT_TIMEOUT = 30  # seconds

    def __new__(cls, model: str = CHATGPT_MODEL, timeout: int = DEFAULT_TIMEOUT):
        if cls._instance is None:
            cls._instance = super(ChatGPTClient, cls).__new__(cls)
            cls._instance.model = model
            cls._instance.timeout = timeout
            cls._instance._client = OpenAI(api_key=CHATGPT_API_KEY)
            logger.info("ChatGPTClient singleton initialized with model: %s, timeout: %ds",
                       model, timeout)
        return cls._instance

    def generate(self, prompt: str) -> str:
        """
        Generate content from ChatGPT API.

        Args:
            prompt: The prompt to send to the model

        Returns:
            The generated text response

        Raises:
            Exception: If the API call fails
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("ChatGPT API call failed: %s", str(e))
            raise

