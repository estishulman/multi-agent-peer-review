from peer_review_mcp.tools.validation_engine import ValidationEngine

_engine = ValidationEngine()


def validate_tool(question: str) -> dict:
    """
    MCP tool entrypoint.
    """
    return _engine.validate(question)
