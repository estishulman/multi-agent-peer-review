import logging
from openai import OpenAI, AsyncOpenAI
from .limiter import llm_concurrency
from ..config import CHATGPT_API_KEY, CHATGPT_MODEL

logger = logging.getLogger(__name__)


class ChatGPTClient:  # Thin wrapper client for OpenAI ChatGPT: send prompts and return text
    """Singleton client for OpenAI ChatGPT API.

    Thin wrapper that sends prompts to OpenAI and returns raw text responses.

    Attributes:
        model (str): Model identifier used for requests.
        timeout (int): Timeout in seconds for API calls.
    """
    _instance = None
    _client = None
    _async_client = None
    DEFAULT_TIMEOUT = 30  # seconds

    def __new__(cls, model: str = CHATGPT_MODEL, timeout: int = DEFAULT_TIMEOUT):
        if cls._instance is None:
            cls._instance = super(ChatGPTClient, cls).__new__(cls)
            cls._instance.model = model
            cls._instance.timeout = timeout
            cls._instance._client = OpenAI(api_key=CHATGPT_API_KEY, timeout=timeout)
            cls._instance._async_client = AsyncOpenAI(api_key=CHATGPT_API_KEY, timeout=timeout)
            logger.info("ChatGPTClient singleton initialized with model: %s, timeout: %ds",
                       model, timeout)
        return cls._instance

    def generate(self, prompt: str) -> str:
        """
        Sends a prompt to the ChatGPT API and retrieves the generated response.

        Args:
            prompt: The input prompt to send to the API.

        Returns:
            The generated response

        Note:
            Uses the modern chat response shape (choices[0].message.content) as the
            primary source for generated text. A compatibility fallback is available
            for rare, older response shapes.
        """
        logger.info("Sending prompt to ChatGPT API: %s", prompt)
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
            )
            # Primary: choices[0].message.content; compatibility fallback covers rare legacy shapes
            try:
                text = response.choices[0].message.content
            except Exception:
                # Compatibility fallback (rare): attempt older response shape
                text = getattr(response.choices[0], 'text', '')
            logger.info("Received response from ChatGPT API: %s", text)
            return text
        except TimeoutError as e:
            logger.error("ChatGPT API call exceeded timeout")
            raise
        except Exception as e:
            logger.exception("Error during ChatGPT API call: %s", e)
            raise

    async def generate_async(self, prompt: str) -> str:
        """
        Sends a prompt to the ChatGPT API asynchronously and retrieves the generated response.

        Args:
            prompt: The input prompt to send to the API.

        Returns:
            The generated response.
        """
        logger.info("Sending prompt to ChatGPT API (async): %s", prompt)
        try:
            async with llm_concurrency():
                response = await self._async_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1024,
                )
            try:
                text = response.choices[0].message.content
            except Exception:
                text = getattr(response.choices[0], "text", "")
            logger.info("Received response from ChatGPT API (async): %s", text)
            return text
        except TimeoutError:
            logger.error("ChatGPT API call exceeded timeout")
            raise
        except Exception as e:
            logger.exception("Error during ChatGPT API call (async): %s", e)
            raise
