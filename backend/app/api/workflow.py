from inspect import isawaitable
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.schemas.workflow import (
    AcceptanceRequest,
    AcceptanceResponse,
    AuditResponse,
    CreateAgreementRequest,
    CreateAgreementResponse,
    EvidenceRequest,
    EvidenceResponse,
    FollowUpRequest,
    FollowUpResponse,
    IntakeAnalyseRequest,
    IntakeAnalyseResponse,
    ProjectDetailResponse,
    TimelineResponse,
)
from app.services.errors import AppError
from app.services.workflow import WorkflowService

router = APIRouter(prefix="/api", tags=["workflow"])

# IMPORTANT:
# The current React UI and API schemas are built for WorkflowService.
# Keep all Step 1–6 actions on this same persistence path.
service = WorkflowService()


async def safe_call(fn):
    """Run a workflow operation and convert known app errors to safe API errors."""
    try:
        result = fn()
        return await result if isawaitable(result) else result
    except AppError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc


@router.post(
    "/intake/analyse",
    response_model=IntakeAnalyseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyse_intake(request: IntakeAnalyseRequest) -> IntakeAnalyseResponse:
    """
    Step 1:
    Create and persist the project in the same SQLite database
    that Agreement Studio reads from.
    """
    return await safe_call(lambda: service.analyse_intake(request))


@router.get(
    "/projects/{project_id}",
    response_model=ProjectDetailResponse,
)
async def get_project(project_id: UUID) -> ProjectDetailResponse:
    """
    Load the exact project created during intake.
    Used by Agreement Studio and all later workflow pages.
    """
    return await safe_call(lambda: service.get_project_detail(project_id))


@router.post(
    "/projects/{project_id}/agreements",
    response_model=CreateAgreementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agreement(
    project_id: UUID,
    request: CreateAgreementRequest,
) -> CreateAgreementResponse:
    """
    Step 2:
    Create Agreement FS-001 Version 1 for the persisted project.
    """
    return await safe_call(
        lambda: service.create_agreement(project_id, request),
    )


@router.post(
    "/projects/{project_id}/acceptance",
    response_model=AcceptanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_acceptance(
    project_id: UUID,
    request: AcceptanceRequest,
) -> AcceptanceResponse:
    """
    Step 3:
    Record exact acceptance text against the current agreement version.
    """
    return await safe_call(
        lambda: service.record_acceptance(project_id, request),
    )


@router.post(
    "/projects/{project_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_evidence(
    project_id: UUID,
    request: EvidenceRequest,
) -> EvidenceResponse:
    """
    Step 4:
    Record delivery or invoice evidence.
    """
    return await safe_call(
        lambda: service.record_evidence(project_id, request),
    )


@router.post(
    "/projects/{project_id}/follow-up",
    response_model=FollowUpResponse,
)
async def create_follow_up(
    project_id: UUID,
    request: FollowUpRequest,
) -> FollowUpResponse:
    """
    Step 5:
    Evaluate follow-up policy and create a safe draft where allowed.
    """
    return await safe_call(
        lambda: service.create_follow_up(project_id, request),
    )


@router.get(
    "/projects/{project_id}/timeline",
    response_model=TimelineResponse,
)
async def get_timeline(project_id: UUID) -> TimelineResponse:
    """Step 4 timeline/evidence view."""
    return await safe_call(lambda: service.get_timeline(project_id))


@router.get(
    "/projects/{project_id}/audit",
    response_model=AuditResponse,
)
async def get_audit(project_id: UUID) -> AuditResponse:
    """Audit trail view."""
    return await safe_call(lambda: service.get_audit(project_id))