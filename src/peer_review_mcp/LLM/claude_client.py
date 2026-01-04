import logging
from anthropic import Anthropic
from ..config import CLAUDE_API_KEY, CLAUDE_MODEL

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Singleton client for Anthropic Claude API. Ensures only one client instance is created."""
    _instance = None
    _client = None
    DEFAULT_TIMEOUT = 30  # seconds

    def __new__(cls, model: str = CLAUDE_MODEL, timeout: int = DEFAULT_TIMEOUT):
        if cls._instance is None:
            cls._instance = super(ClaudeClient, cls).__new__(cls)
            cls._instance.model = model
            cls._instance.timeout = timeout
            cls._instance._client = Anthropic(api_key=CLAUDE_API_KEY)
            logger.info("ClaudeClient singleton initialized with model: %s, timeout: %ds",
                       model, timeout)
        return cls._instance

    def generate(self, prompt: str) -> str:
        logger.info("Sending prompt to Claude API: %s", prompt)
        try:
            message = self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            logger.info("Received response from Claude API: %s", message.content[0].text)
            return message.content[0].text
        except Exception as e:
            logger.error("Claude API call failed: %s", str(e))
            raise

