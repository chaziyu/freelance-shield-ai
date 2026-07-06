import os
import re
import sys
import traceback
from datetime import date, datetime
from functools import wraps
from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlmodel import Session

from app.db.database import engine
from app.services.domain_service import (
    DomainService,
    StateTransitionError,
    ValidationError,
)

mcp = FastMCP(
    "freelance-project-mcp",
    instructions=(
        "Restricted internal STDIO-only tools for FreelanceShield AI. "
        "Tools return JSON-compatible dictionaries with 'ok' and 'data' or 'error'."
    ),
)

service = DomainService()

# --- Config and constants ---
ADK_DISCUSSION_TOOLS = ["create_project_from_terms", "save_discussion_facts"]
ADK_CONTRACT_TOOLS = [
    "get_contract_template",
    "create_contract_version",
    "create_signature_request",
]
ADK_COMMUNICATION_TOOLS = [
    "get_latest_active_contract",
    "get_due_communications",
    "queue_routine_update",
    "create_scope_change_request",
]
ADK_SAFETY_TOOLS = ["evaluate_automation_policy"]
ADK_TIMELINE_TOOLS = ["get_project_timeline"]


# --- Request Schemas ---
class CreateProjectFromTermsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(..., min_length=1, max_length=255)
    client_name: str | None = Field(default=None, max_length=255)
    source_platform: str = Field(..., min_length=1, max_length=50)


class SaveDiscussionFactsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    extracted_facts: dict[str, Any]
    missing_fields: list[str]
    risk_flags: list[str]
    raw_input: str = Field(..., min_length=1, max_length=100000)


class GetContractTemplateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateContractVersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    agreement_code: str = Field(..., min_length=1, max_length=50)
    scope: str = Field(..., min_length=1, max_length=5000)
    deliverables_json: str = Field(..., min_length=1, max_length=10000)
    revision_limit: int | None = Field(default=None, ge=0)
    fee_amount_minor: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    payment_terms: str | None = Field(default=None, max_length=1000)
    effective_start_date: date | None = Field(default=None)
    milestone_plan_json: str | None = Field(default=None, max_length=10000)


class CreateSignatureRequestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agreement_version_id: UUID


class GetLatestActiveContractRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID


class CreateMilestonesFromContractRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    agreement_version_id: UUID


class GetDueCommunicationsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID


class QueueRoutineUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    agreement_version_id: UUID
    requested_action: str = Field(..., min_length=1, max_length=50)
    idempotency_key: str = Field(..., min_length=1, max_length=255)
    milestone_id: UUID | None = Field(default=None)

    @field_validator("requested_action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        valid_actions = {
            "kickoff_confirmation",
            "deadline_reminder",
            "review_request",
            "delivery_confirmation",
        }
        if v not in valid_actions:
            raise ValueError(f"Invalid requested_action for routine update: {v}")
        return v


class CreateScopeChangeRequestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_reply_id: UUID
    summary: str = Field(..., min_length=1, max_length=1000)


class EvaluateAutomationPolicyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    agreement_version_id: UUID
    requested_action: str = Field(..., min_length=1, max_length=50)
    milestone_id: UUID | None = Field(default=None)
    message_type: str | None = Field(default=None, max_length=50)

    @field_validator("requested_action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        valid_actions = {
            "kickoff_confirmation",
            "deadline_reminder",
            "review_request",
            "delivery_confirmation",
            "delay",
            "payment",
            "dispute",
            "scope_change",
            "apology",
            "compensation",
            "legal",
        }
        if v not in valid_actions:
            raise ValueError(f"Invalid requested_action: {v}")
        return v


class GetProjectTimelineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID


# --- Helpers & Sanitization ---
def serialize_entity(entity: Any) -> Any:
    if hasattr(entity, "model_dump"):
        return entity.model_dump(mode="json")
    if isinstance(entity, list):
        return [serialize_entity(item) for item in entity]
    if isinstance(entity, dict):
        return {k: serialize_entity(v) for k, v in entity.items()}
    if isinstance(entity, UUID):
        return str(entity)
    if isinstance(entity, (datetime, date)):
        return entity.isoformat()
    return entity


def sanitize_message(msg: str) -> str:
    if not msg:
        return ""
    # Remove file paths (e.g., C:\foo\bar or /foo/bar)
    msg = re.sub(r"[a-zA-Z]:\\[\\\w\-\.\s]+", "[PATH]", msg)
    msg = re.sub(r"/[/\w\-\.\s]+", "[PATH]", msg)

    # Remove potential secrets from environment
    for k, v in os.environ.items():
        if any(sec in k.upper() for sec in ["KEY", "SECRET", "PASSWORD", "TOKEN"]):
            if v and len(v) > 3 and v in msg:
                msg = msg.replace(v, "[SECRET]")

    # Check for SQL/database error patterns
    if "sqlite" in msg.lower() or "table" in msg.lower() or "select" in msg.lower():
        msg = "A database constraint or error occurred."

    return msg


