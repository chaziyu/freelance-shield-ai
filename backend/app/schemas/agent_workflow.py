from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvidenceBackedField(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: Any
    evidence_quote: str
    confidence: float


class ExtractedDiscussionFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    scope: EvidenceBackedField | None = None
    deliverables: EvidenceBackedField | None = None
    fee_amount_minor: EvidenceBackedField | None = None
    currency: EvidenceBackedField | None = None
    deadline: EvidenceBackedField | None = None
    revision_limit: EvidenceBackedField | None = None
    payment_terms: EvidenceBackedField | None = None
    missing_fields: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)


class DiscussionWorkflowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    discussion_text: str
    source_platform: str
    client_name: str | None = None


class ReviewedTerms(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    agreement_code: str
    scope: str
    deliverables: list[str]
    revision_limit: int | None = None
    fee_amount_minor: int | None = None
    currency: str | None = None
    payment_terms: str | None = None
    effective_start_date: date | None = None
    milestone_plan: list[dict[str, Any]] | None = None


class ReviewedTermsAttestation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    reviewed_terms_hash: str
    issued_at: float
    expires_at: float
    signature_or_hmac: str


class ContractDraftProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    agreement_code: str
    scope: str
    deliverables_json: str
    revision_limit: int | None = None
    fee_amount_minor: int | None = None
    currency: str | None = None
    payment_terms: str | None = None
    effective_start_date: date | None = None
    milestone_plan_json: str | None = None


class ContractDraftWorkflowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    reviewed_terms: ReviewedTerms
    attestation: ReviewedTermsAttestation


class ContractDraftWorkflowOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agreement: Any
    trace: list["AgentTraceEvent"]


class DueUpdateWorkflowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    test_time: datetime | None = None


class RoutineUpdateCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    agreement_version_id: UUID
    milestone_id: UUID | None = None
    message_type: str
    body: str


class ClientReplyClassificationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reply_text: str


class ClientReplyClassificationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    classification: Literal[
        "ACKNOWLEDGEMENT", "FEEDBACK", "QUESTION", "SCOPE_CHANGE", "CONCERN"
    ]
    confidence: float
    evidence_quote: str
    recommended_next_action: str
    trace: list["AgentTraceEvent"]


class ScopeChangeWorkflowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_reply_id: UUID
    summary: str


class SafetyAuditDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal[
        "safe_to_show",
        "blocked",
        "warnings",
        "blocked_reasons",
        "required_human_review",
    ]
    blocked: bool
    warnings: list[str] = Field(default_factory=list)
    blocked_reasons: list[str] = Field(default_factory=list)
    required_human_review: bool


class SafetyValidationReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_type: str
    candidate_hash: str
    deterministic_checks_passed: bool
    failed_check_codes: list[str]
    issued_at: float
    expires_at: float
    receipt_signature: str


class AgentTraceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    step_number: int
    timestamp: datetime
    agent_name: str
    event_type: str
    tool_name: str | None = None
    status: str
    safe_summary: str


class WorkflowResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ok: bool
    data: dict[str, Any] | None = None
    trace: list[AgentTraceEvent] = Field(default_factory=list)
    error: dict[str, Any] | None = None
