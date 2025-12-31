from __future__ import annotations
import os
from openai import OpenAI
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "PUT_YOUR_REAL_KEY_HERE"
client=OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
class Reviewer:
    name: str

    async def review(self, question: str) -> list[str]:
        raise NotImplementedError

class OpenAIReviewer(Reviewer):
    print(">>> OPENAI REVIEWER CALLED <<<")
    name = "openai_correctness"
    model = "gpt-4.1-mini"

    async def review(self, question: str) -> list[dict]:
        prompt = f"""
You are a strict peer reviewer for technical/coding answers.
You receive ONLY the user question. Do NOT answer the question.
Return ONLY risk-focused insights in JSON.

User question:
{question}
"""

        # Simple JSON output: we’ll parse it as dicts
        resp = client.responses.create(
            model=self.model,
            input=prompt,
            # We want structured JSON. See Structured Outputs docs. :contentReference[oaicite:3]{index=3}
            text={"format": {"type": "json_object"}},
        )

        # The SDK returns content; we’ll extract the text and json-load it
        import json
        txt = resp.output_text
        data = json.loads(txt)

        # Expect: {"insights":[{...},{...}]}
        return data.get("insights", [])

class AssumptionsReviewer(Reviewer):
    name = "assumptions"

    async def review(self, question: str) -> list[str]:
        # Placeholder: later you can call an LLM here
        hints = []
        if "always" in question.lower() or "never" in question.lower():
            hints.append("Watch for absolute claims (always/never) — may be incorrect.")
        return hints

class EdgeCasesReviewer(Reviewer):
    name = "edge_cases"

    async def review(self, question: str) -> list[str]:
        # Placeholder
        return ["Check missing edge cases (timeouts, retries, null/empty inputs)."]

class ToolingReviewer(Reviewer):
    name = "tooling"

    async def review(self, question: str) -> list[str]:
        # Placeholder
        if "python" in question.lower():
            return ["Verify Python version assumptions and library APIs (they change often)."]
        return []
