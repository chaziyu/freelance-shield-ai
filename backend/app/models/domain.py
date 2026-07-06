from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, UniqueConstraint, text
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


# --- Enums ---


class ProjectStatus(StrEnum):
    DISCUSSION_CAPTURED = "DISCUSSION_CAPTURED"
    TERMS_REVIEW = "TERMS_REVIEW"
    CONTRACT_PENDING_SIGNATURE = "CONTRACT_PENDING_SIGNATURE"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"
    SCOPE_CHANGE_PENDING = "SCOPE_CHANGE_PENDING"
    PAUSED = "PAUSED"


class AgreementStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_SIGNATURE = "PENDING_SIGNATURE"
    PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"


class PartyRole(StrEnum):
    freelancer = "freelancer"
    client = "client"


class SignatureStatus(StrEnum):
    pending = "pending"
    accepted = "accepted"


class MilestoneStatus(StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class RecordedBy(StrEnum):
    freelancer = "freelancer"
    system_demo = "system_demo"


class SendMode(StrEnum):
    routine_auto = "routine_auto"
    approval_required = "approval_required"


class MessageStatus(StrEnum):
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    DELIVERED_TO_DEMO_INBOX = "DELIVERED_TO_DEMO_INBOX"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    APPROVED = "APPROVED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    CANCELLED = "CANCELLED"


class ReplyClassification(StrEnum):
    ACKNOWLEDGEMENT = "ACKNOWLEDGEMENT"
    FEEDBACK = "FEEDBACK"
    QUESTION = "QUESTION"
    SCOPE_CHANGE = "SCOPE_CHANGE"
    CONCERN = "CONCERN"


class ScopeChangeStatus(StrEnum):
    detected = "detected"
    pending_review = "pending_review"
    accepted = "accepted"
    rejected = "rejected"


class InitiatedBy(StrEnum):
    freelancer = "freelancer"
    client = "client"


# --- SQLModel Entities ---


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    client_name: str | None = Field(default=None, nullable=True)
    source_platform: str
    status: str = Field(default=ProjectStatus.DISCUSSION_CAPTURED)
    automation_enabled: bool = Field(
        default=False, sa_column_kwargs={"server_default": "0"}
    )
    active_agreement_version_id: UUID | None = Field(
        default=None, nullable=True, foreign_key="agreement_versions.id"
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Legacy compatibility fields
    amount: float | None = Field(default=None, nullable=True)
    currency: str | None = Field(default=None, nullable=True)
    deadline: str | None = Field(default=None, nullable=True)
    invoice_due_date: str | None = Field(default=None, nullable=True)
    dispute_flag: bool = Field(default=False, sa_column_kwargs={"server_default": "0"})
    latest_policy_json: str | None = Field(default=None, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('DISCUSSION_CAPTURED', 'TERMS_REVIEW', "
            "'CONTRACT_PENDING_SIGNATURE', 'ACTIVE', 'COMPLETED', "
            "'CLOSED', 'SCOPE_CHANGE_PENDING', 'PAUSED', 'DRAFT', "
            "'TERMS_READY', 'ACCEPTANCE_PENDING', 'ACCEPTED', "
            "'IN_PROGRESS', 'DELIVERED', 'INVOICED', 'OVERDUE', "
            "'DISPUTED', 'RESOLUTION_PENDING')",
            name="ck_project_status",
        ),
    )


class AgreementVersion(SQLModel, table=True):
    __tablename__ = "agreement_versions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id")
    agreement_code: str
    version_number: int
    scope: str
    deliverables_json: str | None = Field(default=None, nullable=True)
    revision_limit: int | None = Field(default=None, nullable=True)
    fee_amount_minor: int | None = Field(default=None, nullable=True)
    currency: str | None = Field(default=None, nullable=True)
    payment_terms: str | None = Field(default=None, nullable=True)
    effective_start_date: date | None = Field(default=None, nullable=True)
    milestone_plan_json: str | None = Field(default=None, nullable=True)
    status: str = Field(
        default=AgreementStatus.DRAFT, sa_column_kwargs={"server_default": "'DRAFT'"}
    )
    created_at: datetime = Field(default_factory=utc_now)
    activated_at: datetime | None = Field(default=None, nullable=True)

    # Legacy compatibility fields
    deliverables: str | None = Field(default=None, nullable=True)
    amount: float | None = Field(default=None, nullable=True)
    deadline: str | None = Field(default=None, nullable=True)
    accepted_at: datetime | None = Field(default=None, nullable=True)
    acceptance_status: str | None = Field(default=None, nullable=True)

    __table_args__ = (
        UniqueConstraint("project_id", "version_number", name="uq_project_version"),
        Index(
            "uq_active_agreement",
            "project_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
            sqlite_where=text("status = 'ACTIVE'"),
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'PENDING_SIGNATURE', "
            "'PARTIALLY_ACCEPTED', 'ACTIVE', 'SUPERSEDED')",
            name="ck_agreement_status",
        ),
    )


class SignatureRecord(SQLModel, table=True):
    __tablename__ = "signature_records"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agreement_version_id: UUID = Field(foreign_key="agreement_versions.id")
    party_role: str
    signer_display_name: str
    accepted_at: datetime | None = Field(default=None, nullable=True)
    acceptance_text: str
    status: str = Field(default=SignatureStatus.pending)

    __table_args__ = (
        UniqueConstraint(
            "agreement_version_id", "party_role", name="uq_agreement_role"
        ),
        CheckConstraint(
            "party_role IN ('freelancer', 'client')", name="ck_signature_party_role"
        ),
        CheckConstraint(
            "status IN ('pending', 'accepted')", name="ck_signature_status"
        ),
    )


class Milestone(SQLModel, table=True):
    __tablename__ = "milestones"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id")
    agreement_version_id: UUID = Field(foreign_key="agreement_versions.id")
    title: str
    description: str | None = Field(default=None, nullable=True)
    due_at: datetime | None = Field(default=None, nullable=True)
    status: str = Field(default=MilestoneStatus.PLANNED)
    completion_recorded_at: datetime | None = Field(default=None, nullable=True)
    recorded_by: str | None = Field(default=None, nullable=True)
    source_plan_item_key: str | None = Field(default=None, nullable=True)

    __table_args__ = (
        Index(
            "uq_agreement_milestone_key",
            "agreement_version_id",
            "source_plan_item_key",
            unique=True,
            sqlite_where=text("source_plan_item_key IS NOT NULL"),
        ),
        CheckConstraint(
            "status IN ('PLANNED', 'IN_PROGRESS', "
            "'READY_FOR_REVIEW', 'COMPLETED', 'BLOCKED')",
            name="ck_milestone_status",
        ),
        CheckConstraint(
            "recorded_by IS NULL OR recorded_by IN ('freelancer', 'system_demo')",
            name="ck_milestone_recorded_by",
        ),
    )


class DiscussionFactSnapshot(SQLModel, table=True):
    __tablename__ = "discussion_fact_snapshots"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id")
    extracted_facts_json: str
    missing_fields_json: str
    risk_flags_json: str
    source_text_hash: str
    created_at: datetime = Field(default_factory=utc_now)


class ClientMessage(SQLModel, table=True):
    __tablename__ = "client_messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id")
    agreement_version_id: UUID = Field(foreign_key="agreement_versions.id")
    milestone_id: UUID | None = Field(
        default=None, nullable=True, foreign_key="milestones.id"
    )
    message_type: str
    body: str
    send_mode: str
    status: str
    scheduled_for: datetime | None = Field(default=None, nullable=True)
    delivered_at: datetime | None = Field(default=None, nullable=True)
    idempotency_key: str = Field(unique=True)

    __table_args__ = (
        CheckConstraint(
            "send_mode IN ('routine_auto', 'approval_required')",
            name="ck_message_send_mode",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'QUEUED', 'DELIVERED_TO_DEMO_INBOX', "
            "'ACKNOWLEDGED', 'APPROVED', 'APPROVAL_REQUIRED', 'CANCELLED')",
            name="ck_message_status",
        ),
    )


