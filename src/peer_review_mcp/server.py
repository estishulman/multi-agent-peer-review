import logging
from mcp.server.fastmcp import FastMCP
from peer_review_mcp.orchestrator.central_orchestrator import CentralOrchestrator

logging.basicConfig(level=logging.INFO)

mcp = FastMCP(
    "Peer Review MCP",
    json_response=True,
)

_orchestrator = CentralOrchestrator()


@mcp.tool(
    name="answer_with_peer_review",
    description="Answer a question; uses peer review when needed"
)
async def answer_with_peer_review(question: str, debug: bool = False) -> dict:
    return await _orchestrator.process(question=question, debug=debug)


def run() -> None:
    mcp.run(transport="stdio")
