import sqlite3
from pathlib import Path

from app.config import settings


def connect() -> sqlite3.Connection:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(path: Path | None = None) -> None:
    database_path = path or settings.database_path
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                client_name TEXT,
                source_platform TEXT NOT NULL,
                amount REAL,
                currency TEXT,
                deadline TEXT,
                invoice_due_date TEXT,
                status TEXT NOT NULL,
                dispute_flag INTEGER NOT NULL DEFAULT 0,
                latest_policy_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agreement_versions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id),
                agreement_code TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                scope TEXT NOT NULL,
                deliverables TEXT NOT NULL,
                revision_limit INTEGER,
                amount REAL,
                currency TEXT,
                deadline TEXT,
                payment_terms TEXT,
                acceptance_status TEXT NOT NULL,
                accepted_at TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(project_id, agreement_code, version_number)
            );

            CREATE TABLE IF NOT EXISTS evidence_events (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id),
                event_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS communication_drafts (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id),
                draft_type TEXT NOT NULL,
                body TEXT NOT NULL,
                audit_status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                project_id TEXT REFERENCES projects(id),
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        connection.commit()
    finally:
        connection.close()
