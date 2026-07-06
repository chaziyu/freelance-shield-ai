import json
from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlmodel import Session, select

from app.models.domain import (
    AgreementStatus,
    AgreementVersion,
    AuditEvent,
    ClientMessage,
    ClientReply,
    InitiatedBy,
    MessageStatus,
    Milestone,
    MilestoneStatus,
    PartyRole,
    Project,
    ProjectStatus,
    RecordedBy,
    ReplyClassification,
    ScopeChangeRequest,
    ScopeChangeStatus,
    SendMode,
    SignatureRecord,
    SignatureStatus,
    utc_now,
)
from app.repositories.domain_repo import DomainRepository


class ValidationError(ValueError):
    pass


class StateTransitionError(ValueError):
    pass


class DomainService:
    def __init__(self, repository: DomainRepository | None = None):
        self.repository = repository or DomainRepository()

    def _audit(
        self,
        session: Session,
        project_id: UUID | None,
        actor: str,
        action: str,
        metadata: dict[str, Any],
    ) -> AuditEvent:
        event = AuditEvent(
            id=uuid4(),
            project_id=project_id,
            actor=actor,
            action=action,
            metadata_json=json.dumps(metadata, sort_keys=True),
            created_at=utc_now(),
        )
        return self.repository.append_audit_event(session, event)

    # --- Project Actions ---

    def create_project(
        self,
        session: Session,
        title: str,
        client_name: str | None,
        source_platform: str,
    ) -> Project:
        project = Project(
            id=uuid4(),
            title=title,
            client_name=client_name,
            source_platform=source_platform,
            status=ProjectStatus.DISCUSSION_CAPTURED,
            automation_enabled=False,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        self.repository.create_project(session, project)
        self._audit(
            session,
            project.id,
            actor="system",
            action="project_created",
            metadata={"title": title, "source_platform": source_platform},
        )
        return project

    # --- Agreement Actions ---

    def create_agreement_draft(
        self,
        session: Session,
        project_id: UUID,
        agreement_code: str,
        scope: str,
        deliverables_json: str,
        revision_limit: int | None = None,
        fee_amount_minor: int | None = None,
        currency: str | None = None,
        payment_terms: str | None = None,
        effective_start_date: date | None = None,
        milestone_plan_json: str | None = None,
    ) -> AgreementVersion:
        project = self.repository.get_project(session, project_id)
        if not project:
            raise ValidationError(f"Project {project_id} not found.")

        # Find next version number
        existing = self.repository.get_agreement_versions(session, project_id)
        version_number = 1 if not existing else existing[-1].version_number + 1

        agreement = AgreementVersion(
            id=uuid4(),
            project_id=project_id,
            agreement_code=agreement_code,
            version_number=version_number,
            scope=scope,
            deliverables_json=deliverables_json,
            revision_limit=revision_limit,
            fee_amount_minor=fee_amount_minor,
            currency=currency,
            payment_terms=payment_terms,
            effective_start_date=effective_start_date,
            milestone_plan_json=milestone_plan_json,
            status=AgreementStatus.DRAFT,
            created_at=utc_now(),
        )
        self.repository.create_agreement_version(session, agreement)

        self._audit(
            session,
            project_id,
            actor="freelancer",
            action="agreement_draft_created",
            metadata={
                "agreement_code": agreement_code,
                "version_number": version_number,
            },
        )
        return agreement

    def transition_to_pending_signature(
        self, session: Session, agreement_id: UUID
    ) -> AgreementVersion:
        agreement = self.repository.get_agreement_version(session, agreement_id)
        if not agreement:
            raise ValidationError(f"Agreement {agreement_id} not found.")

        if agreement.status != AgreementStatus.DRAFT:
            raise StateTransitionError(
                "Agreement must be in DRAFT to transition to "
                f"PENDING_SIGNATURE, got {agreement.status}"
            )

        # Completeness validations
        if agreement.fee_amount_minor is None:
            raise ValidationError(
                "fee_amount_minor is required before requesting signatures."
            )
        if not agreement.currency:
            raise ValidationError("currency is required before requesting signatures.")
        if not agreement.milestone_plan_json:
            raise ValidationError(
                "milestone_plan_json is required before requesting signatures."
            )

        # Verify plan json is a valid list of milestones
        try:
            plan = json.loads(agreement.milestone_plan_json)
            if not isinstance(plan, list) or len(plan) == 0:
                raise ValidationError(
                    "milestone_plan_json must be a non-empty list of milestones."
                )
        except json.JSONDecodeError as exc:
            raise ValidationError(
                "milestone_plan_json is not a valid JSON string."
            ) from exc

        # Set status
        agreement.status = AgreementStatus.PENDING_SIGNATURE
        self.repository.update_agreement_version(session, agreement)

        # Update project status
        project = self.repository.get_project(session, agreement.project_id)
        if project:
            project.status = ProjectStatus.CONTRACT_PENDING_SIGNATURE
            project.updated_at = utc_now()
            self.repository.update_project(session, project)

        # Create SignatureRecords
        freelancer_sig = SignatureRecord(
            id=uuid4(),
            agreement_version_id=agreement_id,
            party_role=PartyRole.freelancer,
            signer_display_name="Freelancer Pending Sign",
            status=SignatureStatus.pending,
            acceptance_text="",
        )
        client_sig = SignatureRecord(
            id=uuid4(),
            agreement_version_id=agreement_id,
            party_role=PartyRole.client,
            signer_display_name="Client Pending Sign",
            status=SignatureStatus.pending,
            acceptance_text="",
        )
        self.repository.create_signature_record(session, freelancer_sig)
        self.repository.create_signature_record(session, client_sig)

        self._audit(
            session,
            agreement.project_id,
            actor="freelancer",
            action="agreement_pending_signature",
            metadata={"agreement_id": str(agreement_id)},
        )
        return agreement

    def record_signature(
        self,
        session: Session,
        agreement_id: UUID,
        party_role: PartyRole,
        signer_display_name: str,
        acceptance_text: str,
    ) -> SignatureRecord:
        agreement = self.repository.get_agreement_version(session, agreement_id)
        if not agreement:
            raise ValidationError(f"Agreement {agreement_id} not found.")

        if agreement.status not in (
            AgreementStatus.PENDING_SIGNATURE,
            AgreementStatus.PARTIALLY_ACCEPTED,
        ):
            raise StateTransitionError(
                f"Agreement is not accepting signatures in status {agreement.status}"
            )

        # Load signatures
        sigs = self.repository.get_signature_records(session, agreement_id)
        target_sig = next((s for s in sigs if s.party_role == party_role), None)
        if not target_sig:
            raise ValidationError(f"No signature record found for role {party_role}.")

        if target_sig.status == SignatureStatus.accepted:
            raise StateTransitionError(
                f"Signature for role {party_role} is already accepted."
            )

        # Update signature
        target_sig.signer_display_name = signer_display_name
        target_sig.acceptance_text = acceptance_text
        target_sig.status = SignatureStatus.accepted
        target_sig.accepted_at = utc_now()
        self.repository.update_signature_record(session, target_sig)

        # Recalculate agreement status
        all_accepted = all(s.status == SignatureStatus.accepted for s in sigs)
        if all_accepted:
            # Mutual acceptance met: Activate agreement
            self._activate_agreement(session, agreement)
        else:
            agreement.status = AgreementStatus.PARTIALLY_ACCEPTED
            self.repository.update_agreement_version(session, agreement)

        self._audit(
            session,
            agreement.project_id,
            actor=str(party_role),
            action="signature_recorded",
            metadata={
                "party_role": str(party_role),
                "signer_name": signer_display_name,
            },
        )
        return target_sig

    def _activate_agreement(
        self, session: Session, agreement: AgreementVersion
    ) -> None:
        project_id = agreement.project_id
        project = self.repository.get_project(session, project_id)
        if not project:
            raise ValidationError("Project not found.")

        # Check that both signatures are accepted
        sigs = self.repository.get_signature_records(session, agreement.id)
        all_accepted = sigs and all(s.status == SignatureStatus.accepted for s in sigs)
        if not all_accepted:
            raise StateTransitionError(
                "Cannot activate contract without accepted "
                "signatures from both parties."
            )

        # Enforcement: Check if project already has another ACTIVE agreement
        # version (excluding the one being superseded)
        active_versions = [
            v
            for v in self.repository.get_agreement_versions(session, project_id)
            if v.status == AgreementStatus.ACTIVE
            and v.id != agreement.id
            and v.id != project.active_agreement_version_id
        ]
        if active_versions:
            raise StateTransitionError(
                "Multiple active agreement versions are not allowed."
            )

        # Check if version > 1 (Supersession)
        previous_active_id = project.active_agreement_version_id
        if previous_active_id:
            # Supersede previous active version
            prev_agreement = self.repository.get_agreement_version(
                session, previous_active_id
            )
            if prev_agreement:
                prev_agreement.status = AgreementStatus.SUPERSEDED
                self.repository.update_agreement_version(session, prev_agreement)

            # Block unfinished milestones of previous version
            milestones = self.repository.get_milestones(session, project_id)
            for milestone in milestones:
                if (
                    milestone.agreement_version_id == previous_active_id
                    and milestone.status != MilestoneStatus.COMPLETED
                ):
                    milestone.status = MilestoneStatus.BLOCKED
                    self.repository.update_milestone(session, milestone)

            # Cancel undelivered messages of previous version
            messages = self.repository.get_client_messages(session, project_id)
            for msg in messages:
                if (
                    msg.agreement_version_id == previous_active_id
                    and msg.status
                    not in (
                        MessageStatus.DELIVERED_TO_DEMO_INBOX,
                        MessageStatus.ACKNOWLEDGED,
                    )
                ):
                    msg.status = MessageStatus.CANCELLED
                    self.repository.update_client_message(session, msg)

        # Activate V2
        agreement.status = AgreementStatus.ACTIVE
        agreement.activated_at = utc_now()
        self.repository.update_agreement_version(session, agreement)

        # Update Project
        project.active_agreement_version_id = agreement.id
        project.status = ProjectStatus.ACTIVE
        project.automation_enabled = True
        project.updated_at = utc_now()
        self.repository.update_project(session, project)

        # Create new milestones
        plan = json.loads(agreement.milestone_plan_json)
        for m_def in plan:
            m = Milestone(
                id=uuid4(),
                project_id=project_id,
                agreement_version_id=agreement.id,
                title=m_def["title"],
                description=m_def.get("description"),
                status=MilestoneStatus.PLANNED,
                due_at=datetime.fromisoformat(m_def["due_at"])
                if m_def.get("due_at")
                else None,
            )
            self.repository.create_milestone(session, m)

        self._audit(
            session,
            project_id,
            actor="system",
            action="agreement_activated",
            metadata={
                "agreement_code": agreement.agreement_code,
                "version_number": agreement.version_number,
            },
        )

    # --- Milestone Actions ---

    def record_milestone_progress(
        self,
        session: Session,
        milestone_id: UUID,
        new_status: MilestoneStatus,
        recorded_by: str,
    ) -> Milestone:
        milestone = self.repository.get_milestone(session, milestone_id)
        if not milestone:
            raise ValidationError(f"Milestone {milestone_id} not found.")

        # recorded_by validation
        if recorded_by not in (RecordedBy.freelancer, RecordedBy.system_demo):
            raise ValidationError(
                f"Invalid recorded_by: {recorded_by}. "
                "AI is not allowed to update progress."
            )

        # Check that agreement controlling milestone is the active one
        project = self.repository.get_project(session, milestone.project_id)
        if (
            not project
            or project.active_agreement_version_id != milestone.agreement_version_id
        ):
            raise StateTransitionError(
                "Can only modify milestones of the active agreement version."
            )

        # State transition validation
        current = milestone.status
        allowed = False
        if current == MilestoneStatus.PLANNED:
            allowed = new_status in (
                MilestoneStatus.IN_PROGRESS,
                MilestoneStatus.BLOCKED,
            )
        elif current == MilestoneStatus.IN_PROGRESS:
            allowed = new_status in (
                MilestoneStatus.READY_FOR_REVIEW,
                MilestoneStatus.BLOCKED,
            )
        elif current == MilestoneStatus.READY_FOR_REVIEW:
            allowed = new_status in (MilestoneStatus.COMPLETED, MilestoneStatus.BLOCKED)
        elif current == MilestoneStatus.BLOCKED:
            allowed = new_status in (
                MilestoneStatus.PLANNED,
                MilestoneStatus.IN_PROGRESS,
            )

        if not allowed:
            raise StateTransitionError(
                f"Transition from {current} to {new_status} is not allowed."
            )

        # Apply progress
        milestone.status = new_status
        milestone.recorded_by = recorded_by
        if new_status == MilestoneStatus.COMPLETED:
            milestone.completion_recorded_at = utc_now()
        self.repository.update_milestone(session, milestone)

        self._audit(
            session,
            milestone.project_id,
            actor=recorded_by,
            action="milestone_progress_recorded",
            metadata={"milestone_id": str(milestone_id), "new_status": str(new_status)},
        )
        return milestone

    # --- Scope Change Actions ---

    def detect_scope_change(
        self,
        session: Session,
        project_id: UUID,
        source_reply_id: UUID | None,
        summary: str,
        initiated_by: str,
        affected_milestone_ids: list[UUID],
    ) -> ScopeChangeRequest:
        project = self.repository.get_project(session, project_id)
        if not project:
            raise ValidationError(f"Project {project_id} not found.")

        if initiated_by not in (InitiatedBy.freelancer, InitiatedBy.client):
            raise ValidationError(f"Invalid scope change initiator: {initiated_by}")

        # Transition project state to SCOPE_CHANGE_PENDING and pause automation
        project.status = ProjectStatus.SCOPE_CHANGE_PENDING
        project.automation_enabled = False
        project.updated_at = utc_now()
        self.repository.update_project(session, project)

        request = ScopeChangeRequest(
            id=uuid4(),
            project_id=project_id,
            source_reply_id=source_reply_id,
            summary=summary,
            status=ScopeChangeStatus.detected,
            proposed_contract_version_id=None,
            affected_milestone_ids_json=json.dumps(
                [str(mid) for mid in affected_milestone_ids]
            ),
            initiated_by=initiated_by,
            created_at=utc_now(),
        )
        self.repository.create_scope_change_request(session, request)

        self._audit(
            session,
            project_id,
            actor=initiated_by,
            action="scope_change_detected",
            metadata={"summary": summary[:100]},
        )
        return request

    def process_scope_change_decision(
        self, session: Session, request_id: UUID, decision: ScopeChangeStatus
    ) -> ScopeChangeRequest:
        statement = select(ScopeChangeRequest).where(
            ScopeChangeRequest.id == request_id
        )
        request = session.exec(statement).first()
        if not request:
            raise ValidationError(f"ScopeChangeRequest {request_id} not found.")

        if request.status != ScopeChangeStatus.detected:
            raise StateTransitionError(
                f"Decision is not allowed on scope change with status {request.status}"
            )

        if decision not in (ScopeChangeStatus.accepted, ScopeChangeStatus.rejected):
            raise ValidationError(f"Invalid scope change decision status: {decision}")

        request.status = decision
        self.repository.update_scope_change_request(session, request)

        project = self.repository.get_project(session, request.project_id)
        if not project:
            raise ValidationError("Project not found.")

        if decision == ScopeChangeStatus.rejected:
            # Resume automation and active contract workflow
            project.status = ProjectStatus.ACTIVE
            project.automation_enabled = True
            project.updated_at = utc_now()
            self.repository.update_project(session, project)

        self._audit(
            session,
            request.project_id,
            actor="freelancer",
            action="scope_change_processed",
            metadata={"request_id": str(request_id), "decision": str(decision)},
        )
        return request

    # --- Client Messaging Actions ---

    def queue_client_message(
        self,
        session: Session,
        project_id: UUID,
        agreement_version_id: UUID,
        message_type: str,
        body: str,
        send_mode: SendMode,
        idempotency_key: str,
        milestone_id: UUID | None = None,
    ) -> ClientMessage:
        project = self.repository.get_project(session, project_id)
        if not project:
            raise ValidationError(f"Project {project_id} not found.")

        agreement = self.repository.get_agreement_version(session, agreement_version_id)
        if not agreement or agreement.status != AgreementStatus.ACTIVE:
            raise ValidationError("Messages must refer to an ACTIVE contract version.")

        if send_mode not in (SendMode.routine_auto, SendMode.approval_required):
            raise ValidationError(f"Invalid message send_mode: {send_mode}")

        # Unique idempotency_key verification
        # The database unique constraint will fail, but check at app level first
        statement = select(ClientMessage).where(
            ClientMessage.idempotency_key == idempotency_key
        )
        existing = session.exec(statement).first()
        if existing:
            raise ValidationError("Duplicate idempotency key rejected.")

        status = (
            MessageStatus.QUEUED
            if send_mode == SendMode.routine_auto
            else MessageStatus.APPROVAL_REQUIRED
        )

        message = ClientMessage(
            id=uuid4(),
            project_id=project_id,
            agreement_version_id=agreement_version_id,
            milestone_id=milestone_id,
            message_type=message_type,
            body=body,
            send_mode=send_mode,
            status=status,
            idempotency_key=idempotency_key,
        )
        self.repository.create_client_message(session, message)

        self._audit(
            session,
            project_id,
            actor="system",
            action="client_message_queued",
            metadata={"message_type": message_type, "status": str(status)},
        )
        return message

    def deliver_message_to_demo_inbox(
        self, session: Session, message_id: UUID
    ) -> ClientMessage:
        message = self.repository.get_client_message(session, message_id)
        if not message:
            raise ValidationError(f"Message {message_id} not found.")

        # Verification: V1 messages cannot be delivered after V2 activates
        project = self.repository.get_project(session, message.project_id)
        if not project:
            raise ValidationError("Project not found.")

        if project.active_agreement_version_id != message.agreement_version_id:
            raise StateTransitionError(
                "Cannot deliver message for an inactive agreement version."
            )

        # Verification: project must not be paused or in scope change pending
        if (
            project.status == ProjectStatus.SCOPE_CHANGE_PENDING
            or not project.automation_enabled
        ):
            raise StateTransitionError(
                "Cannot deliver message while automation is disabled "
                "or scope change is pending."
            )

        if message.status not in (MessageStatus.QUEUED, MessageStatus.APPROVED):
            raise StateTransitionError(
                f"Cannot deliver message in status {message.status}"
            )

        message.status = MessageStatus.DELIVERED_TO_DEMO_INBOX
        message.delivered_at = utc_now()
        self.repository.update_client_message(session, message)

        self._audit(
            session,
            message.project_id,
            actor="system",
            action="client_message_delivered",
            metadata={"message_id": str(message_id)},
        )
        return message

    def record_client_reply(
        self,
        session: Session,
        project_id: UUID,
        client_message_id: UUID | None,
        body: str,
        classification: ReplyClassification,
        possible_scope_change: bool,
    ) -> ClientReply:
        project = self.repository.get_project(session, project_id)
        if not project:
            raise ValidationError(f"Project {project_id} not found.")

        if client_message_id:
            msg = self.repository.get_client_message(session, client_message_id)
            if not msg:
                raise ValidationError("Referenced message not found.")

        reply = ClientReply(
            id=uuid4(),
            project_id=project_id,
            client_message_id=client_message_id,
            body=body,
            classification=classification,
            possible_scope_change=possible_scope_change,
            received_at=utc_now(),
        )
        self.repository.create_client_reply(session, reply)

        # Automatic scope change detection
        if possible_scope_change or classification == ReplyClassification.SCOPE_CHANGE:
            # Auto trigger detect_scope_change
            self.detect_scope_change(
                session,
                project_id=project_id,
                source_reply_id=reply.id,
                summary=f"Reply scope change: {body[:100]}",
                initiated_by=InitiatedBy.client,
                affected_milestone_ids=[],
            )

        self._audit(
            session,
            project_id,
            actor="client",
            action="client_reply_recorded",
            metadata={
                "classification": str(classification),
                "possible_scope_change": possible_scope_change,
            },
        )
        return reply
