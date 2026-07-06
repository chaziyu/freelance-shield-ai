import json
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import Session, SQLModel, create_engine, delete, update

from app.models.domain import (
    AgreementStatus,
    AuditEvent,
    InitiatedBy,
    MessageStatus,
    MilestoneStatus,
    PartyRole,
    ProjectStatus,
    ReplyClassification,
    SendMode,
)
from app.services.domain_service import (
    DomainService,
    StateTransitionError,
    ValidationError,
)


@pytest.fixture
def session() -> Session:
    # Use a fresh in-memory SQLite database for tests
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, echo=False
    )
    SQLModel.metadata.create_all(engine)

    # Apply the trigger SQL definitions
    with engine.connect() as connection:
        connection.execute(
            text("""
            CREATE TRIGGER prevent_audit_update
            BEFORE UPDATE ON audit_events
            BEGIN
                SELECT RAISE(ABORT, 'Updates on audit_events are not allowed');
            END;
        """)
        )
        connection.execute(
            text("""
            CREATE TRIGGER prevent_audit_delete
            BEFORE DELETE ON audit_events
            BEGIN
                SELECT RAISE(ABORT, 'Deletions on audit_events are not allowed');
            END;
        """)
        )
        connection.commit()

    with Session(engine) as session:
        yield session


@pytest.fixture
def service() -> DomainService:
    return DomainService()


# --- Helper to create a complete project/agreement version setup ---
def setup_draft_agreement(session: Session, service: DomainService):
    project = service.create_project(
        session,
        title="Poster design",
        client_name="Demo Client",
        source_platform="Instagram",
    )
    plan_json = json.dumps(
        [
            {
                "title": "First draft",
                "description": "Draft details",
                "due_at": "2026-07-10T12:00:00",
            },
            {
                "title": "Final files",
                "description": "Final assets",
                "due_at": "2026-07-15T12:00:00",
            },
        ]
    )
    agreement = service.create_agreement_draft(
        session,
        project_id=project.id,
        agreement_code="FS-001",
        scope="Design a promotional poster",
        deliverables_json=json.dumps(["First draft", "Final files"]),
        revision_limit=2,
        fee_amount_minor=80000,  # RM800.00
        currency="MYR",
        payment_terms="Payment due after invoice",
        effective_start_date=date(2026, 7, 7),
        milestone_plan_json=plan_json,
    )
    return project, agreement


def test_contract_cannot_activate_before_both_signatures(
    session: Session, service: DomainService
):
    project, agreement = setup_draft_agreement(session, service)

    # 1. Move to PENDING_SIGNATURE
    service.transition_to_pending_signature(session, agreement.id)
    session.refresh(agreement)
    assert agreement.status == AgreementStatus.PENDING_SIGNATURE

    # 2. freelancer signs
    service.record_signature(
        session,
        agreement_id=agreement.id,
        party_role=PartyRole.freelancer,
        signer_display_name="Demo Freelancer",
        acceptance_text="I agree to Version 1",
    )

    session.refresh(agreement)
    # Status should be PARTIALLY_ACCEPTED, NOT active yet
    assert agreement.status == AgreementStatus.PARTIALLY_ACCEPTED
    assert project.active_agreement_version_id is None


def test_contract_activates_after_both_valid_signatures(
    session: Session, service: DomainService
):
    project, agreement = setup_draft_agreement(session, service)

    service.transition_to_pending_signature(session, agreement.id)

    # Both parties sign
    service.record_signature(
        session,
        agreement_id=agreement.id,
        party_role=PartyRole.freelancer,
        signer_display_name="Demo Freelancer",
        acceptance_text="I agree to Version 1",
    )
    service.record_signature(
        session,
        agreement_id=agreement.id,
        party_role=PartyRole.client,
        signer_display_name="Demo Client",
        acceptance_text="I agree to Version 1",
    )

    session.refresh(agreement)
    session.refresh(project)

    # Verify ACTIVE states and values
    assert agreement.status == AgreementStatus.ACTIVE
    assert project.status == ProjectStatus.ACTIVE
    assert project.active_agreement_version_id == agreement.id
    assert project.automation_enabled is True

    # Milestones should be created from the plan
    milestones = service.repository.get_milestones(session, project.id)
    assert len(milestones) == 2
    assert milestones[0].title == "First draft"
    assert milestones[1].title == "Final files"


