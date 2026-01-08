import importlib.util
import sys
from pathlib import Path
import pytest

from peer_review_mcp import server
from types import SimpleNamespace
from peer_review_mcp.models.review_point import ReviewPoint
from peer_review_mcp.models.review_result import ReviewResult
from peer_review_mcp.models.polish_comment import PolishComment
from peer_review_mcp.orchestrator.central_orchestrator import CentralOrchestrator
from peer_review_mcp.tools import answer_tool as answer_module
from peer_review_mcp.tools.validation_engine import ValidationEngine
from peer_review_mcp.LLM.chatgpt_client import ChatGPTClient
from peer_review_mcp.LLM.claude_client import ClaudeClient
from peer_review_mcp.LLM.gemini_client import GeminiClient


def _load_models_module():
    models_path = Path(__file__).resolve().parents[1] / "peer_review_mcp" / "models.py"
    spec = importlib.util.spec_from_file_location("peer_review_mcp.models_file", models_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_models_roundtrip():
    models_module = _load_models_module()
    models_module.Insight.model_rebuild()
    models_module.ValidateRequest.model_rebuild()
    models_module.ValidateResponse.model_rebuild()
    insight = models_module.Insight(
        risk_type="security",
        statement="Possible injection",
        why_it_matters="Could leak data",
        what_to_check="Validate input sanitization",
    )
    req = models_module.ValidateRequest(question="What is X?")
    resp = models_module.ValidateResponse(severity="high", insights=[insight], must_fix=["fix"], notes=["note"])
    assert req.question == "What is X?"
    assert resp.insights[0].risk_type == "security"


@pytest.mark.anyio
async def test_server_answer_with_peer_review_success(monkeypatch):
    async def _process(*, question, context_summary=None):
        return {"answer": "ok", "meta": {"used_peer_review": True}}

    monkeypatch.setattr(server, "_orchestrator", SimpleNamespace(process=_process))
    result = await server.answer_with_peer_review("q")
    assert result["answer"] == "ok"


@pytest.mark.anyio
async def test_validation_engine_reviewer_failure():
    class GoodReviewer:
        async def review(self, *, question, answer, context_summary, mode):
            return ReviewResult(mode=mode, items=[{"text": "x", "risk_type": "other", "severity": "low"}])

    class BadReviewer:
        async def review(self, *, question, answer, context_summary, mode):
            raise Exception("boom")

    engine = ValidationEngine()
    engine.reviewers = [GoodReviewer(), BadReviewer()]
    result = await engine.validate("q")
    assert result["count"] == 2
    assert result["items"][-1].risk_type == "api_tooling"


@pytest.mark.anyio
async def test_answer_tool_converts_review_points(monkeypatch):
    captured = {}

    class StubEngine:
        async def answer(self, *, question, context_summary=None, review_points=None):
            captured["review_points"] = review_points
            return {"answer": "ok"}

    monkeypatch.setattr(answer_module, "_engine", StubEngine())
    points = [ReviewPoint(text="a"), "b"]
    result = await answer_module.answer_tool(question="q", review_points=points)
    assert result["answer"] == "ok"
    assert captured["review_points"] == ["a", "b"]


@pytest.mark.anyio
async def test_orchestrator_process_with_polish(monkeypatch):
    co = CentralOrchestrator()

    async def _validate(question, context_summary=None):
        return {"items": [ReviewPoint(text="r1")]}

    async def _answer(*, question, context_summary=None, review_points=None):
        return {"answer": "draft", "confidence": 0.9, "needs_polish": True}

    async def _review_for_polish(*, question, answer, context_summary=None):
        return [PolishComment(text="clarify")]

    async def _generate_async(prompt):
        return "polished"

    monkeypatch.setattr("peer_review_mcp.orchestrator.central_orchestrator.validate_tool", _validate)
    monkeypatch.setattr("peer_review_mcp.orchestrator.central_orchestrator.answer_tool", _answer)
    monkeypatch.setattr(co.polishing_engine, "review_for_polish", _review_for_polish)
    monkeypatch.setattr(co.polish_llm, "generate_async", _generate_async)

    result = await co.process(question="q")
    assert result["answer"] == "polished"
    assert result["meta"]["polishing_applied"] is True


@pytest.mark.anyio
async def test_async_clients_generate_success():
    class ChatStub:
        class chat:
            class completions:
                @staticmethod
                async def create(*, model, messages, max_tokens):
                    class Message:
                        content = "ok"

                    class Choice:
                        message = Message()

                    class Response:
                        choices = [Choice()]

                    return Response()

    class ClaudeStub:
        class messages:
            @staticmethod
            async def create(*, model, max_tokens, messages, timeout):
                class Content:
                    text = "ok"

                class Message:
                    content = [Content()]

                return Message()

    class GeminiStub:
        class aio:
            class models:
                @staticmethod
                async def generate_content(*, model, contents):
                    class Response:
                        text = "ok"

                    return Response()

    chat_client = object.__new__(ChatGPTClient)
    chat_client.model = "m"
    chat_client.timeout = 1
    chat_client._async_client = ChatStub()

    claude_client = object.__new__(ClaudeClient)
    claude_client.model = "m"
    claude_client.timeout = 1
    claude_client._async_client = ClaudeStub()

    gemini_client = object.__new__(GeminiClient)
    gemini_client.model = "m"
    gemini_client.timeout = 1
    gemini_client._client = GeminiStub()

    assert await chat_client.generate_async("p") == "ok"
    assert await claude_client.generate_async("p") == "ok"
    assert await gemini_client.generate_async("p") == "ok"
