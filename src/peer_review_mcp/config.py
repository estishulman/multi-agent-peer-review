from dotenv import load_dotenv
import os

load_dotenv()

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = "models/gemini-flash-latest"

# Claude Configuration
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

# ChatGPT Configuration
CHATGPT_API_KEY = os.getenv("OPENAI_API_KEY")
CHATGPT_MODEL = "gpt-4o-mini"

# Concurrency limits
try:
    LLM_MAX_CONCURRENCY = int(os.getenv("LLM_MAX_CONCURRENCY", "0") or "0")
except ValueError:
    LLM_MAX_CONCURRENCY = 0