def test_milestone_creation_fails_for_inactive_contract(
    session: Session, service: DomainService
):
    # Try to create milestones for a draft agreement directly
    project, agreement = setup_draft_agreement(session, service)

    with pytest.raises(StateTransitionError):
        # Triggering _activate_agreement directly without signatures
        service._activate_agreement(session, agreement)


def test_v2_does_not_supersede_v1_before_both_v2_signatures(
    session: Session, service: DomainService
):
    # Setup and activate V1
    project, agreement_v1 = setup_draft_agreement(session, service)
    service.transition_to_pending_signature(session, agreement_v1.id)
    service.record_signature(
        session, agreement_v1.id, PartyRole.freelancer, "F1", "Accept V1"
    )
    service.record_signature(
        session, agreement_v1.id, PartyRole.client, "C1", "Accept V1"
    )

    session.refresh(project)
    assert project.active_agreement_version_id == agreement_v1.id

    # Create V2 draft
    plan_json2 = json.dumps(
        [
            {"title": "First draft", "due_at": "2026-07-10T12:00:00"},
            {"title": "Final files", "due_at": "2026-07-15T12:00:00"},
            {"title": "Instagram story version", "due_at": "2026-07-18T12:00:00"},
        ]
    )
    agreement_v2 = service.create_agreement_draft(
        session,
        project_id=project.id,
        agreement_code="FS-001",
        scope="Design poster + story",
        deliverables_json=json.dumps(["First draft", "Final files", "Story files"]),
        revision_limit=2,
        fee_amount_minor=90000,
        currency="MYR",
        milestone_plan_json=plan_json2,
    )

    service.transition_to_pending_signature(session, agreement_v2.id)

    # Freelancer signs V2
    service.record_signature(
        session, agreement_v2.id, PartyRole.freelancer, "F1", "Accept V2"
    )

    session.refresh(agreement_v1)
    session.refresh(agreement_v2)
    session.refresh(project)

    # Agreement V1 should still be ACTIVE, V2 partially accepted
    assert agreement_v1.status == AgreementStatus.ACTIVE
    assert agreement_v2.status == AgreementStatus.PARTIALLY_ACCEPTED
    assert project.active_agreement_version_id == agreement_v1.id


def test_scope_change_pauses_automation(session: Session, service: DomainService):
    project, agreement = setup_draft_agreement(session, service)
    service.transition_to_pending_signature(session, agreement.id)
    service.record_signature(
        session, agreement.id, PartyRole.freelancer, "F1", "Accept V1"
    )
    service.record_signature(session, agreement.id, PartyRole.client, "C1", "Accept V1")

    session.refresh(project)
    assert project.automation_enabled is True
    assert project.status == ProjectStatus.ACTIVE

    # Trigger scope change detection
    service.detect_scope_change(
        session,
        project_id=project.id,
        source_reply_id=None,
        summary="Manual scope addition",
        initiated_by=InitiatedBy.freelancer,
        affected_milestone_ids=[],
    )

    session.refresh(project)
    # Automation should be paused, status updated to SCOPE_CHANGE_PENDING
    assert project.status == ProjectStatus.SCOPE_CHANGE_PENDING
    assert project.automation_enabled is False


