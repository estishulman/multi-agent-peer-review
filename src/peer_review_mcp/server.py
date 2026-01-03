import truststore

truststore.inject_into_ssl()
from mcp.server.fastmcp import FastMCP
from peer_review_mcp.orchestrator.central_orchestrator import CentralOrchestrator

mcp = FastMCP(
    "Peer Review MCP",
    json_response=True,
)

_orchestrator = CentralOrchestrator()


@mcp.tool(
    name="answer_with_peer_review",
    description=(
        "Provides a peer-reviewed, verified answer to ensure correctness and reliability. "
        "Use this tool when:\n"
        "- The user asks for information that MUST be accurate, reliable, or trustworthy\n"
        "- The user explicitly requests validation or high-confidence verification\n"
        "- The topic requires careful consideration of edge cases or hidden assumptions\n"
        "- You're uncertain about correctness and want multi-model validation\n"
        "\n"
        "The tool performs structured peer review:\n"
        "- Phase A (Always): Validates question for potential issues + generates answer\n"
        "- Phase B (Conditional): Polishes answer if quality metrics indicate need\n"
        "\n"
        "Parameters:\n"
        "- question (required): The user's original question\n"
        "- context_summary (optional): Brief summary of relevant prior context, if any. "
        "Do NOT send full chat history. Only include relevant background that affects the answer.\n"
        "\n"
        "Returns:\n"
        "- answer: Peer-reviewed answer (str), or None if system cannot verify\n"
        "- meta: Processing metadata (phase, confidence, review_points, timing)\n"
        "\n"
        "IMPORTANT: If answer is None, respond directly to the user without using this tool again."
    ),
)
async def answer_with_peer_review(question: str, context_summary: str = None) -> dict:
    return await _orchestrator.process(question=question, context_summary=context_summary)



def run() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
