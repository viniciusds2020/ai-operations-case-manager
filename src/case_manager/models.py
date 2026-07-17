from typing import Literal

from pydantic import BaseModel, Field

CaseStatus = Literal["pending_review", "ready", "approved", "rejected", "executed"]


class PlanStep(BaseModel):
    tool: str
    description: str
    requires_approval: bool = False


class Case(BaseModel):
    id: str
    title: str
    requester: str
    filename: str
    sha256: str
    case_type: str
    confidence: float
    status: CaseStatus
    risk_score: float
    risk_reasons: list[str]
    extracted_fields: dict[str, str]
    missing_fields: list[str]
    plan: list[PlanStep]
    summary: str
    created_at: str
    updated_at: str


class Event(BaseModel):
    id: int | None = None
    case_id: str
    event_type: str
    actor: str
    detail: str
    created_at: str


class ReviewRequest(BaseModel):
    decision: Literal["approve", "reject"]
    actor: str = Field(min_length=2, max_length=100)
    reason: str = Field(min_length=5, max_length=500)


class ExecuteRequest(BaseModel):
    actor: str = Field(min_length=2, max_length=100)
