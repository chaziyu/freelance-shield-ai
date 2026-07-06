# REST API Contract

## Status

This is the target `/api` contract for the corrected contract-driven communication MVP. The current implementation still exposes legacy evidence/payment-follow-up routes; those routes are not part of this target and must be migrated in Milestone 6.

## Conventions

- Content type: `application/json`.
- IDs: UUID strings.
- Timestamps: UTC ISO 8601 strings.
- Dates and times remain unresolved as `null` when not explicitly supplied or safely normalized.
- Money: positive decimal-safe amount plus ISO 4217 currency code.
- Enums: uppercase strings exactly as documented.
- Discussion and reply bodies are untrusted data fields.
- Routine messages may be delivered only to `DEMO_INBOX`.
- Approval-required message bodies include `Draft only — review and send manually.`

## Shared enums

```text
ProjectStatus:
  DISCUSSION_CAPTURED | TERMS_REVIEW | CONTRACT_PENDING_SIGNATURE |
  ACTIVE | SCOPE_CHANGE_PENDING | PAUSED | COMPLETED | CLOSED

AgreementStatus:
  DRAFT | FREELANCER_ACCEPTED | CLIENT_ACCEPTED | ACTIVE | SUPERSEDED

PartyRole:
  FREELANCER | CLIENT

SignatureStatus:
  PENDING | ACCEPTED

MilestoneStatus:
  PLANNED | IN_PROGRESS | READY_FOR_REVIEW | COMPLETED | BLOCKED

MessageType:
  KICKOFF_CONFIRMATION | UPCOMING_MILESTONE_REMINDER |
  REVISION_WINDOW_REMINDER | DELIVERY_CONFIRMATION |
  INVOICE_AVAILABILITY_NOTICE | DELAY_NOTICE | SCOPE_CHANGE_RESPONSE |
  PAYMENT_REMINDER | DISPUTE_RESPONSE

SendMode:
  ROUTINE_AUTO | APPROVAL_REQUIRED

MessageStatus:
  DRAFT | APPROVAL_REQUIRED | APPROVED | QUEUED |
  DELIVERED_TO_DEMO_INBOX | ACKNOWLEDGED | BLOCKED

ReplyClassification:
  ACKNOWLEDGEMENT | FEEDBACK | QUESTION | SCOPE_CHANGE | CONCERN

ScopeChangeStatus:
  DETECTED | PENDING_REVIEW | ACCEPTED | REJECTED

TraceStatus:
  STARTED | SUCCEEDED | BLOCKED | FAILED
```

## Shared objects

### DiscussionFacts

```json
{
  "project_title": "Poster design",
  "scope": "Design one promotional poster.",
  "deliverables": [],
  "fee_amount": 800,
  "currency": "MYR",
  "deadline": null,
  "revision_limit": 2,
  "payment_terms": null,
  "missing_fields": ["deadline", "payment_terms"],
  "risk_flags": ["informal_platform"]
}
```

### Project

```json
{
  "id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "title": "Poster design",
  "client_name": "Demo Client",
  "source_platform": "Instagram",
  "status": "CONTRACT_PENDING_SIGNATURE",
  "automation_enabled": false,
  "created_at": "2026-07-06T04:00:00Z",
  "updated_at": "2026-07-06T04:05:00Z"
}
```

### AgreementVersion

```json
{
  "id": "b5509f66-955a-4e3e-b925-c82d85fbdf8d",
  "project_id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "agreement_code": "FS-001",
  "version_number": 1,
  "scope": "Design one promotional poster.",
  "deliverables": ["First draft", "Final poster file"],
  "revision_limit": 2,
  "fee_amount": 800,
  "currency": "MYR",
  "payment_terms": "Payment due within 7 days of invoice.",
  "effective_start_date": "2026-07-07",
  "acceptance_status": "DRAFT",
  "created_at": "2026-07-06T04:05:00Z",
  "activated_at": null
}
```

### SignatureRecord

```json
{
  "id": "6ce86f2f-7814-4d17-baf6-91ca1a72e605",
  "agreement_version_id": "b5509f66-955a-4e3e-b925-c82d85fbdf8d",
  "party_role": "FREELANCER",
  "signer_display_name": "Demo Freelancer",
  "acceptance_text": "I accept Contract FS-001 Version 1 as the freelancer.",
  "status": "ACCEPTED",
  "accepted_at": "2026-07-06T04:10:00Z"
}
```

