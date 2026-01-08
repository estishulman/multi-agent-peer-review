import logging
from anthropic import Anthropic, AsyncAnthropic
from .limiter import llm_concurrency
from ..config import CLAUDE_API_KEY, CLAUDE_MODEL

logger = logging.getLogger(__name__)


class ClaudeClient:  # Thin wrapper client for Anthropic Claude: send prompts and return text
    """Singleton client for Anthropic Claude API.

    Thin wrapper that sends prompts to Claude and returns raw text responses.

    Attributes:
        model (str): Model identifier used for requests.
        timeout (int): Timeout in seconds for API calls.
    """
    _instance = None
    _client = None
    _async_client = None
    DEFAULT_TIMEOUT = 30  # seconds

    def __new__(cls, model: str = CLAUDE_MODEL, timeout: int = DEFAULT_TIMEOUT):
        if cls._instance is None:
            cls._instance = super(ClaudeClient, cls).__new__(cls)
            cls._instance.model = model
            cls._instance.timeout = timeout
            cls._instance._client = Anthropic(api_key=CLAUDE_API_KEY)
            cls._instance._async_client = AsyncAnthropic(api_key=CLAUDE_API_KEY)
            logger.info("ClaudeClient singleton initialized with model: %s, timeout: %ds",
                       model, timeout)
        return cls._instance

    def generate(self, prompt: str) -> str:
        """
            Sends a prompt to the Claude API and retrieves the generated response.

            Args:
                prompt: The input prompt to send to the API.

            Returns:
                The generated response as a string.

            Raises:
                TimeoutError: If the API call exceeds the timeout duration.
                Exception: For other errors during the API call.

            Note:
                Extracts the generated text from the Anthropic response shape and
                passes the configured timeout to the underlying client call.
            """
        logger.info("Sending prompt to Claude API: %s", prompt)
        try:
            message = self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                timeout=self.timeout  # Added timeout handling
            )
            logger.info("Received response from Claude API: %s", message.content[0].text)
            return message.content[0].text
        except TimeoutError as e:
            logger.error("Claude API call exceeded timeout of %ds", self.timeout)
            raise
        except Exception as e:
            logger.error("Claude API call failed: %s", str(e))
            raise

    async def generate_async(self, prompt: str) -> str:
        """
            Sends a prompt to the Claude API asynchronously and retrieves the generated response.

            Args:
                prompt: The input prompt to send to the API.

            Returns:
                The generated response as a string.

            Raises:
                TimeoutError: If the API call exceeds the timeout duration.
                Exception: For other errors during the API call.
            """
        logger.info("Sending prompt to Claude API (async): %s", prompt)
        try:
            async with llm_concurrency():
                message = await self._async_client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    timeout=self.timeout
                )
            logger.info("Received response from Claude API (async): %s", message.content[0].text)
            return message.content[0].text
        except TimeoutError:
            logger.error("Claude API call exceeded timeout of %ds", self.timeout)
            raise
        except Exception as e:
            logger.error("Claude API call failed (async): %s", str(e))
            raise
