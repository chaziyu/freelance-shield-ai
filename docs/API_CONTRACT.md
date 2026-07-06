# REST API Contract

## Status

This is the MVP contract for `/api`. The current implementation includes `GET /api/health`, workflow routes, SQLite-backed persistence, API-backed Intake, Agreement, Acceptance, Evidence, Follow-Up, and Audit UI slices, a real internal MCP server, and Google ADK agent definitions. Local scaffold workflow writes require `FREELANCE_SHIELD_ALLOW_LOCAL_WORKFLOW=1`; the production path still must replace the REST scaffold shortcut with active Google ADK coordinator execution using the internal MCP server. Implementation may add fields only when documentation and aligned frontend/backend schemas are updated together; the safety behavior below is mandatory.

## Conventions

- Content type: `application/json`.
- IDs: UUID strings.
- Timestamps: UTC ISO 8601 strings, for example `2026-07-06T04:00:00Z`.
- Timestamp display: API responses remain UTC. The frontend may render timestamps using a user-selected GMT offset, for example `GMT+08:00`, without changing stored values or response ordering.
- Dates: ISO 8601 calendar dates, for example `2026-07-10`.
- Money: positive JSON number plus ISO 4217 currency code. The persistence implementation must use decimal-safe storage rather than binary floating-point arithmetic.
- Unknown or unresolved values: `null`; agents must not invent them.
- Enum values: uppercase strings exactly as listed here.
- All generated communication bodies include `Draft only — review and send manually.`

## Shared enums

```text
ProjectStatus:
  DRAFT | TERMS_READY | ACCEPTANCE_PENDING | ACCEPTED | IN_PROGRESS |
  DELIVERED | INVOICED | OVERDUE | CLOSED | DISPUTED | RESOLUTION_PENDING

AcceptanceStatus:
  DRAFT | PENDING | ACCEPTED

EvidenceType:
  ACCEPTANCE | DELIVERY | INVOICE | SCOPE_CHANGE

DraftType:
  ACCEPTANCE_REQUEST | DELIVERY_CONFIRMATION | PAYMENT_REMINDER |
  DISPUTE_CLARIFICATION

DraftAuditStatus:
  PENDING | APPROVED_TO_SHOW | BLOCKED

TraceStatus:
  STARTED | SUCCEEDED | BLOCKED | FAILED
```

## Shared objects

### Project

```json
{
  "id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "title": "Poster design",
  "client_name": null,
  "source_platform": "Instagram",
  "amount": 800,
  "currency": "MYR",
  "deadline": null,
  "invoice_due_date": null,
  "status": "DRAFT",
  "dispute_flag": false,
  "created_at": "2026-07-06T04:00:00Z",
  "updated_at": "2026-07-06T04:00:00Z"
}
```

### ExtractedFacts

```json
{
  "project_title": "Poster design",
  "amount": 800,
  "currency": "MYR",
  "deadline": null,
  "revision_limit": 2,
  "payment_terms": null,
  "missing_fields": ["deadline", "payment_terms"],
  "risk_flags": ["informal_platform"]
}
```

The relative phrase “Friday” is not converted to a date without a supplied reference date.

### AgreementVersion

```json
{
  "id": "b5509f66-955a-4e3e-b925-c82d85fbdf8d",
  "project_id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "agreement_code": "FS-001",
  "version_number": 1,
  "scope": "Design one promotional poster.",
  "deliverables": "One final digital poster file.",
  "revision_limit": 2,
  "amount": 800,
  "currency": "MYR",
  "deadline": "2026-07-10",
  "payment_terms": "Payment due within 7 days of invoice.",
  "acceptance_status": "PENDING",
  "accepted_at": null,
  "created_at": "2026-07-06T04:05:00Z"
}
```

### EvidenceEvent

```json
{
  "id": "36ae756a-72ea-4677-b451-f45f6b9d2855",
  "project_id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "event_type": "DELIVERY",
  "summary": "Synthetic poster delivery recorded.",
  "content_hash": "64-character-lowercase-sha256-hex-value",
  "created_at": "2026-07-06T05:00:00Z"
}
```

Hashes are content-integrity aids only; they do not prove authorship, ownership, authenticity, event time, or legal admissibility.

### CommunicationDraft

```json
{
  "id": "895e5832-1662-4eb9-ab1d-cc3b9296e170",
  "project_id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "draft_type": "DISPUTE_CLARIFICATION",
  "body": "Thanks for raising your concern. Please identify the incomplete items so we can compare them with the agreed scope and discuss next steps.\n\nDraft only — review and send manually.",
  "audit_status": "APPROVED_TO_SHOW",
  "created_at": "2026-07-06T05:10:00Z"
}
```

