from typing import Optional
from peer_review_mcp.tools.validation_engine import ValidationEngine

_engine = ValidationEngine()


def validate_tool(question: str, context_summary: Optional[str] = None) -> dict:
    """
    MCP tool entrypoint.
    Validates question considering context.

    Args:
        question: The user's question
        context_summary: Optional summary of relevant context

    Returns:
        Dictionary with 'items' containing list of ReviewPoint objects
    """
    return _engine.validate(question, context_summary)
