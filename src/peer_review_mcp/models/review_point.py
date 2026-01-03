from dataclasses import dataclass
from typing import Optional, Literal

RiskType = Literal["assumptions", "api_tooling", "edge_cases", "concurrency", "security", "other"]
Severity = Literal["low", "medium", "high"]


@dataclass
class ReviewPoint:
    """
    Structured review point with classification.
    Used by validation and synthesis engines to provide context about potential issues.
    """
    text: str
    risk_type: Optional[RiskType] = None
    severity: Optional[Severity] = None
    confidence: Optional[float] = None  # 0.0-1.0, importance of this review point

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/debugging."""
        return {
            "text": self.text,
            "risk_type": self.risk_type,
            "severity": self.severity,
            "confidence": self.confidence,
        }

