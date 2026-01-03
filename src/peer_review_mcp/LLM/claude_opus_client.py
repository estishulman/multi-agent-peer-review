import logging
from anthropic import Anthropic
from ..config import CLAUDE_OPUS_API_KEY, CLAUDE_OPUS_MODEL

logger = logging.getLogger(__name__)


class ClaudeOpusClient:
    """Singleton client for Anthropic Claude Opus API. Ensures only one client instance is created."""
    _instance = None
    _client = None
    DEFAULT_TIMEOUT = 30  # seconds

    def __new__(cls, model: str = CLAUDE_OPUS_MODEL, timeout: int = DEFAULT_TIMEOUT):
        if cls._instance is None:
            cls._instance = super(ClaudeOpusClient, cls).__new__(cls)
            cls._instance.model = model
            cls._instance.timeout = timeout
            cls._instance._client = Anthropic(api_key=CLAUDE_OPUS_API_KEY)
            logger.info("ClaudeOpusClient singleton initialized with model: %s, timeout: %ds",
                       model, timeout)
        return cls._instance

    def generate(self, prompt: str) -> str:
        """
        Generate content from Claude Opus API.

        Args:
            prompt: The prompt to send to the model

        Returns:
            The generated text response

        Raises:
            Exception: If the API call fails
        """
        try:
            message = self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error("Claude Opus API call failed: %s", str(e))
            raise

