from datetime import date
from typing import Any
from uuid import UUID, uuid4

from mcp.server.fastmcp import FastMCP

from app.repositories.workflow import WorkflowRepository
from app.schemas.workflow import (
    AcceptanceRequest,
    CreateAgreementRequest,
    EvidenceRequest,
    FollowUpRequest,
    IntakeAnalyseRequest,
)
from app.services.workflow import WorkflowService
from app.utils.time import utc_now

mcp = FastMCP(
    "freelance-evidence-mcp",
    instructions=(
        "Internal STDIO-only tools for the FreelanceShield AI workflow. "
        "Tools return JSON-compatible dictionaries and never send messages."
    ),
)

service = WorkflowService()
repository = WorkflowRepository()


def _uuid(value: str) -> UUID:
    return UUID(value)


def _json(value) -> dict[str, Any]:
    return value.model_dump(mode="json")


@mcp.tool()
def create_project(
    chat_text: str,
    source_platform: str,
    reference_date: str | None = None,
) -> dict[str, Any]:
    request = IntakeAnalyseRequest(
        chat_text=chat_text,
        source_platform=source_platform,
        reference_date=date.fromisoformat(reference_date) if reference_date else None,
    )
    return _json(service.analyse_intake(request))


@mcp.tool()
def save_extracted_facts(
    project_id: str,
    extracted_facts: dict[str, Any],
) -> dict[str, Any]:
    project_uuid = _uuid(project_id)
    repository.get_project(project_uuid)
    event = repository.append_audit(
        event_id=uuid4(),
        project_id=project_uuid,
        actor="IntakeAgent",
        action="extracted_facts_saved",
        metadata={"fields": sorted(extracted_facts.keys())},
        now=utc_now(),
    )
    return _json(event)


@mcp.tool()
def get_contract_template() -> dict[str, Any]:
    event = repository.append_audit(
        event_id=uuid4(),
        project_id=None,
        actor="AgreementAgent",
        action="contract_template_read",
        metadata={"template": "statement_of_work_v1"},
        now=utc_now(),
    )
    return {
        "audit_event": _json(event),
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
        },
    }


@mcp.tool()
def create_agreement_version(
    project_id: str,
    scope: str,
    deliverables: str,
    revision_limit: int | None = None,
    amount: float | None = None,
    currency: str | None = None,
    deadline: str | None = None,
    payment_terms: str | None = None,
    change_reason: str | None = None,
) -> dict[str, Any]:
    request = CreateAgreementRequest(
        amount=amount,
        change_reason=change_reason,
        currency=currency,
        deadline=date.fromisoformat(deadline) if deadline else None,
        deliverables=deliverables,
        payment_terms=payment_terms,
        revision_limit=revision_limit,
        scope=scope,
    )
    return _json(service.create_agreement(_uuid(project_id), request))


@mcp.tool()
def record_acceptance(
    project_id: str,
    agreement_code: str,
    version_number: int,
    acceptance_text: str,
) -> dict[str, Any]:
    request = AcceptanceRequest(
        acceptance_text=acceptance_text,
        agreement_code=agreement_code,
        version_number=version_number,
    )
    return _json(service.record_acceptance(_uuid(project_id), request))


@mcp.tool()
def record_evidence_event(
    project_id: str,
    event_type: str,
    summary: str,
    invoice_due_date: str | None = None,
) -> dict[str, Any]:
    request = EvidenceRequest(
        event_type=event_type,
        invoice_due_date=(
            date.fromisoformat(invoice_due_date) if invoice_due_date else None
        ),
        summary=summary,
    )
    return _json(service.record_evidence(_uuid(project_id), request))


@mcp.tool()
def get_project_timeline(project_id: str) -> dict[str, Any]:
    return _json(service.get_timeline(_uuid(project_id)))


@mcp.tool()
def evaluate_follow_up_policy(
    project_id: str,
    dispute_declared: bool = False,
    dispute_message: str | None = None,
) -> dict[str, Any]:
    dispute = None
    if dispute_declared:
        dispute = {
            "declared": True,
            "message": dispute_message or "Client dispute recorded.",
        }
    request = FollowUpRequest(dispute=dispute)
    policy = service.evaluate_follow_up_policy_only(_uuid(project_id), request)
    return _json(policy)


@mcp.tool()
def create_draft_record(project_id: str) -> dict[str, Any]:
    return _json(service.create_draft_record(_uuid(project_id)))


@mcp.tool()
def append_audit_log(
    actor: str,
    action: str,
    metadata: dict[str, Any],
    project_id: str | None = None,
) -> dict[str, Any]:
    project_uuid = _uuid(project_id) if project_id else None
    if project_uuid:
        repository.get_project(project_uuid)
    event = repository.append_audit(
        event_id=uuid4(),
        project_id=project_uuid,
        actor=actor,
        action=action,
        metadata=metadata,
        now=utc_now(),
    )
    return _json(event)


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
