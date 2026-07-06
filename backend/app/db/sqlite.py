import sqlite3
from pathlib import Path

from sqlmodel import SQLModel, text

from app.config import settings
from app.db.database import engine

# Import all models to ensure metadata registration
from app.models.domain import (  # noqa: F401
    AgreementVersion,
    AuditEvent,
    ClientMessage,
    ClientReply,
    CommunicationDraft,
    EvidenceEvent,
    Milestone,
    Project,
    ScopeChangeRequest,
    SignatureRecord,
)


def connect() -> sqlite3.Connection:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(path: Path | None = None) -> None:
    database_path = path or settings.database_path
    database_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize SQLModel metadata
    SQLModel.metadata.create_all(engine)

    # Establish triggers to protect audit_events
    with engine.connect() as connection:
        connection.execute(
            text("""
            CREATE TRIGGER IF NOT EXISTS prevent_audit_update
            BEFORE UPDATE ON audit_events
            BEGIN
                SELECT RAISE(ABORT, 'Updates on audit_events are not allowed');
            END;
        """)
        )
        connection.execute(
            text("""
            CREATE TRIGGER IF NOT EXISTS prevent_audit_delete
            BEFORE DELETE ON audit_events
            BEGIN
                SELECT RAISE(ABORT, 'Deletions on audit_events are not allowed');
            END;
        """)
        )
        connection.commit()
