from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    AgreementVersion,
    AuditEvent,
    ClientMessage,
    ClientReply,
    Milestone,
    Project,
    ScopeChangeRequest,
    SignatureRecord,
)


class DomainRepository:
    # --- Project Operations ---

    def create_project(self, session: Session, project: Project) -> Project:
        session.add(project)
        session.flush()
        return project

    def get_project(self, session: Session, project_id: UUID) -> Project | None:
        return session.get(Project, project_id)

    def update_project(self, session: Session, project: Project) -> Project:
        session.add(project)
        session.flush()
        return project

    # --- AgreementVersion Operations ---

    def create_agreement_version(
        self, session: Session, agreement: AgreementVersion
    ) -> AgreementVersion:
        session.add(agreement)
        session.flush()
        return agreement

    def get_agreement_version(
        self, session: Session, agreement_id: UUID
    ) -> AgreementVersion | None:
        return session.get(AgreementVersion, agreement_id)

    def get_agreement_versions(
        self, session: Session, project_id: UUID
    ) -> list[AgreementVersion]:
        statement = (
            select(AgreementVersion)
            .where(AgreementVersion.project_id == project_id)
            .order_by(AgreementVersion.version_number.asc())
        )
        return list(session.exec(statement).all())

    def update_agreement_version(
        self, session: Session, agreement: AgreementVersion
    ) -> AgreementVersion:
        session.add(agreement)
        session.flush()
        return agreement

    # --- SignatureRecord Operations ---

    def create_signature_record(
        self, session: Session, signature: SignatureRecord
    ) -> SignatureRecord:
        session.add(signature)
        session.flush()
        return signature

    def get_signature_records(
        self, session: Session, agreement_version_id: UUID
    ) -> list[SignatureRecord]:
        statement = select(SignatureRecord).where(
            SignatureRecord.agreement_version_id == agreement_version_id
        )
        return list(session.exec(statement).all())

    def update_signature_record(
        self, session: Session, signature: SignatureRecord
    ) -> SignatureRecord:
        session.add(signature)
        session.flush()
        return signature

    # --- Milestone Operations ---

    def create_milestone(self, session: Session, milestone: Milestone) -> Milestone:
        session.add(milestone)
        session.flush()
        return milestone

    def get_milestone(self, session: Session, milestone_id: UUID) -> Milestone | None:
        return session.get(Milestone, milestone_id)

    def get_milestones(self, session: Session, project_id: UUID) -> list[Milestone]:
        statement = select(Milestone).where(Milestone.project_id == project_id)
        return list(session.exec(statement).all())

    def update_milestone(self, session: Session, milestone: Milestone) -> Milestone:
        session.add(milestone)
        session.flush()
        return milestone

    # --- ClientMessage Operations ---

    def create_client_message(
        self, session: Session, message: ClientMessage
    ) -> ClientMessage:
        session.add(message)
        session.flush()
        return message

    def get_client_message(
        self, session: Session, message_id: UUID
    ) -> ClientMessage | None:
        return session.get(ClientMessage, message_id)

    def get_client_messages(
        self, session: Session, project_id: UUID
    ) -> list[ClientMessage]:
        statement = select(ClientMessage).where(ClientMessage.project_id == project_id)
        return list(session.exec(statement).all())

    def update_client_message(
        self, session: Session, message: ClientMessage
    ) -> ClientMessage:
        session.add(message)
        session.flush()
        return message

    # --- ClientReply Operations ---

    def create_client_reply(self, session: Session, reply: ClientReply) -> ClientReply:
        session.add(reply)
        session.flush()
        return reply

    def get_client_replies(
        self, session: Session, project_id: UUID
    ) -> list[ClientReply]:
        statement = select(ClientReply).where(ClientReply.project_id == project_id)
        return list(session.exec(statement).all())

    # --- ScopeChangeRequest Operations ---

    def create_scope_change_request(
        self, session: Session, request: ScopeChangeRequest
    ) -> ScopeChangeRequest:
        session.add(request)
        session.flush()
        return request

    def get_scope_change_requests(
        self, session: Session, project_id: UUID
    ) -> list[ScopeChangeRequest]:
        statement = select(ScopeChangeRequest).where(
            ScopeChangeRequest.project_id == project_id
        )
        return list(session.exec(statement).all())

    def update_scope_change_request(
        self, session: Session, request: ScopeChangeRequest
    ) -> ScopeChangeRequest:
        session.add(request)
        session.flush()
        return request

    # --- AuditEvent Operations (Strictly Append-Only) ---

    def append_audit_event(self, session: Session, event: AuditEvent) -> AuditEvent:
        # Simply add and flush, no recursion or updates allowed
        session.add(event)
        session.flush()
        return event

    def get_audit_events(self, session: Session, project_id: UUID) -> list[AuditEvent]:
        statement = (
            select(AuditEvent)
            .where(AuditEvent.project_id == project_id)
            .order_by(AuditEvent.created_at.asc())
        )
        return list(session.exec(statement).all())