### Milestone

```json
{
  "id": "f93bac35-e9cf-4bb0-a81e-93365a0ef289",
  "project_id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "agreement_version_id": "b5509f66-955a-4e3e-b925-c82d85fbdf8d",
  "title": "First draft",
  "description": "Prepare the first poster draft for review.",
  "due_at": "2026-07-08T09:00:00Z",
  "status": "READY_FOR_REVIEW",
  "completion_recorded_at": "2026-07-08T08:30:00Z",
  "recorded_by": "freelancer"
}
```

### ClientMessage

```json
{
  "id": "895e5832-1662-4eb9-ab1d-cc3b9296e170",
  "project_id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "agreement_version_id": "b5509f66-955a-4e3e-b925-c82d85fbdf8d",
  "milestone_id": "f93bac35-e9cf-4bb0-a81e-93365a0ef289",
  "message_type": "DELIVERY_CONFIRMATION",
  "body": "Your first draft is ready for review. Please share feedback within the agreed revision window.",
  "send_mode": "ROUTINE_AUTO",
  "status": "DELIVERED_TO_DEMO_INBOX",
  "scheduled_for": "2026-07-08T08:30:00Z",
  "delivered_at": "2026-07-08T08:31:00Z",
  "idempotency_key": "sha256-hex"
}
```

### ClientReply

```json
{
  "id": "0b16bfea-bd78-45a3-a63f-443ae72b9ee1",
  "project_id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "client_message_id": "895e5832-1662-4eb9-ab1d-cc3b9296e170",
  "body": "Can you also make an Instagram Story version using the same design?",
  "classification": "SCOPE_CHANGE",
  "possible_scope_change": true,
  "received_at": "2026-07-08T09:00:00Z"
}
```

### ScopeChangeRequest

```json
{
  "id": "e8294986-d4c8-407e-a992-3f106fa0a3ec",
  "project_id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "source_reply_id": "0b16bfea-bd78-45a3-a63f-443ae72b9ee1",
  "summary": "Client requested an additional Instagram Story format.",
  "status": "PENDING_REVIEW",
  "proposed_contract_version_id": null,
  "created_at": "2026-07-08T09:00:01Z"
}
```

### TraceEvent and AuditEvent

```json
{
  "actor": "CommunicationAgent",
  "action": "record_client_reply",
  "status": "SUCCEEDED",
  "timestamp": "2026-07-08T09:00:00Z",
  "metadata": {"classification": "SCOPE_CHANGE"}
}
```

Trace and audit metadata is allowlisted. It never contains raw prompts, secrets, environment values, stack traces, or hidden database details.

## Error contract

```json
{
  "error": {
    "code": "mutual_acceptance_required",
    "message": "Both parties must accept the same contract version before activation.",
    "request_id": "c2aa85b5-60bd-4dc2-92cf-fdbd929a24a0",
    "details": []
  }
}
```

| Status | Use |
| --- | --- |
| `400` | Semantically invalid request |
| `404` | Referenced resource not found |
| `409` | Invalid state transition, version conflict, duplicate delivery, or acceptance mismatch |
| `422` | Request schema validation failure |
| `500` | Generic safe message and request ID only |
| `503` | Required ADK/model configuration unavailable |

Policy blocks return `200` with explicit `allowed`, `blocked`, and reason-code fields; they are audited expected outcomes.

## Endpoints

### `POST /api/discussions/analyse`

Request:

```json
{
  "discussion_text": "Need a poster by Friday. RM800. Two revisions.",
  "source_platform": "Instagram",
  "reference_date": null
}
```

Response `200`:

```json
{
  "facts": {},
  "trace": []
}
```

This endpoint does not create a contract. Relative dates remain unresolved without a reference date.

### `POST /api/projects`

Creates a project from freelancer-reviewed facts.

```json
{
  "title": "Poster design",
  "client_name": "Demo Client",
  "source_platform": "Instagram",
  "reviewed_facts": {}
}
```

Response `201`: `{ "project": {}, "trace": [] }`, initial state `TERMS_REVIEW`.

### `POST /api/projects/{project_id}/contracts`