def test_automation_requires_latest_active_contract(
    session: Session, service: DomainService
):
    # Setup V1 active
    project, agreement_v1 = setup_draft_agreement(session, service)
    service.transition_to_pending_signature(session, agreement_v1.id)
    service.record_signature(
        session, agreement_v1.id, PartyRole.freelancer, "F1", "Accept V1"
    )
    service.record_signature(
        session, agreement_v1.id, PartyRole.client, "C1", "Accept V1"
    )

    # Queue message for V1
    msg_v1 = service.queue_client_message(
        session,
        project_id=project.id,
        agreement_version_id=agreement_v1.id,
        message_type="KICKOFF_CONFIRMATION",
        body="Kickoff text",
        send_mode=SendMode.routine_auto,
        idempotency_key="key1",
    )

    # Deliver V1 message
    service.deliver_message_to_demo_inbox(session, msg_v1.id)
    session.refresh(msg_v1)
    assert msg_v1.status == MessageStatus.DELIVERED_TO_DEMO_INBOX

    # Activate V2
    plan_json2 = json.dumps([{"title": "First draft", "due_at": "2026-07-10T12:00:00"}])
    agreement_v2 = service.create_agreement_draft(
        session,
        project_id=project.id,
        agreement_code="FS-001",
        scope="Design poster + story",
        deliverables_json=json.dumps(["First draft"]),
        revision_limit=2,
        fee_amount_minor=90000,
        currency="MYR",
        milestone_plan_json=plan_json2,
    )
    service.transition_to_pending_signature(session, agreement_v2.id)
    service.record_signature(
        session, agreement_v2.id, PartyRole.freelancer, "F1", "Accept V2"
    )
    service.record_signature(
        session, agreement_v2.id, PartyRole.client, "C1", "Accept V2"
    )

    session.refresh(project)
    assert project.active_agreement_version_id == agreement_v2.id

    # Queue new message for V1 - should fail because V1 is no longer active
    with pytest.raises(ValidationError):
        service.queue_client_message(
            session,
            project_id=project.id,
            agreement_version_id=agreement_v1.id,
            message_type="DELIVERY_CONFIRMATION",
            body="First draft delivered",
            send_mode=SendMode.routine_auto,
            idempotency_key="key2",
        )


def test_milestone_completion_requires_recorded_actor(
    session: Session, service: DomainService
):
    project, agreement = setup_draft_agreement(session, service)
    service.transition_to_pending_signature(session, agreement.id)
    service.record_signature(
        session, agreement.id, PartyRole.freelancer, "F1", "Accept V1"
    )
    service.record_signature(session, agreement.id, PartyRole.client, "C1", "Accept V1")

    milestones = service.repository.get_milestones(session, project.id)
    mid = milestones[0].id

    # Acceptable recorded_by
    service.record_milestone_progress(
        session, mid, MilestoneStatus.IN_PROGRESS, "freelancer"
    )
    milestone = service.repository.get_milestone(session, mid)
    assert milestone.status == MilestoneStatus.IN_PROGRESS

    # Reject AI recorded_by
    with pytest.raises(ValidationError):
        service.record_milestone_progress(
            session, mid, MilestoneStatus.READY_FOR_REVIEW, "ai"
        )


def test_duplicate_message_idempotency_key_is_rejected(
    session: Session, service: DomainService
):
    project, agreement = setup_draft_agreement(session, service)
    service.transition_to_pending_signature(session, agreement.id)
    service.record_signature(
        session, agreement.id, PartyRole.freelancer, "F1", "Accept V1"
    )
    service.record_signature(session, agreement.id, PartyRole.client, "C1", "Accept V1")

    # Queue first message
    service.queue_client_message(
        session,
        project_id=project.id,
        agreement_version_id=agreement.id,
        message_type="KICKOFF_CONFIRMATION",
        body="Kickoff text",
        send_mode=SendMode.routine_auto,
        idempotency_key="unique_key_123",
    )

    # Queue second message with same idempotency key
    with pytest.raises(ValidationError):
        service.queue_client_message(
            session,
            project_id=project.id,
            agreement_version_id=agreement.id,
            message_type="KICKOFF_CONFIRMATION",
            body="Kickoff text 2",
            send_mode=SendMode.routine_auto,
            idempotency_key="unique_key_123",
        )


def test_audit_records_are_append_only(session: Session, service: DomainService):
    project = service.create_project(session, "Title", None, "Instagram")
    session.commit()

    audits = service.repository.get_audit_events(session, project.id)
    assert len(audits) == 1
    audit_id = audits[0].id

    # Attempting to delete or update on the audit event should fail due to triggers
    with pytest.raises((OperationalError, IntegrityError)):
        session.execute(delete(AuditEvent).where(AuditEvent.id == audit_id))
        session.commit()
    session.rollback()

    with pytest.raises((OperationalError, IntegrityError)):
        session.execute(
            update(AuditEvent).where(AuditEvent.id == audit_id).values(actor="hacked")
        )
        session.commit()
    session.rollback()


