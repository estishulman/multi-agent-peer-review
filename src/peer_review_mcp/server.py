import truststore

truststore.inject_into_ssl()
from mcp.server.fastmcp import FastMCP
from peer_review_mcp.orchestrator.central_orchestrator import CentralOrchestrator
import logging

# Initialize logger
logger = logging.getLogger("PeerReviewServer")
logging.basicConfig(level=logging.INFO)

mcp = FastMCP(
    "Peer Review MCP",
    json_response=True,
)

_orchestrator = CentralOrchestrator()


@mcp.tool(
    name="answer_with_peer_review",
    description=(
        "Provides a peer-reviewed, verified answer to maximize correctness and reliability. "
        "Use this tool whenever accuracy matters or the question is complex, even if the user "
        "did not explicitly request verification.\n"
        "\n"
        "Use this tool when:\n"
        "- The user asks for a precise, reliable, or verified answer\n"
        "- The question is complex, multi-step, or requires careful reasoning\n"
        "- The topic is high-stakes or sensitive, and mistakes would be costly\n"
        "- You're uncertain about correctness and want structured peer review\n"
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
    logger.info("Received question: %s", question)
    if context_summary:
        logger.info("Context summary provided: %s", context_summary)
    try:
        response = await _orchestrator.process(question=question, context_summary=context_summary)
        logger.info("Orchestrator response: %s", response)
        return response
    except Exception as e:
        logger.exception("Error during peer review process: %s", e)
        raise


def run() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