Creates V1 or the next immutable version from reviewed facts. The backend assigns code and version.

```json
{
  "scope": "Design one promotional poster.",
  "deliverables": ["First draft", "Final poster file"],
  "milestones": [
    {"title": "First draft", "due_at": "2026-07-08T09:00:00Z"},
    {"title": "Final files", "due_at": "2026-07-10T09:00:00Z"}
  ],
  "revision_limit": 2,
  "fee_amount": 800,
  "currency": "MYR",
  "payment_terms": "Payment due within 7 days of invoice.",
  "effective_start_date": "2026-07-07",
  "scope_change_request_id": null
}
```

Response `201`: contract, two pending signature requests, project state `CONTRACT_PENDING_SIGNATURE`, and trace.

### `POST /api/contracts/{contract_id}/acceptance`

Records a user-triggered acceptance. It never infers or creates the other party's acceptance.

```json
{
  "party_role": "FREELANCER",
  "signer_display_name": "Demo Freelancer",
  "acceptance_text": "I accept Contract FS-001 Version 1 as the freelancer."
}
```

The simulated client uses `party_role: "CLIENT"` and exact client wording. Once both roles accept the same latest version, the response activates the contract, creates milestones, enables automation, and supersedes the previous active version when applicable. Duplicate or mismatched acceptance returns `409` and is audited.

### `POST /api/projects/{project_id}/milestones/{milestone_id}/progress`

Freelancer-only application action:

```json
{
  "status": "READY_FOR_REVIEW",
  "note": "First draft recorded as ready."
}
```

AI output cannot call this route or tool. The response contains the milestone and any newly due communication event.

### `POST /api/projects/{project_id}/scheduler/run`

Runs the same scheduler service as the periodic/internal trigger for one project. It checks active version, mutual acceptance, automation state, progress evidence, send mode, safety, and idempotency.

Response:

```json
{
  "queued": 1,
  "delivered_to_demo_inbox": 1,
  "skipped_duplicates": 0,
  "blocked": [],
  "trace": []
}
```

### `POST /api/internal/run-scheduled-update-check`

Runs the same scheduler method across eligible projects. This is for predictable local demos/tests and is not a public production scheduler endpoint.

### `POST /api/projects/{project_id}/client-replies`

```json
{
  "client_message_id": "895e5832-1662-4eb9-ab1d-cc3b9296e170",
  "body": "Can you also make an Instagram Story version using the same design?"
}
```

Response records the reply, classification, possible-scope-change flag, automation state, optional change request, and trace. Reply text is untrusted data and cannot itself change contract terms.

### `POST /api/projects/{project_id}/scope-changes`

Freelancer reviews a detected request:

```json
{
  "scope_change_request_id": "e8294986-d4c8-407e-a992-3f106fa0a3ec",
  "decision": "ACCEPTED",
  "summary": "Add one Instagram Story adaptation."
}
```

An accepted request creates proposed V2 with pending signatures. A rejected request records the decision and resumes eligible V1 automation. Neither result silently changes the active contract.

### `GET /api/projects/{project_id}`

Returns project, latest active contract, pending proposed contract, signature statuses, milestones, automation status, pending scope change, message summary, audit summary, and latest backend trace.

### `GET /api/projects/{project_id}/timeline`

Returns chronological discussion, contract, signature, milestone, queue, delivery, reply, scope-change, and version-activation events. Public timeline entries omit private audit metadata.

### `GET /api/projects/{project_id}/messages`

Returns queued, approval-required, blocked, and demo-inbox-delivered messages. It exposes no external-send action.

### `GET /api/projects/{project_id}/audit`

Returns oldest-first append-only `AuditEvent` objects. There is no audit update or delete endpoint.

### `GET /api/health`

```json
{"status": "ok", "service": "freelance-shield-ai"}
```

Health responses reveal no versions, environment variables, paths, credentials, or internal exceptions.

## Mandatory service enforcement

- Mutual acceptance is version-specific.
- Contract activation, supersession, milestone creation, and automation enablement are transactional.
- Progress requires a freelancer-recorded action.
- Scheduler delivery uses only the latest active version and a unique idempotency key.
- Approval-required messages cannot reach the demo inbox before explicit approval.
- Scope-change classification creates a request and pause, not a contract mutation.
- All writes and rejected attempts create audit events.
