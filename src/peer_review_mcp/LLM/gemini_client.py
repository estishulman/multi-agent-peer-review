import os
import certifi
import logging

os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = certifi.where()
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from google import genai
from ..config import GEMINI_API_KEY, DEFAULT_MODEL
from .limiter import llm_concurrency

logger = logging.getLogger(__name__)


class GeminiClient:  # Thin wrapper client for Google Gemini: send prompts and return text
    """
    Singleton client for Google Gemini API.

    Thin wrapper that sends prompts to Gemini and returns raw text responses.

    Attributes:
        model: The model to use for generating responses.
        timeout: Timeout duration for API calls.
    """
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
        """
        Sends a prompt to the Gemini API and retrieves the generated response.

        Args:
            prompt: The input prompt to send to the API.

        Returns:
            The generated response as a string.

        Raises:
            TimeoutError: If the API call exceeds the timeout duration.
            Exception: For other errors during the API call.
        """
        logger.info("Sending prompt to Gemini API: %s", prompt)
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            logger.info("Received response from Gemini API: %s", response.text)
            return response.text
        except TimeoutError as e:
            logger.error("Gemini API call exceeded timeout of %ds", self.timeout)
            raise
        except Exception as e:
            logger.exception("Error during Gemini API call: %s", e)
            raise

    async def generate_async(self, prompt: str) -> str:
        """
        Sends a prompt to the Gemini API asynchronously and retrieves the generated response.

        Args:
            prompt: The input prompt to send to the API.

        Returns:
            The generated response as a string.

        Raises:
            TimeoutError: If the API call exceeds the timeout duration.
            Exception: For other errors during the API call.
        """
        logger.info("Sending prompt to Gemini API (async): %s", prompt)
        try:
            async with llm_concurrency():
                response = await self._client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
            logger.info("Received response from Gemini API (async): %s", response.text)
            return response.text
        except TimeoutError:
            logger.error("Gemini API call exceeded timeout of %ds", self.timeout)
            raise
        except Exception as e:
            logger.exception("Error during Gemini API call (async): %s", e)
            raise
