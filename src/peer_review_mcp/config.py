from dotenv import load_dotenv
import os

load_dotenv()

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = "models/gemini-flash-latest"

# Claude Configuration
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

# Claude Opus Configuration
CLAUDE_OPUS_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # Same as Claude
CLAUDE_OPUS_MODEL = "claude-3-opus-20250729"

# ChatGPT Configuration
CHATGPT_API_KEY = os.getenv("OPENAI_API_KEY")
CHATGPT_MODEL = "gpt-4o-mini"

