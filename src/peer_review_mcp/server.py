#import certifi
#import os

#os.environ["SSL_CERT_FILE"] = certifi.where()
#os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

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
        "Provides a verified and double-checked answer designed to ensure correctness and reliability. "
        "Use this tool when the user asks for information that must be true, accurate, reliable, trustworthy, or verified, "
        "or when the user explicitly requests validation, confirmation, or a high-confidence response. "
        "In these cases, you must not answer the user directly without using this tool, "
        "as answering without verification could result in incorrect or untrusted information."
       "The tool expects the original user question only."
        "Expects a single input:- question: string (natural language user question)"

    ),
)
async def answer_with_peer_review(question: str) -> dict:
    return await _orchestrator.process(question=question)

    #f not question or not isinstance(question, str):
      #  raise ValueError("question is required and must be a string")

    #return await _orchestrator.process(
      #  question=question,
    #)

#async def answer_with_peer_review(question: str, debug: bool = False) -> dict:
   # return await _orchestrator.process(question=question, debug=debug)



def run() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