### TraceEvent

```json
{
  "actor": "FollowUpAgent",
  "action": "evaluate_follow_up_policy",
  "status": "SUCCEEDED",
  "timestamp": "2026-07-06T05:10:00Z",
  "metadata": {
    "outcome": "DISPUTE_CLARIFICATION"
  }
}
```

Trace metadata is an allowlisted public summary. It must not contain raw prompts, secrets, environment values, hidden database details, or stack traces.

### TimelineSummary

```json
{
  "event_count": 6,
  "latest_event_type": "DRAFT_CREATED",
  "latest_event_at": "2026-07-06T05:10:00Z",
  "hash_previews": ["36ae75", "64be01", "895e58"]
}
```

Hash previews are short UI labels only. Full hashes remain available on evidence records where needed and are still integrity aids only.

### AuditSummary

```json
{
  "event_count": 9,
  "latest_actor": "SafetyAuditAgent",
  "latest_action": "draft_approved_to_show",
  "latest_event_at": "2026-07-06T05:10:00Z"
}
```

### AuditEvent

```json
{
  "id": "0f975e02-eb3a-419a-a646-b232a59f6e59",
  "project_id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "actor": "SafetyAuditAgent",
  "action": "draft_approved_to_show",
  "metadata": {
    "draft_type": "DISPUTE_CLARIFICATION"
  },
  "created_at": "2026-07-06T05:10:00Z"
}
```

## Error contract

All application errors use:

```json
{
  "error": {
    "code": "invalid_state_transition",
    "message": "The project cannot enter OVERDUE without an invoice due date.",
    "request_id": "c2aa85b5-60bd-4dc2-92cf-fdbd929a24a0",
    "details": []
  }
}
```

| Status | Use |
| --- | --- |
| `400` | Semantically invalid request not covered by field validation |
| `404` | Project or agreement not found |
| `409` | Invalid state transition, version conflict, or acceptance mismatch |
| `422` | Request schema validation failure; `details` may identify invalid fields without echoing sensitive values |
| `500` | Generic safe message and request ID only |

Safety blocks are expected workflow results, not server failures. They return `200` with `blocked: true`, no displayable draft, and audited reason codes.

## Endpoints

### `POST /api/intake/analyse`

Extract facts and create the initial project through `IntakeAgent` and its allowed MCP tools.

Request:

```json
{
  "chat_text": "Need a poster by Friday. RM800. Two revisions.",
  "source_platform": "Instagram",
  "reference_date": null
}
```

Rules:

- `chat_text` is required, bounded in implementation, and treated as untrusted data.
- `source_platform` is a user-facing label, not an external integration.
- `reference_date` is optional. Without it, relative dates remain unresolved.

Response `201`:

```json
{
  "project": {},
  "extracted_facts": {},
  "trace": []
}
```

The placeholders above carry the shared object shapes. Initial status is `DRAFT` when required terms remain unresolved, otherwise `TERMS_READY`.

### `POST /api/projects/{project_id}/agreements`

Create Version `1` or the next version through `AgreementAgent`. Existing versions are immutable.

Request:

```json
{
  "scope": "Design one promotional poster.",
  "deliverables": "One final digital poster file.",
  "revision_limit": 2,
  "amount": 800,
  "currency": "MYR",
  "deadline": "2026-07-10",
  "payment_terms": "Payment due within 7 days of invoice.",
  "change_reason": null
}
```

Response `201`:

```json
{
  "agreement": {},
  "acceptance_message": "Please reply: “I agree to Agreement FS-001 Version 1.”",
  "project_status": "ACCEPTANCE_PENDING",
  "trace": []
}
```

Rules:

- The backend assigns `agreement_code` and `version_number`; clients cannot choose them.
- Missing terms remain visibly unresolved and prevent acceptance until the service considers terms ready.
- When a current agreement exists, `change_reason` is required, the next version is created with `PENDING` acceptance, and a `SCOPE_CHANGE` evidence event is appended.

### `POST /api/projects/{project_id}/acceptance`

Record simulated acceptance through the trusted application workflow and approved MCP tools. This endpoint does not contact a client.

Request:

```json
{
  "agreement_code": "FS-001",
  "version_number": 1,
  "acceptance_text": "I agree to Agreement FS-001 Version 1."
}
```

Response `201`:

```json
{
  "agreement": {},
  "acceptance_evidence": {},
  "project_status": "ACCEPTED",
  "trace": []
}
```

The code, version, and normalized acceptance text must all refer to the current agreement. Mismatch returns `409`, changes no acceptance state, and appends a safe rejection audit event.

### `POST /api/projects/{project_id}/evidence`

Record delivery or invoice evidence through the trusted application workflow.

