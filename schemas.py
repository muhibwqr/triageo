from pydantic import BaseModel, Field
from typing import List, Literal

Severity = Literal["low", "medium", "high", "critical"]
Category = Literal["auth", "injection", "misconfig", "llm_misuse", "network", "other"]

class TriageResult(BaseModel):
    severity: Severity
    category: Category
    summary: str
    recommended_actions: List[str]
    needs_human_review: bool = True
    confidence: float = Field(ge=0.0, le=1.0, default=0.6)
    evidence: List[str] = []
