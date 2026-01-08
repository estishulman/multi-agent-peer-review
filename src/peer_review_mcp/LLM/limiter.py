import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncIterator

_llm_semaphore: Optional[asyncio.Semaphore] = None


def configure_llm_concurrency(limit: int) -> None:
    """Set a global concurrency limit for async LLM calls."""
    global _llm_semaphore
    if limit and limit > 0:
        _llm_semaphore = asyncio.Semaphore(limit)
    else:
        _llm_semaphore = None


@asynccontextmanager
async def llm_concurrency() -> AsyncIterator[None]:
    """Async context manager that enforces the configured concurrency limit."""
    if _llm_semaphore is None:
        yield
        return
    async with _llm_semaphore:
        yield
