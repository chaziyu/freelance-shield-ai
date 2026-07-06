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
from app.services.workflow_backend import require_configured_workflow_backend

router = APIRouter(prefix="/api", tags=["workflow"])
service = WorkflowService()


def safe_call(fn, *, require_workflow_backend: bool = True):
    try:
        if require_workflow_backend:
            require_configured_workflow_backend()
        return fn()
    except AppError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc


@router.post(
    "/intake/analyse",
    response_model=IntakeAnalyseResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyse_intake(request: IntakeAnalyseRequest) -> IntakeAnalyseResponse:
    return safe_call(lambda: service.analyse_intake(request))


@router.post(
    "/projects/{project_id}/agreements",
    response_model=CreateAgreementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agreement(
    project_id: UUID, request: CreateAgreementRequest
) -> CreateAgreementResponse:
    return safe_call(lambda: service.create_agreement(project_id, request))


@router.post(
    "/projects/{project_id}/acceptance",
    response_model=AcceptanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_acceptance(
    project_id: UUID, request: AcceptanceRequest
) -> AcceptanceResponse:
    return safe_call(lambda: service.record_acceptance(project_id, request))


@router.post(
    "/projects/{project_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_evidence(project_id: UUID, request: EvidenceRequest) -> EvidenceResponse:
    return safe_call(lambda: service.record_evidence(project_id, request))


@router.post("/projects/{project_id}/follow-up", response_model=FollowUpResponse)
def create_follow_up(project_id: UUID, request: FollowUpRequest) -> FollowUpResponse:
    return safe_call(lambda: service.create_follow_up(project_id, request))


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: UUID) -> ProjectDetailResponse:
    return safe_call(
        lambda: service.get_project_detail(project_id),
        require_workflow_backend=False,
    )


@router.get("/projects/{project_id}/timeline", response_model=TimelineResponse)
def get_timeline(project_id: UUID) -> TimelineResponse:
    return safe_call(
        lambda: service.get_timeline(project_id),
        require_workflow_backend=False,
    )


@router.get("/projects/{project_id}/audit", response_model=AuditResponse)
def get_audit(project_id: UUID) -> AuditResponse:
    return safe_call(
        lambda: service.get_audit(project_id),
        require_workflow_backend=False,
    )
