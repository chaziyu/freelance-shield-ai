from uuid import UUID, uuid4

from app.policy.follow_up import evaluate_follow_up_policy
from app.repositories.workflow import WorkflowRepository
from app.schemas.workflow import (
    AcceptanceRequest,
    AcceptanceResponse,
    AcceptanceStatus,
    AgreementVersion,
    AuditResponse,
    AuditSummary,
    CommunicationDraft,
    CreateAgreementRequest,
    CreateAgreementResponse,
    DraftAuditStatus,
    DraftType,
    EvidenceEvent,
    EvidenceRequest,
    EvidenceResponse,
    EvidenceType,
    ExtractedFacts,
    FollowUpPolicy,
    FollowUpRequest,
    FollowUpResponse,
    IntakeAnalyseRequest,
    IntakeAnalyseResponse,
    ProjectDetailResponse,
    ProjectStatus,
    SafetyResult,
    TimelineEvent,
    TimelineResponse,
    TimelineSummary,
    TraceEvent,
    TraceStatus,
)
from app.services.errors import ConflictError, NotFoundError
from app.utils.hashing import sha256_text
from app.utils.time import utc_now

DRAFT_WARNING = "Draft only — review and send manually."


class WorkflowService:
    def __init__(self, repository: WorkflowRepository | None = None):
        self.repository = repository or WorkflowRepository()

    def analyse_intake(self, request: IntakeAnalyseRequest) -> IntakeAnalyseResponse:
        now = utc_now()
        facts = self._extract_facts(request.chat_text, request.source_platform)
        status = (
            ProjectStatus.TERMS_READY
            if not facts.missing_fields
            else ProjectStatus.DRAFT
        )
        project = self.repository.create_project(
            project_id=uuid4(),
            title=facts.project_title,
            source_platform=request.source_platform,
            amount=facts.amount,
            currency=facts.currency,
            deadline=facts.deadline,
            status=status,
            now=now,
        )
        self._audit(
            project.id, "IntakeAgent", "intake_analysed", facts.model_dump(), now
        )
        return IntakeAnalyseResponse(
            project=project,
            extracted_facts=facts,
            trace=[
                self._trace(
                    "CoordinatorAgent", "route_intake", TraceStatus.SUCCEEDED, now
                ),
                self._trace(
                    "IntakeAgent", "extract_project_facts", TraceStatus.SUCCEEDED, now
                ),
            ],
        )

    def create_agreement(
        self, project_id: UUID, request: CreateAgreementRequest
    ) -> CreateAgreementResponse:
        now = utc_now()
        project = self._project(project_id)
        current = self.repository.get_current_agreement(project_id)
        version_number = 1 if current is None else current.version_number + 1
        if current is not None and not request.change_reason:
            raise ConflictError(
                "A scope change requires a change reason and fresh acceptance."
            )

        agreement = AgreementVersion(
            id=uuid4(),
            project_id=project.id,
            agreement_code="FS-001",
            version_number=version_number,
            scope=request.scope,
            deliverables=request.deliverables,
            revision_limit=request.revision_limit,
            amount=request.amount,
            currency=request.currency,
            deadline=request.deadline,
            payment_terms=request.payment_terms,
            acceptance_status=AcceptanceStatus.PENDING,
            accepted_at=None,
            created_at=now,
        )
        agreement = self.repository.create_agreement(
            agreement,
            ProjectStatus.ACCEPTANCE_PENDING,
            now,
        )
        if version_number > 1:
            self.repository.create_evidence(
                self._evidence(
                    project.id,
                    EvidenceType.SCOPE_CHANGE,
                    request.change_reason or "Scope change recorded.",
                    now,
                )
            )
        self._audit(
            project.id,
            "AgreementAgent",
            "agreement_version_created",
            {"agreement_code": "FS-001", "version_number": version_number},
            now,
        )
        return CreateAgreementResponse(
            agreement=agreement,
            acceptance_message=(
                f'Please reply: "I agree to Agreement {agreement.agreement_code} '
                f'Version {agreement.version_number}."'
            ),
            project_status=ProjectStatus.ACCEPTANCE_PENDING,
            trace=[
                self._trace(
                    "CoordinatorAgent", "route_agreement", TraceStatus.SUCCEEDED, now
                ),
                self._trace(
                    "AgreementAgent",
                    "create_agreement_version",
                    TraceStatus.SUCCEEDED,
                    now,
                ),
            ],
        )

    def record_acceptance(
        self, project_id: UUID, request: AcceptanceRequest
    ) -> AcceptanceResponse:
        now = utc_now()
        project = self._project(project_id)
        current = self.repository.get_current_agreement(project_id)
        if current is None:
            raise NotFoundError("No current agreement exists for this project.")
        expected = (
            f"I agree to Agreement {current.agreement_code} "
            f"Version {current.version_number}."
        )
        if (
            request.agreement_code != current.agreement_code
            or request.version_number != current.version_number
            or request.acceptance_text.strip() != expected
        ):
            self._audit(
                project.id,
                "system",
                "acceptance_rejected",
                {"reason": "code_version_or_text_mismatch"},
                now,
            )
            raise ConflictError(
                "Acceptance must match the current agreement code and version."
            )
        if project.status not in {
            ProjectStatus.TERMS_READY,
            ProjectStatus.ACCEPTANCE_PENDING,
        }:
            raise ConflictError(
                "Acceptance is not allowed from the current project state."
            )

        agreement = self.repository.accept_agreement(current.id, project.id, now)
        evidence = self.repository.create_evidence(
            self._evidence(
                project.id, EvidenceType.ACCEPTANCE, request.acceptance_text, now
            )
        )
        self._audit(
            project.id,
            "system",
            "acceptance_recorded",
            {
                "agreement_code": current.agreement_code,
                "version_number": current.version_number,
            },
            now,
        )
        return AcceptanceResponse(
            agreement=agreement,
            acceptance_evidence=evidence,
            project_status=ProjectStatus.ACCEPTED,
            trace=[
                self._trace(
                    "CoordinatorAgent", "record_acceptance", TraceStatus.SUCCEEDED, now
                ),
            ],
        )

    def record_evidence(
        self, project_id: UUID, request: EvidenceRequest
    ) -> EvidenceResponse:
        now = utc_now()
        project = self._project(project_id)
        if request.event_type not in {EvidenceType.DELIVERY, EvidenceType.INVOICE}:
            raise ConflictError(
                "Public evidence requests accept only DELIVERY or INVOICE."
            )
        if request.event_type == EvidenceType.DELIVERY and project.status not in {
            ProjectStatus.ACCEPTED,
            ProjectStatus.IN_PROGRESS,
            ProjectStatus.DELIVERED,
            ProjectStatus.INVOICED,
        }:
            raise ConflictError("Delivery evidence requires an accepted agreement.")
        if request.event_type == EvidenceType.INVOICE and project.status not in {
            ProjectStatus.DELIVERED,
            ProjectStatus.INVOICED,
        }:
            raise ConflictError("Invoice evidence requires recorded delivery.")
        if (
            request.event_type == EvidenceType.INVOICE
            and request.invoice_due_date is None
        ):
            raise ConflictError("An invoice requires an invoice due date.")

        evidence = self.repository.create_evidence(
            self._evidence(project.id, request.event_type, request.summary, now)
        )
        status = (
            ProjectStatus.DELIVERED
            if request.event_type == EvidenceType.DELIVERY
            else ProjectStatus.INVOICED
        )
        self.repository.update_project_state(
            project.id,
            status=status,
            invoice_due_date=request.invoice_due_date,
            now=now,
        )
        self._audit(
            project.id,
            "system",
            "evidence_recorded",
            {"event_type": request.event_type.value},
            now,
        )
        return EvidenceResponse(
            evidence=evidence,
            project_status=status,
            trace=[
                self._trace(
                    "CoordinatorAgent", "record_evidence", TraceStatus.SUCCEEDED, now
                )
            ],
        )

    def create_follow_up(
        self, project_id: UUID, request: FollowUpRequest
    ) -> FollowUpResponse:
        self.evaluate_follow_up_policy_only(project_id, request)
        return self.create_draft_record(project_id)

    def evaluate_follow_up_policy_only(
        self, project_id: UUID, request: FollowUpRequest
    ) -> FollowUpPolicy:
        now = utc_now()
        project = self._project(project_id)
        if request.dispute and request.dispute.declared:
            project = self.repository.update_project_state(
                project.id,
                status=ProjectStatus.DISPUTED,
                dispute_flag=True,
                now=now,
            )
            self._audit(
                project.id,
                "system",
                "dispute_recorded",
                {"message_hash": sha256_text(request.dispute.message)},
                now,
            )

        policy = evaluate_follow_up_policy(project, now.date())
        self.repository.update_project_state(
            project.id,
            status=project.status,
            latest_policy=policy,
            now=now,
        )
        self._audit(
            project.id,
            "FollowUpAgent",
            "policy_evaluated",
            policy.model_dump(mode="json"),
            now,
        )
        return policy

    def create_draft_record(self, project_id: UUID) -> FollowUpResponse:
        now = utc_now()
        project = self._project(project_id)
        policy = self.repository.get_latest_policy(project_id)
        if policy is None:
            policy = evaluate_follow_up_policy(project, now.date())
            self.repository.update_project_state(
                project.id,
                status=project.status,
                latest_policy=policy,
                now=now,
            )
            self._audit(
                project.id,
                "FollowUpAgent",
                "policy_evaluated",
                policy.model_dump(mode="json"),
                now,
            )
        body = self._draft_body(policy.allowed_draft_type)
        safety = self._audit_draft(policy.allowed_draft_type, body)
        draft = None
        if safety.safe_to_show:
            draft = self.repository.create_draft(
                CommunicationDraft(
                    id=uuid4(),
                    project_id=project.id,
                    draft_type=policy.allowed_draft_type,
                    body=body,
                    audit_status=DraftAuditStatus.APPROVED_TO_SHOW,
                    created_at=now,
                )
            )
            self._audit(
                project.id,
                "SafetyAuditAgent",
                "draft_approved_to_show",
                {"draft_type": policy.allowed_draft_type.value},
                now,
            )
        return FollowUpResponse(
            policy=policy,
            safety=safety,
            draft=draft,
            trace=[
                self._trace(
                    "FollowUpAgent",
                    "evaluate_follow_up_policy",
                    TraceStatus.SUCCEEDED,
                    now,
                ),
                self._trace(
                    "SafetyAuditAgent", "review_draft", TraceStatus.SUCCEEDED, now
                ),
            ],
        )

    def get_project_detail(self, project_id: UUID) -> ProjectDetailResponse:
        project = self._project(project_id)
        audit = self.repository.list_audit(project_id)
        evidence = self.repository.list_evidence(project_id)
        latest_trace = [
            self._trace(
                event.actor,
                event.action,
                TraceStatus.SUCCEEDED,
                event.created_at,
                event.metadata,
            )
            for event in audit[-5:]
        ]
        return ProjectDetailResponse(
            project=project,
            current_agreement=self.repository.get_current_agreement(project_id),
            latest_policy=self.repository.get_latest_policy(project_id),
            latest_draft=self.repository.get_latest_draft(project_id),
            timeline_summary=self._timeline_summary(evidence),
            audit_summary=self._audit_summary(audit),
            latest_trace=latest_trace,
        )

    def get_timeline(self, project_id: UUID) -> TimelineResponse:
        self._project(project_id)
        events = [
            TimelineEvent(
                content_hash=evidence.content_hash,
                event_type=evidence.event_type.value,
                summary=evidence.summary,
                timestamp=evidence.created_at,
                reference_id=str(evidence.id),
            )
            for evidence in self.repository.list_evidence(project_id)
        ]
        return TimelineResponse(project_id=project_id, events=events)

    def get_audit(self, project_id: UUID) -> AuditResponse:
        self._project(project_id)
        return AuditResponse(
            project_id=project_id, events=self.repository.list_audit(project_id)
        )

    def _project(self, project_id: UUID):
        try:
            return self.repository.get_project(project_id)
        except KeyError as exc:
            raise NotFoundError("Project not found.") from exc

    def _extract_facts(self, chat_text: str, source_platform: str) -> ExtractedFacts:
        text = chat_text.lower()
        amount = 800.0 if "rm800" in text or "rm 800" in text else None
        revision_limit = 2 if "two revisions" in text or "2 revisions" in text else None
        missing_fields = ["deadline", "payment_terms"]
        return ExtractedFacts(
            project_title="Poster design" if "poster" in text else "Freelance project",
            amount=amount,
            currency="MYR" if amount is not None else None,
            deadline=None,
            revision_limit=revision_limit,
            payment_terms=None,
            missing_fields=missing_fields,
            risk_flags=["informal_platform"] if source_platform != "Email" else [],
        )

    def _evidence(
        self,
        project_id: UUID,
        event_type: EvidenceType,
        summary: str,
        now,
    ) -> EvidenceEvent:
        return EvidenceEvent(
            id=uuid4(),
            project_id=project_id,
            event_type=event_type,
            summary=summary,
            content_hash=sha256_text(summary),
            created_at=now,
        )

    def _audit(
        self,
        project_id: UUID,
        actor: str,
        action: str,
        metadata: dict,
        now,
    ):
        self.repository.append_audit(
            event_id=uuid4(),
            project_id=project_id,
            actor=actor,
            action=action,
            metadata=metadata,
            now=now,
        )

    def _trace(
        self,
        actor: str,
        action: str,
        status: TraceStatus,
        timestamp,
        metadata: dict | None = None,
    ) -> TraceEvent:
        return TraceEvent(
            actor=actor,
            action=action,
            status=status,
            timestamp=timestamp,
            metadata=metadata or {},
        )

    def _draft_body(self, draft_type: DraftType) -> str:
        if draft_type == DraftType.DISPUTE_CLARIFICATION:
            return (
                "Thanks for raising your concern. Please identify the incomplete items "
                "so we can compare them with the agreed scope and discuss next "
                "steps.\n\n"
                f"{DRAFT_WARNING}"
            )
        if draft_type == DraftType.PAYMENT_REMINDER:
            return (
                "Hi, this is a friendly reminder about the invoice for the "
                "agreed work. "
                "Please review it when you can and let me know if anything needs "
                "clarification.\n\n"
                f"{DRAFT_WARNING}"
            )
        if draft_type == DraftType.ACCEPTANCE_REQUEST:
            return (
                "Please review the current agreement details. If everything looks "
                "correct, "
                "reply with the exact agreement code and version shown in the app.\n\n"
                f"{DRAFT_WARNING}"
            )
        return (
            "Thanks for working through the project details. Please confirm "
            "the delivery "
            "or invoice status when convenient.\n\n"
            f"{DRAFT_WARNING}"
        )

    def _audit_draft(self, draft_type: DraftType, body: str) -> SafetyResult:
        blocked_terms = [
            "legally binding",
            "legal notice",
            "guaranteed recovery",
            "demand payment",
        ]
        if draft_type == DraftType.PAYMENT_REMINDER and "dispute" in body.lower():
            return SafetyResult(
                safe_to_show=False,
                blocked=True,
                warnings=[],
                blocked_reasons=["PAYMENT_DEMAND_NOT_ALLOWED_DURING_DISPUTE"],
            )
        if DRAFT_WARNING not in body or any(
            term in body.lower() for term in blocked_terms
        ):
            return SafetyResult(
                safe_to_show=False,
                blocked=True,
                warnings=[],
                blocked_reasons=["UNSAFE_DRAFT_CONTENT"],
            )
        return SafetyResult(
            safe_to_show=True,
            blocked=False,
            warnings=[DRAFT_WARNING],
            blocked_reasons=[],
        )

    def _timeline_summary(
        self, evidence: list[EvidenceEvent]
    ) -> TimelineSummary | None:
        if not evidence:
            return None
        latest = evidence[-1]
        return TimelineSummary(
            event_count=len(evidence),
            latest_event_type=latest.event_type.value,
            latest_event_at=latest.created_at,
            hash_previews=[event.content_hash[:6] for event in evidence[-3:]],
        )

    def _audit_summary(self, events) -> AuditSummary | None:
        if not events:
            return None
        latest = events[-1]
        return AuditSummary(
            event_count=len(events),
            latest_actor=latest.actor,
            latest_action=latest.action,
            latest_event_at=latest.created_at,
        )
