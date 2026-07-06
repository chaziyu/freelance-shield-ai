import json
import sqlite3
from datetime import date, datetime
from typing import Any
from uuid import UUID

from app.db.sqlite import connect
from app.schemas.workflow import (
    AcceptanceStatus,
    AgreementVersion,
    AuditEvent,
    CommunicationDraft,
    DraftAuditStatus,
    DraftType,
    EvidenceEvent,
    EvidenceType,
    FollowUpPolicy,
    Project,
    ProjectStatus,
)


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _date_out(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _dt_out(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class WorkflowRepository:
    def create_project(
        self,
        *,
        project_id: UUID,
        title: str,
        source_platform: str,
        amount: float | None,
        currency: str | None,
        deadline: date | None,
        status: ProjectStatus,
        now: datetime,
    ) -> Project:
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO projects (
                    id, title, source_platform, amount, currency, deadline,
                    status, dispute_flag, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    str(project_id),
                    title,
                    source_platform,
                    amount,
                    currency,
                    _date_out(deadline),
                    status.value,
                    _dt_out(now),
                    _dt_out(now),
                ),
            )
            connection.commit()
        return self.get_project(project_id)

    def get_project(self, project_id: UUID) -> Project:
        row = self._fetch_one("SELECT * FROM projects WHERE id = ?", (str(project_id),))
        if row is None:
            raise KeyError("project_not_found")
        return self._project_from_row(row)

    def update_project_state(
        self,
        project_id: UUID,
        *,
        status: ProjectStatus,
        now: datetime,
        dispute_flag: bool | None = None,
        invoice_due_date: date | None = None,
        latest_policy: FollowUpPolicy | None = None,
    ) -> Project:
        project = self.get_project(project_id)
        with connect() as connection:
            connection.execute(
                """
                UPDATE projects
                SET status = ?,
                    dispute_flag = ?,
                    invoice_due_date = COALESCE(?, invoice_due_date),
                    latest_policy_json = COALESCE(?, latest_policy_json),
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    status.value,
                    int(project.dispute_flag if dispute_flag is None else dispute_flag),
                    _date_out(invoice_due_date),
                    latest_policy.model_dump_json() if latest_policy else None,
                    _dt_out(now),
                    str(project_id),
                ),
            )
            connection.commit()
        return self.get_project(project_id)

    def create_agreement(
        self,
        agreement: AgreementVersion,
        project_status: ProjectStatus,
        now: datetime,
    ) -> AgreementVersion:
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO agreement_versions (
                    id, project_id, agreement_code, version_number, scope,
                    deliverables, revision_limit, amount, currency, deadline,
                    payment_terms, acceptance_status, accepted_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(agreement.id),
                    str(agreement.project_id),
                    agreement.agreement_code,
                    agreement.version_number,
                    agreement.scope,
                    agreement.deliverables,
                    agreement.revision_limit,
                    agreement.amount,
                    agreement.currency,
                    _date_out(agreement.deadline),
                    agreement.payment_terms,
                    agreement.acceptance_status.value,
                    _dt_out(agreement.accepted_at),
                    _dt_out(agreement.created_at),
                ),
            )
            connection.execute(
                "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
                (project_status.value, _dt_out(now), str(agreement.project_id)),
            )
            connection.commit()
        return self.get_current_agreement(agreement.project_id)

    def get_current_agreement(self, project_id: UUID) -> AgreementVersion | None:
        row = self._fetch_one(
            """
            SELECT * FROM agreement_versions
            WHERE project_id = ?
            ORDER BY version_number DESC
            LIMIT 1
            """,
            (str(project_id),),
        )
        return self._agreement_from_row(row) if row else None

    def accept_agreement(
        self,
        agreement_id: UUID,
        project_id: UUID,
        now: datetime,
    ) -> AgreementVersion:
        with connect() as connection:
            connection.execute(
                """
                UPDATE agreement_versions
                SET acceptance_status = ?, accepted_at = ?
                WHERE id = ?
                """,
                (AcceptanceStatus.ACCEPTED.value, _dt_out(now), str(agreement_id)),
            )
            connection.execute(
                "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
                (ProjectStatus.ACCEPTED.value, _dt_out(now), str(project_id)),
            )
            connection.commit()
        current = self.get_current_agreement(project_id)
        if current is None:
            raise KeyError("agreement_not_found")
        return current

    def create_evidence(self, evidence: EvidenceEvent) -> EvidenceEvent:
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO evidence_events (
                    id, project_id, event_type, summary, content_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(evidence.id),
                    str(evidence.project_id),
                    evidence.event_type.value,
                    evidence.summary,
                    evidence.content_hash,
                    _dt_out(evidence.created_at),
                ),
            )
            connection.commit()
        return evidence

    def list_evidence(self, project_id: UUID) -> list[EvidenceEvent]:
        rows = self._fetch_all(
            """
            SELECT * FROM evidence_events
            WHERE project_id = ?
            ORDER BY created_at ASC
            """,
            (str(project_id),),
        )
        return [self._evidence_from_row(row) for row in rows]

    def create_draft(self, draft: CommunicationDraft) -> CommunicationDraft:
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO communication_drafts (
                    id, project_id, draft_type, body, audit_status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(draft.id),
                    str(draft.project_id),
                    draft.draft_type.value,
                    draft.body,
                    draft.audit_status.value,
                    _dt_out(draft.created_at),
                ),
            )
            connection.commit()
        return draft

    def get_latest_draft(self, project_id: UUID) -> CommunicationDraft | None:
        row = self._fetch_one(
            """
            SELECT * FROM communication_drafts
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (str(project_id),),
        )
        return self._draft_from_row(row) if row else None

    def append_audit(
        self,
        *,
        event_id: UUID,
        project_id: UUID | None,
        actor: str,
        action: str,
        metadata: dict[str, Any],
        now: datetime,
    ) -> AuditEvent:
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_events (
                    id, project_id, actor, action, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(event_id),
                    str(project_id) if project_id else None,
                    actor,
                    action,
                    json.dumps(metadata, sort_keys=True),
                    _dt_out(now),
                ),
            )
            connection.commit()
        return AuditEvent(
            id=event_id,
            project_id=project_id,
            actor=actor,
            action=action,
            metadata=metadata,
            created_at=now,
        )

    def list_audit(self, project_id: UUID) -> list[AuditEvent]:
        rows = self._fetch_all(
            "SELECT * FROM audit_events WHERE project_id = ? ORDER BY created_at ASC",
            (str(project_id),),
        )
        return [self._audit_from_row(row) for row in rows]

    def get_latest_policy(self, project_id: UUID) -> FollowUpPolicy | None:
        row = self._fetch_one(
            "SELECT latest_policy_json FROM projects WHERE id = ?",
            (str(project_id),),
        )
        if row is None or row["latest_policy_json"] is None:
            return None
        return FollowUpPolicy.model_validate_json(row["latest_policy_json"])

    def _fetch_one(self, sql: str, values: tuple[Any, ...]) -> sqlite3.Row | None:
        with connect() as connection:
            return connection.execute(sql, values).fetchone()

    def _fetch_all(self, sql: str, values: tuple[Any, ...]) -> list[sqlite3.Row]:
        with connect() as connection:
            return list(connection.execute(sql, values).fetchall())

    def _project_from_row(self, row: sqlite3.Row) -> Project:
        return Project(
            id=UUID(row["id"]),
            title=row["title"],
            client_name=row["client_name"],
            source_platform=row["source_platform"],
            amount=row["amount"],
            currency=row["currency"],
            deadline=_date(row["deadline"]),
            invoice_due_date=_date(row["invoice_due_date"]),
            status=ProjectStatus(row["status"]),
            dispute_flag=bool(row["dispute_flag"]),
            created_at=_dt(row["created_at"]),
            updated_at=_dt(row["updated_at"]),
        )

    def _agreement_from_row(self, row: sqlite3.Row) -> AgreementVersion:
        return AgreementVersion(
            id=UUID(row["id"]),
            project_id=UUID(row["project_id"]),
            agreement_code=row["agreement_code"],
            version_number=row["version_number"],
            scope=row["scope"],
            deliverables=row["deliverables"],
            revision_limit=row["revision_limit"],
            amount=row["amount"],
            currency=row["currency"],
            deadline=_date(row["deadline"]),
            payment_terms=row["payment_terms"],
            acceptance_status=AcceptanceStatus(row["acceptance_status"]),
            accepted_at=_dt(row["accepted_at"]),
            created_at=_dt(row["created_at"]),
        )

    def _evidence_from_row(self, row: sqlite3.Row) -> EvidenceEvent:
        return EvidenceEvent(
            id=UUID(row["id"]),
            project_id=UUID(row["project_id"]),
            event_type=EvidenceType(row["event_type"]),
            summary=row["summary"],
            content_hash=row["content_hash"],
            created_at=_dt(row["created_at"]),
        )

    def _draft_from_row(self, row: sqlite3.Row) -> CommunicationDraft:
        return CommunicationDraft(
            id=UUID(row["id"]),
            project_id=UUID(row["project_id"]),
            draft_type=DraftType(row["draft_type"]),
            body=row["body"],
            audit_status=DraftAuditStatus(row["audit_status"]),
            created_at=_dt(row["created_at"]),
        )

    def _audit_from_row(self, row: sqlite3.Row) -> AuditEvent:
        return AuditEvent(
            id=UUID(row["id"]),
            project_id=UUID(row["project_id"]) if row["project_id"] else None,
            actor=row["actor"],
            action=row["action"],
            metadata=json.loads(row["metadata_json"]),
            created_at=_dt(row["created_at"]),
        )