def safe_tool(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result_data = func(*args, **kwargs)
            return {"ok": True, "data": result_data}
        except (ValidationError, ValueError) as e:
            safe_msg = sanitize_message(str(e))
            sys.stderr.write(f"Validation error in {func.__name__}: {safe_msg}\n")
            return {
                "ok": False,
                "error": {"code": "VALIDATION_ERROR", "message": safe_msg},
            }
        except StateTransitionError as e:
            safe_msg = sanitize_message(str(e))
            sys.stderr.write(f"State transition error in {func.__name__}: {safe_msg}\n")
            return {
                "ok": False,
                "error": {"code": "STATE_TRANSITION_ERROR", "message": safe_msg},
            }
        except Exception as e:
            sys.stderr.write(f"Unexpected error in {func.__name__}: {str(e)}\n")
            traceback.print_exc(file=sys.stderr)
            return {
                "ok": False,
                "error": {
                    "code": "INTERNAL_TOOL_ERROR",
                    "message": "The requested operation could not be completed.",
                },
            }

    return wrapper


# --- Tools ---
@mcp.tool()
@safe_tool
def create_project_from_terms(
    title: str,
    source_platform: str,
    client_name: str | None = None,
) -> dict[str, Any]:
    req = CreateProjectFromTermsRequest(
        title=title, source_platform=source_platform, client_name=client_name
    )
    with Session(engine) as session:
        project = service.create_project(
            session=session,
            title=req.title,
            client_name=req.client_name,
            source_platform=req.source_platform,
        )
        session.commit()
        session.refresh(project)
        return {"project": serialize_entity(project)}


@mcp.tool()
@safe_tool
def save_discussion_facts(
    project_id: str,
    extracted_facts: dict[str, Any],
    missing_fields: list[str],
    risk_flags: list[str],
    raw_input: str,
) -> dict[str, Any]:
    req = SaveDiscussionFactsRequest(
        project_id=UUID(project_id),
        extracted_facts=extracted_facts,
        missing_fields=missing_fields,
        risk_flags=risk_flags,
        raw_input=raw_input,
    )
    with Session(engine) as session:
        snapshot = service.save_discussion_facts(
            session=session,
            project_id=req.project_id,
            extracted_facts=req.extracted_facts,
            missing_fields=req.missing_fields,
            risk_flags=req.risk_flags,
            raw_input=req.raw_input,
        )
        session.commit()
        return {"snapshot_id": str(snapshot.id)}


@mcp.tool()
@safe_tool
def get_contract_template() -> dict[str, Any]:
    GetContractTemplateRequest()
    return {
        "template": {
            "name": "statement_of_work_v1",
            "sections": [
                "Scope",
                "Deliverables",
                "Revision limit",
                "Amount",
                "Payment terms",
                "Acceptance instruction",
            ],
            "safety_note": "No legal enforceability claim is included.",
        }
    }


@mcp.tool()
@safe_tool
def create_contract_version(
    project_id: str,
    agreement_code: str,
    scope: str,
    deliverables_json: str,
    revision_limit: int | None = None,
    fee_amount_minor: int | None = None,
    currency: str | None = None,
    payment_terms: str | None = None,
    effective_start_date: str | None = None,
    milestone_plan_json: str | None = None,
) -> dict[str, Any]:
    start_date = None
    if effective_start_date:
        start_date = date.fromisoformat(effective_start_date)
    req = CreateContractVersionRequest(
        project_id=UUID(project_id),
        agreement_code=agreement_code,
        scope=scope,
        deliverables_json=deliverables_json,
        revision_limit=revision_limit,
        fee_amount_minor=fee_amount_minor,
        currency=currency,
        payment_terms=payment_terms,
        effective_start_date=start_date,
        milestone_plan_json=milestone_plan_json,
    )
    with Session(engine) as session:
        agreement = service.create_agreement_draft(
            session=session,
            project_id=req.project_id,
            agreement_code=req.agreement_code,
            scope=req.scope,
            deliverables_json=req.deliverables_json,
            revision_limit=req.revision_limit,
            fee_amount_minor=req.fee_amount_minor,
            currency=req.currency,
            payment_terms=req.payment_terms,
            effective_start_date=req.effective_start_date,
            milestone_plan_json=req.milestone_plan_json,
        )
        session.commit()
        session.refresh(agreement)
        return {"agreement": serialize_entity(agreement)}


@mcp.tool()
@safe_tool
def create_signature_request(agreement_version_id: str) -> dict[str, Any]:
    req = CreateSignatureRequestRequest(agreement_version_id=UUID(agreement_version_id))
    with Session(engine) as session:
        agreement = service.transition_to_pending_signature(
            session=session,
            agreement_id=req.agreement_version_id,
            actor="contract_agent",
        )
        session.commit()
        return {"agreement_version_id": str(agreement.id)}


@mcp.tool()
@safe_tool
def get_latest_active_contract(project_id: str) -> dict[str, Any]:
    req = GetLatestActiveContractRequest(project_id=UUID(project_id))
    with Session(engine) as session:
        agreement = service.get_latest_active_contract(
            session=session, project_id=req.project_id
        )
        return {"agreement": serialize_entity(agreement)}


@mcp.tool()
@safe_tool
def create_milestones_from_contract(
    project_id: str, agreement_version_id: str
) -> dict[str, Any]:
    req = CreateMilestonesFromContractRequest(
        project_id=UUID(project_id),
        agreement_version_id=UUID(agreement_version_id),
    )
    with Session(engine) as session:
        milestones = service.create_milestones_from_contract(
            session=session,
            project_id=req.project_id,
            agreement_version_id=req.agreement_version_id,
        )
        session.commit()
        for m in milestones:
            session.refresh(m)
        return {"milestones": serialize_entity(milestones)}


@mcp.tool()
@safe_tool
def get_due_communications(project_id: str) -> dict[str, Any]:
    req = GetDueCommunicationsRequest(project_id=UUID(project_id))
    with Session(engine) as session:
        comms = service.get_due_communications(
            session=session, project_id=req.project_id
        )
        return {"communications": serialize_entity(comms)}


@mcp.tool()
@safe_tool
def queue_routine_update(
    project_id: str,
    agreement_version_id: str,
    requested_action: str,
    idempotency_key: str,
    milestone_id: str | None = None,
) -> dict[str, Any]:
    m_id = UUID(milestone_id) if milestone_id else None
    req = QueueRoutineUpdateRequest(
        project_id=UUID(project_id),
        agreement_version_id=UUID(agreement_version_id),
        requested_action=requested_action,
        idempotency_key=idempotency_key,
        milestone_id=m_id,
    )
    with Session(engine) as session:
        message = service.queue_routine_update(
            session=session,
            project_id=req.project_id,
            agreement_version_id=req.agreement_version_id,
            requested_action=req.requested_action,
            idempotency_key=req.idempotency_key,
            milestone_id=req.milestone_id,
        )
        session.commit()
        session.refresh(message)
        return {"message": serialize_entity(message)}


@mcp.tool()
@safe_tool
def create_scope_change_request(client_reply_id: str, summary: str) -> dict[str, Any]:
    req = CreateScopeChangeRequestRequest(
        client_reply_id=UUID(client_reply_id), summary=summary
    )
    with Session(engine) as session:
        sc_req = service.create_scope_change_request(
            session=session, client_reply_id=req.client_reply_id, summary=req.summary
        )
        session.commit()
        return {"scope_change_request_id": str(sc_req.id)}


@mcp.tool()
@safe_tool
def evaluate_automation_policy(
    project_id: str,
    agreement_version_id: str,
    requested_action: str,
    milestone_id: str | None = None,
    message_type: str | None = None,
) -> dict[str, Any]:
    m_id = UUID(milestone_id) if milestone_id else None
    req = EvaluateAutomationPolicyRequest(
        project_id=UUID(project_id),
        agreement_version_id=UUID(agreement_version_id),
        requested_action=requested_action,
        milestone_id=m_id,
        message_type=message_type,
    )
    with Session(engine) as session:
        result = service.evaluate_automation_policy(
            session=session,
            project_id=req.project_id,
            agreement_version_id=req.agreement_version_id,
            requested_action=req.requested_action,
            milestone_id=req.milestone_id,
            message_type=req.message_type,
        )
        return result


@mcp.tool()
@safe_tool
def get_project_timeline(project_id: str) -> dict[str, Any]:
    req = GetProjectTimelineRequest(project_id=UUID(project_id))
    with Session(engine) as session:
        timeline = service.get_project_timeline(
            session=session, project_id=req.project_id
        )
        return {"events": serialize_entity(timeline)}


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
