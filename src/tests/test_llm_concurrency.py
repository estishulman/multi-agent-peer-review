import asyncio
import pytest

from peer_review_mcp.LLM.limiter import configure_llm_concurrency, llm_concurrency


@pytest.mark.anyio
async def test_llm_concurrency_limit_enforced():
    configure_llm_concurrency(1)
    current = 0
    max_seen = 0
    lock = asyncio.Lock()

    async def worker():
        nonlocal current, max_seen
        async with llm_concurrency():
            async with lock:
                current += 1
                max_seen = max(max_seen, current)
            await asyncio.sleep(0.05)
            async with lock:
                current -= 1

    await asyncio.gather(worker(), worker())
    configure_llm_concurrency(0)
    assert max_seen == 1