class ClientReply(SQLModel, table=True):
    __tablename__ = "client_replies"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id")
    client_message_id: UUID | None = Field(
        default=None, nullable=True, foreign_key="client_messages.id"
    )
    body: str
    classification: str
    possible_scope_change: bool = Field(default=False)
    received_at: datetime = Field(default_factory=utc_now)


class ScopeChangeRequest(SQLModel, table=True):
    __tablename__ = "scope_change_requests"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id")
    source_reply_id: UUID | None = Field(
        default=None, nullable=True, foreign_key="client_replies.id"
    )
    summary: str
    status: str = Field(default=ScopeChangeStatus.detected)
    proposed_contract_version_id: UUID | None = Field(
        default=None, nullable=True, foreign_key="agreement_versions.id"
    )
    affected_milestone_ids_json: str
    initiated_by: str
    created_at: datetime = Field(default_factory=utc_now)

    __table_args__ = (
        CheckConstraint(
            "status IN ('detected', 'pending_review', 'accepted', 'rejected')",
            name="ck_scope_change_status",
        ),
        CheckConstraint(
            "initiated_by IN ('freelancer', 'client')",
            name="ck_scope_change_initiated_by",
        ),
    )


class AuditEvent(SQLModel, table=True):
    __tablename__ = "audit_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID | None = Field(
        default=None, nullable=True, foreign_key="projects.id"
    )
    actor: str
    action: str
    metadata_json: str
    created_at: datetime = Field(default_factory=utc_now)


# --- Legacy compatibility tables ---


class EvidenceEvent(SQLModel, table=True):
    __tablename__ = "evidence_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id")
    event_type: str
    summary: str
    content_hash: str
    created_at: datetime = Field(default_factory=utc_now)


class CommunicationDraft(SQLModel, table=True):
    __tablename__ = "communication_drafts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id")
    draft_type: str
    body: str
    audit_status: str
    created_at: datetime = Field(default_factory=utc_now)
