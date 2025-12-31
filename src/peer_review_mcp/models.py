from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal

Severity = Literal["low", "medium", "high"]
RiskType = Literal["assumptions", "api_tooling", "edge_cases", "concurrency", "security", "other"]

class Insight(BaseModel):
    risk_type: RiskType
    statement: str = Field(..., description="What might be wrong / risky")
    why_it_matters: str = Field(..., description="Impact if wrong")
    what_to_check: str = Field(..., description="Concrete verification step")

class ValidateRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Original user question (only)")
    policy: str | None = Field(
        default=None,
        description="Optional policy/flags, e.g. '--verify' or 'high_precision'",
    )

class ValidateResponse(BaseModel):
    severity: Severity
    insights: list[Insight]
    must_fix: list[str] = []
    notes: list[str] = []