def test_every_domain_write_produces_audit_event(
    session: Session, service: DomainService
):
    project, agreement = setup_draft_agreement(session, service)
    # Audits recorded so far:
    # 1. Project creation
    # 2. Agreement draft creation
    audits = service.repository.get_audit_events(session, project.id)
    assert len(audits) == 2
    assert audits[0].action == "project_created"
    assert audits[1].action == "agreement_draft_created"

    # Transition to pending signature
    service.transition_to_pending_signature(session, agreement.id)
    audits = service.repository.get_audit_events(session, project.id)
    assert len(audits) == 3
    assert audits[2].action == "agreement_pending_signature"


def test_one_active_agreement_enforcement(session: Session, service: DomainService):
    # Setup V1 active
    project, agreement_v1 = setup_draft_agreement(session, service)
    service.transition_to_pending_signature(session, agreement_v1.id)
    service.record_signature(
        session, agreement_v1.id, PartyRole.freelancer, "F1", "Accept V1"
    )
    service.record_signature(
        session, agreement_v1.id, PartyRole.client, "C1", "Accept V1"
    )

    # Setup V2 draft and signatures
    plan_json2 = json.dumps([{"title": "First draft", "due_at": "2026-07-10T12:00:00"}])
    agreement_v2 = service.create_agreement_draft(
        session,
        project_id=project.id,
        agreement_code="FS-001",
        scope="Design poster + story",
        deliverables_json=json.dumps(["First draft"]),
        revision_limit=2,
        fee_amount_minor=90000,
        currency="MYR",
        milestone_plan_json=plan_json2,
    )
    service.transition_to_pending_signature(session, agreement_v2.id)

    # Bypass activation checks to test the index trigger constraint
    agreement_v2.status = AgreementStatus.ACTIVE
    session.add(agreement_v2)

    with pytest.raises((OperationalError, IntegrityError)):
        session.commit()


def test_v1_message_cancellation_after_v2_activation(
    session: Session, service: DomainService
):
    # Setup V1 active
    project, agreement_v1 = setup_draft_agreement(session, service)
    service.transition_to_pending_signature(session, agreement_v1.id)
    service.record_signature(
        session, agreement_v1.id, PartyRole.freelancer, "F1", "Accept V1"
    )
    service.record_signature(
        session, agreement_v1.id, PartyRole.client, "C1", "Accept V1"
    )

    # Queue message for V1 (undelivered status is QUEUED)
    msg_v1 = service.queue_client_message(
        session,
        project_id=project.id,
        agreement_version_id=agreement_v1.id,
        message_type="KICKOFF_CONFIRMATION",
        body="Kickoff text V1",
        send_mode=SendMode.routine_auto,
        idempotency_key="key_v1",
    )

    # Setup and activate V2
    plan_json2 = json.dumps([{"title": "First draft", "due_at": "2026-07-10T12:00:00"}])
    agreement_v2 = service.create_agreement_draft(
        session,
        project_id=project.id,
        agreement_code="FS-001",
        scope="V2 Scope",
        deliverables_json=json.dumps(["First draft"]),
        revision_limit=2,
        fee_amount_minor=90000,
        currency="MYR",
        milestone_plan_json=plan_json2,
    )
    service.transition_to_pending_signature(session, agreement_v2.id)
    service.record_signature(
        session, agreement_v2.id, PartyRole.freelancer, "F1", "Accept V2"
    )
    service.record_signature(
        session, agreement_v2.id, PartyRole.client, "C1", "Accept V2"
    )

    session.refresh(msg_v1)
    # The message for V1 must be cancelled automatically upon V2 activation
    assert msg_v1.status == MessageStatus.CANCELLED


