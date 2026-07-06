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
from app.services.adk_workflow import AdkWorkflowService
from app.services.errors import AppError
from app.services.workflow import WorkflowService
from app.services.workflow_backend import (
    require_configured_workflow_backend,
    use_local_workflow,
)

router = APIRouter(prefix="/api", tags=["workflow"])
service = WorkflowService()
adk_service = AdkWorkflowService()


async def safe_call(fn, *, require_workflow_backend: bool = True):
    try:
        if require_workflow_backend:
            require_configured_workflow_backend()
        result = fn()
        return await result if isawaitable(result) else result
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
async def analyse_intake(request: IntakeAnalyseRequest) -> IntakeAnalyseResponse:
    return await safe_call(
        lambda: _write(
            lambda: service.analyse_intake(request),
            lambda: adk_service.analyse_intake(request),
        )
    )


@router.post(
    "/projects/{project_id}/agreements",
    response_model=CreateAgreementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agreement(
    project_id: UUID, request: CreateAgreementRequest
) -> CreateAgreementResponse:
    return await safe_call(
        lambda: _write(
            lambda: service.create_agreement(project_id, request),
            lambda: adk_service.create_agreement(project_id, request),
        )
    )


@router.post(
    "/projects/{project_id}/acceptance",
    response_model=AcceptanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_acceptance(
    project_id: UUID, request: AcceptanceRequest
) -> AcceptanceResponse:
    return await safe_call(
        lambda: _write(
            lambda: service.record_acceptance(project_id, request),
            lambda: adk_service.record_acceptance(project_id, request),
        )
    )


@router.post(
    "/projects/{project_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_evidence(
    project_id: UUID, request: EvidenceRequest
) -> EvidenceResponse:
    return await safe_call(
        lambda: _write(
            lambda: service.record_evidence(project_id, request),
            lambda: adk_service.record_evidence(project_id, request),
        )
    )


@router.post("/projects/{project_id}/follow-up", response_model=FollowUpResponse)
async def create_follow_up(
    project_id: UUID, request: FollowUpRequest
) -> FollowUpResponse:
    return await safe_call(
        lambda: _write(
            lambda: service.create_follow_up(project_id, request),
            lambda: adk_service.create_follow_up(project_id, request),
        )
    )


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: UUID) -> ProjectDetailResponse:
    return await safe_call(
        lambda: service.get_project_detail(project_id),
        require_workflow_backend=False,
    )


@router.get("/projects/{project_id}/timeline", response_model=TimelineResponse)
async def get_timeline(project_id: UUID) -> TimelineResponse:
    return await safe_call(
        lambda: service.get_timeline(project_id),
        require_workflow_backend=False,
    )


@router.get("/projects/{project_id}/audit", response_model=AuditResponse)
async def get_audit(project_id: UUID) -> AuditResponse:
    return await safe_call(
        lambda: service.get_audit(project_id),
        require_workflow_backend=False,
    )


async def _write(local_call, adk_call):
    if use_local_workflow():
        return local_call()
    return await adk_call()
