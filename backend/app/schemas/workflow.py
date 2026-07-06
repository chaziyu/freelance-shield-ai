from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectStatus(StrEnum):
    DRAFT = "DRAFT"
    TERMS_READY = "TERMS_READY"
    ACCEPTANCE_PENDING = "ACCEPTANCE_PENDING"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    INVOICED = "INVOICED"
    OVERDUE = "OVERDUE"
    CLOSED = "CLOSED"
    DISPUTED = "DISPUTED"
    RESOLUTION_PENDING = "RESOLUTION_PENDING"


class AcceptanceStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"


class EvidenceType(StrEnum):
    ACCEPTANCE = "ACCEPTANCE"
    DELIVERY = "DELIVERY"
    INVOICE = "INVOICE"
    SCOPE_CHANGE = "SCOPE_CHANGE"


class DraftType(StrEnum):
    ACCEPTANCE_REQUEST = "ACCEPTANCE_REQUEST"
    DELIVERY_CONFIRMATION = "DELIVERY_CONFIRMATION"
    PAYMENT_REMINDER = "PAYMENT_REMINDER"
    DISPUTE_CLARIFICATION = "DISPUTE_CLARIFICATION"


class DraftAuditStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED_TO_SHOW = "APPROVED_TO_SHOW"
    BLOCKED = "BLOCKED"


class TraceStatus(StrEnum):
    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class Project(BaseModel):
    id: UUID
    title: str
    client_name: str | None = None
    source_platform: str
    amount: float | None = None
    currency: str | None = None
    deadline: date | None = None
    invoice_due_date: date | None = None
    status: ProjectStatus
    dispute_flag: bool
    created_at: datetime
    updated_at: datetime


class ExtractedFacts(BaseModel):
    project_title: str
    amount: float | None = None
    currency: str | None = None
    deadline: date | None = None
    revision_limit: int | None = None
    payment_terms: str | None = None
    missing_fields: list[str]
    risk_flags: list[str]


class AgreementVersion(BaseModel):
    id: UUID
    project_id: UUID
    agreement_code: str
    version_number: int
    scope: str
    deliverables: str
    revision_limit: int | None = None
    amount: float | None = None
    currency: str | None = None
    deadline: date | None = None
    payment_terms: str | None = None
    acceptance_status: AcceptanceStatus
    accepted_at: datetime | None = None
    created_at: datetime


class EvidenceEvent(BaseModel):
    id: UUID
    project_id: UUID
    event_type: EvidenceType
    summary: str
    content_hash: str
    created_at: datetime


class CommunicationDraft(BaseModel):
    id: UUID
    project_id: UUID
    draft_type: DraftType
    body: str
    audit_status: DraftAuditStatus
    created_at: datetime


class AuditEvent(BaseModel):
    id: UUID
    project_id: UUID | None = None
    actor: str
    action: str
    metadata: dict[str, Any]
    created_at: datetime


class TraceEvent(BaseModel):
    actor: str
    action: str
    status: TraceStatus
    timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class TimelineEvent(BaseModel):
    content_hash: str | None = None
    event_type: str
    summary: str
    timestamp: datetime
    reference_id: str


class TimelineSummary(BaseModel):
    event_count: int
    latest_event_type: str | None = None
    latest_event_at: datetime | None = None
    hash_previews: list[str] = Field(default_factory=list)


class AuditSummary(BaseModel):
    event_count: int
    latest_actor: str | None = None
    latest_action: str | None = None
    latest_event_at: datetime | None = None


class FollowUpPolicy(BaseModel):
    allowed_draft_type: DraftType
    reason_codes: list[str]
    blocked_draft_types: list[DraftType]


class SafetyResult(BaseModel):
    safe_to_show: bool
    blocked: bool
    warnings: list[str]
    blocked_reasons: list[str]


class IntakeAnalyseRequest(BaseModel):
    chat_text: str = Field(min_length=1, max_length=5000)
    source_platform: str = Field(min_length=1, max_length=60)
    reference_date: date | None = None


class IntakeAnalyseResponse(BaseModel):
    project: Project
    extracted_facts: ExtractedFacts
    trace: list[TraceEvent]


class CreateAgreementRequest(BaseModel):
    scope: str = Field(min_length=1, max_length=2000)
    deliverables: str = Field(min_length=1, max_length=2000)
    revision_limit: int | None = Field(default=None, ge=0, le=100)
    amount: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    deadline: date | None = None
    payment_terms: str | None = Field(default=None, max_length=1000)
    change_reason: str | None = Field(default=None, max_length=1000)


class CreateAgreementResponse(BaseModel):
    agreement: AgreementVersion
    acceptance_message: str
    project_status: ProjectStatus
    trace: list[TraceEvent]


class AcceptanceRequest(BaseModel):
    agreement_code: str
    version_number: int
    acceptance_text: str


class AcceptanceResponse(BaseModel):
    agreement: AgreementVersion
    acceptance_evidence: EvidenceEvent
    project_status: ProjectStatus
    trace: list[TraceEvent]


class EvidenceRequest(BaseModel):
    event_type: EvidenceType
    summary: str = Field(min_length=1, max_length=2000)
    invoice_due_date: date | None = None


class EvidenceResponse(BaseModel):
    evidence: EvidenceEvent
    project_status: ProjectStatus
    trace: list[TraceEvent]


class DisputeInput(BaseModel):
    declared: bool
    message: str = Field(min_length=1, max_length=2000)


class FollowUpRequest(BaseModel):
    dispute: DisputeInput | None = None


class FollowUpResponse(BaseModel):
    policy: FollowUpPolicy
    safety: SafetyResult
    draft: CommunicationDraft | None
    trace: list[TraceEvent]


class ProjectDetailResponse(BaseModel):
    project: Project
    current_agreement: AgreementVersion | None
    latest_policy: FollowUpPolicy | None
    latest_draft: CommunicationDraft | None
    timeline_summary: TimelineSummary | None
    audit_summary: AuditSummary | None
    latest_trace: list[TraceEvent]


class TimelineResponse(BaseModel):
    project_id: UUID
    events: list[TimelineEvent]


class AuditResponse(BaseModel):
    project_id: UUID
    events: list[AuditEvent]
