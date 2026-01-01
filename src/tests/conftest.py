import pytest
import asyncio
from peer_review_mcp.orchestrator.central_orchestrator import CentralOrchestrator


@pytest.fixture
def orchestrator():
    return CentralOrchestrator()


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# helper to stub GeminiClient.generate
@pytest.fixture
def stub_llm(monkeypatch):
    def _stub(response_text):
        monkeypatch.setattr(
            "peer_review_mcp.LLM.gemini_client.GeminiClient.generate",
            lambda self, prompt: response_text,
        )
    return _stub