Delivery request:

```json
{
  "event_type": "DELIVERY",
  "summary": "Synthetic poster delivery recorded.",
  "invoice_due_date": null
}
```

Invoice request:

```json
{
  "event_type": "INVOICE",
  "summary": "Synthetic invoice INV-DEMO-001 recorded.",
  "invoice_due_date": "2026-07-13"
}
```

Response `201`:

```json
{
  "evidence": {},
  "project_status": "INVOICED",
  "trace": []
}
```

Public requests accept only `DELIVERY` or `INVOICE`; acceptance evidence comes from the acceptance endpoint and scope-change evidence comes from agreement versioning. An invoice requires `invoice_due_date`. The server canonicalizes summary line endings to LF, preserves all other text, hashes the UTF-8 bytes with SHA-256, and performs the state transition.

### `POST /api/projects/{project_id}/follow-up`

Evaluate policy, generate only the permitted draft, run safety review, and store an approved draft.

Undisputed request:

```json
{
  "dispute": null
}
```

Explicit simulated dispute request:

```json
{
  "dispute": {
    "declared": true,
    "message": "The poster is incomplete. I will not pay."
  }
}
```

The message is untrusted evidence. `declared: true` is an explicit user simulation that sets the deterministic dispute path; the model does not decide whether policy applies.

Approved response `200`:

```json
{
  "policy": {
    "allowed_draft_type": "DISPUTE_CLARIFICATION",
    "reason_codes": ["PROJECT_DISPUTED"],
    "blocked_draft_types": ["PAYMENT_REMINDER"]
  },
  "safety": {
    "safe_to_show": true,
    "blocked": false,
    "warnings": ["Draft only — review and send manually."],
    "blocked_reasons": []
  },
  "draft": {},
  "trace": []
}
```

Blocked response `200`:

```json
{
  "policy": {
    "allowed_draft_type": "DISPUTE_CLARIFICATION",
    "reason_codes": ["PROJECT_DISPUTED"],
    "blocked_draft_types": ["PAYMENT_REMINDER"]
  },
  "safety": {
    "safe_to_show": false,
    "blocked": true,
    "warnings": [],
    "blocked_reasons": ["PAYMENT_DEMAND_NOT_ALLOWED_DURING_DISPUTE"]
  },
  "draft": null,
  "trace": []
}
```

Policy order:

1. Any dispute → `DISPUTE_CLARIFICATION`.
2. No accepted current agreement → `ACCEPTANCE_REQUEST` with lower-certainty wording.
3. Accepted agreement and invoice overdue by server UTC date → `PAYMENT_REMINDER`.
4. Accepted agreement with no overdue invoice → `DELIVERY_CONFIRMATION`.

The server does not accept a requested draft type from the client.

### `GET /api/projects/{project_id}`

Response `200`:

```json
{
  "project": {},
  "current_agreement": {},
  "latest_policy": null,
  "latest_draft": null,
  "timeline_summary": null,
  "audit_summary": null,
  "latest_trace": []
}
```

`current_agreement` is `null` before an agreement exists.
The shell uses this response to render the project header, state rail, safety panel, and audit preview. The frontend must not fabricate these rows when the backend has not returned them.

### `GET /api/projects/{project_id}/timeline`

Response `200`:

```json
{
  "project_id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "events": [
    {
      "event_type": "AGREEMENT_CREATED",
      "summary": "Agreement FS-001 Version 1 created.",
      "timestamp": "2026-07-06T04:05:00Z",
      "reference_id": "b5509f66-955a-4e3e-b925-c82d85fbdf8d"
    }
  ]
}
```

Events are ordered oldest first. Timeline types may include project, agreement, acceptance, evidence, policy, and draft events; they do not expose private audit metadata.

### `GET /api/projects/{project_id}/audit`

Response `200`:

```json
{
  "project_id": "f90c4421-761a-47a6-b5d8-1c55b8982149",
  "events": []
}
```

Events use the shared `AuditEvent` shape and are ordered oldest first. The MVP exposes no audit update or delete endpoint.

### `GET /api/health`

Response `200`:

```json
{
  "status": "ok",
  "service": "freelance-shield-ai"
}
```

Health output must not reveal versions, environment variables, database paths, credentials, or internal exceptions.

## State-transition errors

The service layer, not agents or the frontend, enforces at minimum:

- acceptance only from `TERMS_READY` or `ACCEPTANCE_PENDING` for the current code/version;
- a new scope version resets acceptance to `PENDING`;
- `OVERDUE` only when an invoice due date exists and is before the current server UTC date;
- a dispute sets `dispute_flag = true` and prevents `PAYMENT_REMINDER`;
- each domain write and its audit event commit atomically.
