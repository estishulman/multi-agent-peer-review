import os
import certifi
import logging

os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = certifi.where()
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from google import genai
from ..config import GEMINI_API_KEY, DEFAULT_MODEL

logger = logging.getLogger(__name__)


class GeminiClient:
    """Singleton client for Google Gemini API. Ensures only one client instance is created."""
    _instance = None
    _client = None
    DEFAULT_TIMEOUT = 30  # seconds

    def __new__(cls, model: str = DEFAULT_MODEL, timeout: int = DEFAULT_TIMEOUT):
        if cls._instance is None:
            cls._instance = super(GeminiClient, cls).__new__(cls)
            cls._instance.model = model
            cls._instance.timeout = timeout
            cls._instance._client = genai.Client(api_key=GEMINI_API_KEY)
            logger.info("GeminiClient singleton initialized with model: %s, timeout: %ds",
                       model, timeout)
        return cls._instance

    def generate(self, prompt: str) -> str:
        logger.info("Sending prompt to Gemini API: %s", prompt)
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            logger.info("Received response from Gemini API: %s", response.text)
            return response.text
        except TimeoutError as e:
            logger.error("Gemini API call exceeded timeout of %ds", self.timeout)
            raise
        except Exception as e:
            logger.exception("Error during Gemini API call: %s", e)
            raise

