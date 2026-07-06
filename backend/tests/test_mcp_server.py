import hashlib
import json
import os
import sys
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.domain import (
    AgreementStatus,
    AuditEvent,
    DiscussionFactSnapshot,
    MessageStatus,
    Milestone,
    MilestoneStatus,
    PartyRole,
    ProjectStatus,
    ReplyClassification,
)
from app.services.domain_service import (
    DomainService,
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


# --- Test Migration and Persistence ---


def test_migration_and_columns_exist(session):
    # Verify discussion_fact_snapshots table exists and has the correct columns
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    assert "discussion_fact_snapshots" in tables

    columns = [
        col["name"] for col in inspector.get_columns("discussion_fact_snapshots")
    ]
    assert "id" in columns
    assert "project_id" in columns
    assert "extracted_facts_json" in columns
    assert "missing_fields_json" in columns
    assert "risk_flags_json" in columns
    assert "source_text_hash" in columns
    assert "created_at" in columns

    # Verify milestones table has source_plan_item_key column
    m_columns = [col["name"] for col in inspector.get_columns("milestones")]
    assert "source_plan_item_key" in m_columns


def test_audit_triggers_block_update_delete(session):
    event = AuditEvent(
        id=uuid4(),
        project_id=None,
        actor="system",
        action="test_action",
        metadata_json="{}",
    )
    session.add(event)
    session.commit()

    # Try updating
    event.action = "changed"
    session.add(event)
    with pytest.raises(SQLAlchemyError) as exc:
        session.commit()
    assert "Updates on audit_events are not allowed" in str(exc.value)
    session.rollback()

    # Try deleting
    with pytest.raises(SQLAlchemyError) as exc:
        session.delete(event)
        session.commit()
    assert "Deletions on audit_events are not allowed" in str(exc.value)
    session.rollback()


def test_milestone_unique_constraints(session):
    proj_id = uuid4()
    ag_id = uuid4()

    # Multiple manual milestones with NULL source_plan_item_key are allowed
    m1 = Milestone(
        id=uuid4(),
        project_id=proj_id,
        agreement_version_id=ag_id,
        title="Manual 1",
        status=MilestoneStatus.PLANNED,
        source_plan_item_key=None,
    )
    m2 = Milestone(
        id=uuid4(),
        project_id=proj_id,
        agreement_version_id=ag_id,
        title="Manual 2",
        status=MilestoneStatus.PLANNED,
        source_plan_item_key=None,
    )
    session.add(m1)
    session.add(m2)
    session.commit()

    # Duplicate non-null keys for the same agreement version must be rejected
    m3 = Milestone(
        id=uuid4(),
        project_id=proj_id,
        agreement_version_id=ag_id,
        title="Plan Item 1",
        status=MilestoneStatus.PLANNED,
        source_plan_item_key="item_key_1",
    )
    m4 = Milestone(
        id=uuid4(),
        project_id=proj_id,
        agreement_version_id=ag_id,
        title="Plan Item 2",
        status=MilestoneStatus.PLANNED,
        source_plan_item_key="item_key_1",
    )
    session.add(m3)
    session.commit()

    session.add(m4)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_create_milestones_from_contract_idempotency(session, service):
    project = service.create_project(session, "Proj", None, "Instagram")
    plan_json = json.dumps(
        [
            {
                "source_plan_item_key": "k1",
                "title": "Milestone 1",
                "due_at": "2026-07-10T12:00:00",
            },
            {
                "source_plan_item_key": "k2",
                "title": "Milestone 2",
                "due_at": "2026-07-15T12:00:00",
            },
        ]
    )
    agreement = service.create_agreement_draft(
        session,
        project.id,
        "FS-001",
        "Scope",
        json.dumps(["Deliv"]),
        1,
        1000,
        "USD",
        "Net 30",
        None,
        plan_json,
    )

    service.transition_to_pending_signature(session, agreement.id)
    service.record_signature(
        session, agreement.id, PartyRole.freelancer, "F1", "Accept"
    )
    service.record_signature(session, agreement.id, PartyRole.client, "C1", "Accept")

    session.refresh(agreement)
    assert agreement.status == AgreementStatus.ACTIVE

    m_list1 = service.repository.get_milestones(session, project.id)
    assert len(m_list1) == 2

    # Repeat call should not duplicate
    m_list2 = service.create_milestones_from_contract(session, project.id, agreement.id)
    assert len(m_list2) == 2

    # No duplicate milestones in db
    m_db = session.exec(select(Milestone)).all()
    assert len(m_db) == 2


def test_save_discussion_facts_persists_hash_no_chat_text(session, service):
    project = service.create_project(session, "Proj", None, "Instagram")
    raw_chat = "Let's make a banner for USD1000. Revisions limit 3."
    snapshot = service.save_discussion_facts(
        session=session,
        project_id=project.id,
        extracted_facts={"fee": 1000, "revision_limit": 3},
        missing_fields=["deadline"],
        risk_flags=[],
        raw_input=raw_chat,
    )
    session.commit()

    snap = session.get(DiscussionFactSnapshot, snapshot.id)
    assert snap is not None
    assert raw_chat not in snap.extracted_facts_json
    assert snap.source_text_hash == hashlib.sha256(raw_chat.encode("utf-8")).hexdigest()

    audits = service.repository.get_audit_events(session, project.id)
    fact_audit = next(a for a in audits if a.action == "discussion_facts_saved")
    assert fact_audit.actor == "discussion_agent"
    assert raw_chat not in fact_audit.metadata_json


# --- Test Registry and Authority ---


def test_mcp_registry_rules():
    from app.mcp_server.server import mcp

    tools = set(mcp._tool_manager._tools.keys())
    expected = {
        "create_project_from_terms",
        "save_discussion_facts",
        "get_contract_template",
        "create_contract_version",
        "create_signature_request",
        "get_latest_active_contract",
        "create_milestones_from_contract",
        "get_due_communications",
        "queue_routine_update",
        "create_scope_change_request",
        "evaluate_automation_policy",
        "get_project_timeline",
    }
    assert tools == expected

    # Check forbidden tools absent
    forbidden = {
        "send_email",
        "send_whatsapp",
        "send_telegram",
        "send_instagram_message",
        "control_browser",
        "sign_on_behalf_of_client",
        "sign_on_behalf_of_freelancer",
        "collect_payment",
        "file_legal_claim",
        "submit_complaint",
        "delete_audit_log",
        "update_audit_log",
    }
    assert tools.isdisjoint(forbidden)

    # Check backend-only actions absent
    backend_only = {
        "record_signature_acceptance",
        "record_milestone_progress",
        "pause_project_automation",
        "record_client_reply",
        "append_audit_log",
    }
    assert tools.isdisjoint(backend_only)


def test_pydantic_forbid_extra_fields():
    from pydantic import ValidationError

    from app.mcp_server.server import CreateProjectFromTermsRequest

    with pytest.raises(ValidationError):
        CreateProjectFromTermsRequest(
            title="Title", source_platform="Instagram", extra_field="not_allowed"
        )


# --- Test Policy and Side Effects ---


def test_read_only_tools_no_mutation(session, service):
    project = service.create_project(session, "Proj", None, "Instagram")
    plan_json = json.dumps([{"source_plan_item_key": "k1", "title": "Milestone 1"}])
    agreement = service.create_agreement_draft(
        session,
        project.id,
        "FS-001",
        "Scope",
        json.dumps(["Deliv"]),
        1,
        1000,
        "USD",
        "Net 30",
        None,
        plan_json,
    )
    service.transition_to_pending_signature(session, agreement.id)
    service.record_signature(
        session, agreement.id, PartyRole.freelancer, "F1", "Accept"
    )
    service.record_signature(session, agreement.id, PartyRole.client, "C1", "Accept")

    count_before = len(service.repository.get_audit_events(session, project.id))

    # Read-only calls
    service.get_latest_active_contract(session, project.id)
    service.get_due_communications(session, project.id)
    service.evaluate_automation_policy(
        session, project.id, agreement.id, "kickoff_confirmation"
    )
    service.get_project_timeline(session, project.id)

    count_after = len(service.repository.get_audit_events(session, project.id))
    assert count_before == count_after


def test_create_scope_change_request_safety(session, service):
    project = service.create_project(session, "Proj", None, "Instagram")
    plan_json = json.dumps([{"source_plan_item_key": "k1", "title": "Milestone 1"}])
    agreement = service.create_agreement_draft(
        session,
        project.id,
        "FS-001",
        "Scope",
        json.dumps(["Deliv"]),
        1,
        1000,
        "USD",
        "Net 30",
        None,
        plan_json,
    )
    service.transition_to_pending_signature(session, agreement.id)
    service.record_signature(
        session, agreement.id, PartyRole.freelancer, "F1", "Accept"
    )
    service.record_signature(session, agreement.id, PartyRole.client, "C1", "Accept")

    # 1. Create a client reply
    reply = service.record_client_reply(
        session=session,
        project_id=project.id,
        client_message_id=None,
        body="Can we do Instagram Story too?",
        classification=ReplyClassification.FEEDBACK,
        possible_scope_change=False,
    )
    session.commit()

    # 2. Try calling create_scope_change_request with non-existent reply ID
    with pytest.raises(ValidationError):
        service.create_scope_change_request(session, uuid4(), "Scope change summary")

    # 3. Call with valid reply ID. It should atomically pause project and write audits
    service.create_scope_change_request(session, reply.id, "Story adaptation")
    session.commit()

    session.refresh(project)
    assert project.status == ProjectStatus.SCOPE_CHANGE_PENDING
    assert project.automation_enabled is False

    audits = service.repository.get_audit_events(session, project.id)
    actions = [a.action for a in audits]
    assert "scope_change_detected" in actions
    assert "project_automation_paused" in actions


def test_queue_routine_update_validation(session, service):
    project = service.create_project(session, "Proj", None, "Instagram")
    plan_json = json.dumps(
        [
            {
                "source_plan_item_key": "k1",
                "title": "Milestone 1",
                "due_at": "2026-07-10T12:00:00",
            }
        ]
    )
    agreement = service.create_agreement_draft(
        session,
        project.id,
        "FS-001",
        "Scope",
        json.dumps(["Deliv"]),
        1,
        1000,
        "USD",
        "Net 30",
        None,
        plan_json,
    )
    service.transition_to_pending_signature(session, agreement.id)
    service.record_signature(
        session, agreement.id, PartyRole.freelancer, "F1", "Accept"
    )
    service.record_signature(session, agreement.id, PartyRole.client, "C1", "Accept")
    session.refresh(project)
    session.refresh(agreement)

    # 1. Queue a routine update kickoff_confirmation.
    msg = service.queue_routine_update(
        session=session,
        project_id=project.id,
        agreement_version_id=agreement.id,
        requested_action="kickoff_confirmation",
        idempotency_key="idemp_1",
    )
    assert msg.status == MessageStatus.QUEUED

    # 2. Re-queuing with same key must fail
    with pytest.raises(ValidationError):
        service.queue_routine_update(
            session=session,
            project_id=project.id,
            agreement_version_id=agreement.id,
            requested_action="kickoff_confirmation",
            idempotency_key="idemp_1",
        )

    # 3. Non-routine update like delay notice must fail (always requires approval)
    with pytest.raises(ValidationError):
        service.queue_routine_update(
            session=session,
            project_id=project.id,
            agreement_version_id=agreement.id,
            requested_action="delay",
            idempotency_key="idemp_2",
        )


# --- Test STDIO and Error Safety ---


def test_stdio_subsystem_tool_calls(session):
    import json
    import subprocess

    # We will launch the server in a subprocess and send/receive STDIO messages
    # Standard MCP JSON-RPC protocol
    process = subprocess.Popen(
        [sys.executable, "-m", "app.mcp_server.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )

    # Send a listTools request
    init_req = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
        "id": 0,
    }

    try:
        # 1. Send initialize
        process.stdin.write(json.dumps(init_req) + "\n")
        process.stdin.flush()
        process.stdout.readline()  # Read response

        # 2. Send initialized notification
        process.stdin.write(
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
        )
        process.stdin.flush()

        # 3. Send tools/list
        req = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        process.stdin.write(json.dumps(req) + "\n")
        process.stdin.flush()

        # Read response line
        line = process.stdout.readline()
        resp = json.loads(line)

        assert "result" in resp
        tool_names = [t["name"] for t in resp["result"]["tools"]]
        assert "create_project_from_terms" in tool_names
    finally:
        process.terminate()
        process.wait()


def test_error_safety():
    from app.mcp_server.server import sanitize_message

    # SQL injection/leak prevention
    msg = "OperationalError: no such table: projects in SELECT * FROM projects"
    assert "projects" not in sanitize_message(msg)
    assert "SELECT" not in sanitize_message(msg)

    # File paths
    msg_path = "FileNotFoundError: C:\\Users\\chazi\\database.db not found"
    assert "chazi" not in sanitize_message(msg_path)

    # Secrets
    os.environ["SENTINEL_SECRET_KEY"] = "super-secret-gemini-key"
    msg_sec = "Failed authorization using key super-secret-gemini-key"
    assert "super-secret-gemini-key" not in sanitize_message(msg_sec)
    assert "[SECRET]" in sanitize_message(msg_sec)