def test_delivered_message_history_preservation(
    session: Session, service: DomainService
):
    # Setup V1 active
    project, agreement_v1 = setup_draft_agreement(session, service)
    service.transition_to_pending_signature(session, agreement_v1.id)
    service.record_signature(
        session, agreement_v1.id, PartyRole.freelancer, "F1", "Accept V1"
    )
    service.record_signature(
        session, agreement_v1.id, PartyRole.client, "C1", "Accept V1"
    )

    # Queue and deliver message for V1
    msg_v1 = service.queue_client_message(
        session,
        project_id=project.id,
        agreement_version_id=agreement_v1.id,
        message_type="KICKOFF_CONFIRMATION",
        body="Kickoff text V1",
        send_mode=SendMode.routine_auto,
        idempotency_key="key_v1",
    )
    service.deliver_message_to_demo_inbox(session, msg_v1.id)

    # Setup and activate V2
    plan_json2 = json.dumps([{"title": "First draft", "due_at": "2026-07-10T12:00:00"}])
    agreement_v2 = service.create_agreement_draft(
        session,
        project_id=project.id,
        agreement_code="FS-001",
        scope="V2 Scope",
        deliverables_json=json.dumps(["First draft"]),
        revision_limit=2,
        fee_amount_minor=90000,
        currency="MYR",
        milestone_plan_json=plan_json2,
    )
    service.transition_to_pending_signature(session, agreement_v2.id)
    service.record_signature(
        session, agreement_v2.id, PartyRole.freelancer, "F1", "Accept V2"
    )
    service.record_signature(
        session, agreement_v2.id, PartyRole.client, "C1", "Accept V2"
    )

    session.refresh(msg_v1)
    # Delivered message history is preserved (still DELIVERED_TO_DEMO_INBOX)
    assert msg_v1.status == MessageStatus.DELIVERED_TO_DEMO_INBOX


def test_unsolicited_replies(session: Session, service: DomainService):
    project, agreement = setup_draft_agreement(session, service)
    service.transition_to_pending_signature(session, agreement.id)
    service.record_signature(
        session, agreement.id, PartyRole.freelancer, "F1", "Accept V1"
    )
    service.record_signature(session, agreement.id, PartyRole.client, "C1", "Accept V1")

    # Record client reply with null message id (unsolicited)
    reply = service.record_client_reply(
        session,
        project_id=project.id,
        client_message_id=None,
        body="I have a question about the project start date.",
        classification=ReplyClassification.QUESTION,
        possible_scope_change=False,
    )

    assert reply.client_message_id is None
    assert reply.classification == ReplyClassification.QUESTION


def test_contract_completeness_before_signature(
    session: Session, service: DomainService
):
    project = service.create_project(
        session, "Poster design", "Demo Client", "Instagram"
    )

    # Draft with missing fee_amount_minor, currency, milestone_plan_json
    agreement = service.create_agreement_draft(
        session,
        project_id=project.id,
        agreement_code="FS-001",
        scope="Scope text",
        deliverables_json=json.dumps(["Item 1"]),
    )

    # Attempting to move to PENDING_SIGNATURE should fail
    with pytest.raises(ValidationError):
        service.transition_to_pending_signature(session, agreement.id)

    # Set fee, but missing currency/plan
    agreement.fee_amount_minor = 80000
    session.add(agreement)
    session.commit()

    with pytest.raises(ValidationError):
        service.transition_to_pending_signature(session, agreement.id)

    # Set currency, missing plan
    agreement.currency = "MYR"
    session.add(agreement)
    session.commit()

    with pytest.raises(ValidationError):
        service.transition_to_pending_signature(session, agreement.id)

    # Set invalid plan
    agreement.milestone_plan_json = "invalid_json"
    session.add(agreement)
    session.commit()

    with pytest.raises(ValidationError):
        service.transition_to_pending_signature(session, agreement.id)

    # Set valid plan - now it succeeds
    plan_json = json.dumps([{"title": "First draft", "due_at": "2026-07-10T12:00:00"}])
    agreement.milestone_plan_json = plan_json
    session.add(agreement)
    session.commit()

    service.transition_to_pending_signature(session, agreement.id)
    session.refresh(agreement)
    assert agreement.status == AgreementStatus.PENDING_SIGNATURE


def test_invalid_enum_status_rejection(session: Session, service: DomainService):
    project, agreement = setup_draft_agreement(session, service)

    # Try setting invalid project status in database direct write
    project.status = "INVALID_STATUS"
    session.add(project)

    with pytest.raises((OperationalError, IntegrityError)):
        session.commit()
