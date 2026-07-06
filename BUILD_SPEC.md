# FreelanceShield AI — Contract-Driven Communication Build Specification

## 1. Mission and status

Build a demo-ready Agents for Business capstone that turns an informal freelance discussion into a reviewed, mutually accepted contract and then uses the latest active contract to drive milestones and safe routine communication.

```text
discussion
→ reviewed terms
→ Contract FS-001 V1
→ freelancer + simulated client acceptance
→ active contract
→ milestones
→ routine update delivered to built-in demo inbox
→ client reply classification
→ scope-change request
→ Contract V2
→ renewed mutual acceptance
→ complete audit trail
```

This document is the corrected target specification. The repository currently contains implementation from the retired evidence/payment-follow-up design. Do not describe that implementation as completing this specification. Migrate it milestone by milestone after the documentation revision.

The finished system demonstrates:

- Google ADK multi-agent workflow;
- a real custom MCP server over STDIO;
- per-agent tool separation;
- deterministic scheduler and automation policy;
- a built-in simulated client inbox;
- versioned mutual acceptance and scope-change handling;
- append-only audit and security tests;
- Docker-based deployability and a responsive browser UI.

## 2. Product boundary

### Functional MVP

- Paste and analyse a synthetic client discussion.
- Review and edit extracted facts.
- Create immutable Contract `FS-001` versions.
- Record separate freelancer and simulated-client acceptance.
- Activate a contract only after both accept the same latest version.
- Create milestones from the active contract.
- Record freelancer-controlled milestone progress.
- Schedule, queue, safety-check, and deliver eligible routine updates to the internal demo inbox.
- Record and classify simulated client replies.
- Detect possible scope changes, pause affected automation, and create V2.
- Show project, message, agent, MCP, scheduler, and audit timelines.

### Simulated or deferred

- real e-signature providers;
- external client accounts;
- WhatsApp, email, Telegram, Instagram, or other production delivery;
- payment collection;
- legal research or enforcement;
- browser automation;
- multi-user authentication;
- file uploads and PDF signature workflows.

Allowed product statement:

```text
Routine updates are automatically delivered to the built-in demo inbox.
Production message-channel integrations are deferred.
```

Forbidden product statements include automatic external sending, legal enforceability, and guaranteed payment or recovery.

## 3. Safety invariants

1. Agents never contact an external platform or control a browser.
2. AI cannot sign or accept for the freelancer or client.
3. AI cannot infer project progress; milestone readiness and completion require a freelancer-recorded event.
4. Automation uses only the latest mutually accepted `ACTIVE` contract.
5. Scope-change detection pauses affected automation, creates a change request, and never promises extra work.
6. Routine auto-delivery is limited to the built-in demo inbox.
7. Delay, scope-change, payment, dispute, compensation, extension, legal, and contract-interpretation messages require freelancer approval.
8. Approval-only messages include `Draft only — review and send manually.`
9. Scheduler and delivery operations are idempotent.
10. Discussions and replies are untrusted data, never system instructions.
11. Agents make no legal enforceability, legal-rights, or guaranteed-payment claims.
12. Agents use narrowly filtered MCP tools and never access SQLite directly.
13. Every significant action and blocked attempt is append-only audited.
14. No secrets or real personal data enter the repository, demo, logs, or screenshots.

## 4. Architecture

```text
React + Vite Frontend
        ↓ HTTPS / REST
FastAPI Application
        ↓
Google ADK CoordinatorAgent
 ├── DiscussionAgent
 ├── ContractAgent
 ├── CommunicationAgent
 └── SafetyAuditAgent
        ↓ MCP over STDIO
freelance-project-mcp
        ↓
Domain Services
 ├── Contract Service
 ├── Signature Service
 ├── Milestone Service
 ├── Message Queue Service
 ├── Client Reply Service
 ├── Scope Change Service
 ├── Scheduler Service
 └── Audit Service
        ↓
SQLite Database
        ↓
Built-in Simulated Client Inbox
```

Use one Docker image: Node builds frontend assets; Python serves FastAPI and the SPA; the MCP server runs only as an internal STDIO child process; SQLite lives at `/app/data/freelance_shield.db` on a Compose volume. Do not publish an MCP port.

## 5. Technology and layering

Frontend: React, Vite, TypeScript strict mode, Tailwind CSS, React Router, TanStack Query, Zod, Vitest, and Playwright.

Backend: Python 3.11+, FastAPI, Pydantic, SQLModel or SQLAlchemy, Alembic, Google ADK, MCP Python SDK with FastMCP, Pytest, and httpx.

Layer rules:

| Layer | Owns | Must not own |
| --- | --- | --- |
| Frontend | Forms, workflow UI, inbox, board, trace display | Domain policy or fabricated traces |
| REST API | Validation, typed responses, safe errors | Persistence or scheduler rules |
| ADK agents | Extraction, wording, classification, safety review | Signature, progress, delivery, or database mutation outside MCP |
| MCP server | Approved typed workflow tools | Public HTTP or forbidden external actions |
| Services | Contract, signature, milestone, queue, reply, scope-change logic | UI state or prompt-only enforcement |
| Scheduler policy | Due-time, active-version, send-mode, pause, idempotency checks | LLM judgment for delivery authorization |
| Repositories | Database reads and writes | Product policy |

Use UUID primary keys, UTC timestamps, decimal-safe fee storage, migrations, and transactions that pair domain writes with audit events.

## 6. Persistence model

### Project

```text
id
title
client_name
source_platform
status
automation_enabled
created_at
updated_at
```

### AgreementVersion

```text
id
project_id
agreement_code
version_number
scope
deliverables_json
revision_limit
fee_amount
currency
payment_terms
effective_start_date
acceptance_status
created_at
activated_at
```

### SignatureRecord

```text
id
agreement_version_id
party_role                  # FREELANCER | CLIENT
signer_display_name
accepted_at
acceptance_text
status                      # PENDING | ACCEPTED
```

### Milestone

```text
id
project_id
agreement_version_id
title
description
due_at
status
completion_recorded_at
recorded_by
```

### ClientMessage

```text
id
project_id
agreement_version_id
milestone_id
message_type
body
send_mode                   # ROUTINE_AUTO | APPROVAL_REQUIRED
status
scheduled_for
delivered_at
idempotency_key             # UNIQUE
```

### ClientReply

```text
id
project_id
client_message_id
body
classification
possible_scope_change
received_at
```

### ScopeChangeRequest

```text
id
project_id
source_reply_id
summary
status                      # DETECTED | PENDING_REVIEW | ACCEPTED | REJECTED
proposed_contract_version_id
created_at
```

### AuditEvent

```text
id
project_id
actor
action
metadata_json
created_at
```

Audit events have no update or delete API/tool. Application-level append-only storage is not proof of external authenticity or legal admissibility.

## 7. State models and mandatory transitions

```text
Project:
DISCUSSION_CAPTURED → TERMS_REVIEW → CONTRACT_PENDING_SIGNATURE
→ ACTIVE → COMPLETED → CLOSED
ACTIVE → SCOPE_CHANGE_PENDING → ACTIVE
ACTIVE → PAUSED

AgreementVersion:
DRAFT → FREELANCER_ACCEPTED → CLIENT_ACCEPTED → ACTIVE
ACTIVE → SUPERSEDED

Milestone:
PLANNED → IN_PROGRESS → READY_FOR_REVIEW → COMPLETED
PLANNED / IN_PROGRESS → BLOCKED

ClientMessage:
DRAFT → QUEUED → DELIVERED_TO_DEMO_INBOX → ACKNOWLEDGED
DRAFT → APPROVAL_REQUIRED → APPROVED → QUEUED
```

Rules:

- Both signature roles must accept the same version before activation.
- Milestones cannot be created from an inactive contract.
- Only the latest active contract controls milestones and messages.
- V2 does not supersede V1 until V2 receives both acceptances.
- AI cannot update milestone progress.
- A possible scope change cannot alter scope directly.
- The idempotency key prevents duplicate queueing and delivery.

## 8. Agent architecture

### CoordinatorAgent

Routes typed operations to specialists, preserves context, and returns public trace events. It has no persistence or delivery tools.

### DiscussionAgent

Input: informal discussion, source platform, optional reference date.

Validated output includes project title, scope, deliverables, fee, currency, deadline, revision limit, payment terms, missing fields, and risk flags. It extracts only stated facts and flags ambiguity.

### ContractAgent

Uses freelancer-confirmed facts and an approved template to create a versioned contract containing scope, deliverables, milestones, revisions, fee, payment terms, scope-change procedure, and mutual acceptance wording. It never signs or claims enforceability.

### CommunicationAgent

1. Drafts routine milestone updates based on the active contract and recorded events.
2. Classifies replies as `ACKNOWLEDGEMENT`, `FEEDBACK`, `QUESTION`, `SCOPE_CHANGE`, or `CONCERN`.

It cannot record progress, promise extra scope, or deliver messages.

### SafetyAuditAgent

Checks contract version, recorded progress, message type, send mode, scope-change state, warning requirements, and unsafe wording. It blocks legal claims, threats, unsupported completion, scope promises, and automatic delivery of approval-only messages.

All agent inputs and outputs use Pydantic schemas. Production API workflow calls Google ADK; tests may use controlled model fakes. Missing model configuration fails safely without queueing or delivering a message.

## 9. MCP server

Internal name: `freelance-project-mcp`; transport: STDIO.

Approved tools:

```text
create_project_from_terms
save_discussion_facts
get_contract_template
create_contract_version
create_signature_request
record_signature_acceptance
get_latest_active_contract
create_milestones_from_contract
record_milestone_progress
get_due_communications
queue_routine_update
deliver_to_demo_inbox
record_client_reply
get_project_timeline
create_scope_change_request
pause_project_automation
evaluate_automation_policy
append_audit_log
```

Permission matrix:

| Agent | Allowed tools |
| --- | --- |
| `CoordinatorAgent` | No direct persistence tools |
| `DiscussionAgent` | `create_project_from_terms`, `save_discussion_facts`, `append_audit_log` |
| `ContractAgent` | `get_contract_template`, `create_contract_version`, `create_signature_request`, `append_audit_log` |
| `CommunicationAgent` | `get_latest_active_contract`, `get_due_communications`, `queue_routine_update`, `record_client_reply`, `create_scope_change_request`, `append_audit_log` |
| `SafetyAuditAgent` | `evaluate_automation_policy`, `append_audit_log` |

Trusted backend orchestration handles signature acceptance, milestone progress, scheduler execution, automation pause, and demo-inbox delivery. The scheduler alone calls `deliver_to_demo_inbox` after deterministic policy approval.

Forbidden tools include external send functions, browser control, signing on behalf of either party, payment collection, legal filing, and audit deletion.

## 10. Automation policy

Eligible routine messages:

```text
KICKOFF_CONFIRMATION
UPCOMING_MILESTONE_REMINDER
REVISION_WINDOW_REMINDER
DELIVERY_CONFIRMATION
INVOICE_AVAILABILITY_NOTICE
```

Every automatic delivery requires:

1. latest contract is `ACTIVE`;
2. both signature records match that version;
3. project automation is enabled and not affected by a scope-change pause;
4. required milestone or freelancer-recorded event exists;
5. message type is routine;
6. SafetyAuditAgent approves wording;
7. idempotency key does not already exist;
8. destination is the built-in demo inbox.

Approval-required messages never auto-deliver and carry the draft-only warning.

Expose a predictable scheduler trigger for tests and demos:

```text
POST /api/internal/run-scheduled-update-check
```

The periodic task and API trigger call the same scheduler service method.

## 11. REST API

Target endpoints:

```text
POST /api/discussions/analyse
POST /api/projects
POST /api/projects/{project_id}/contracts
POST /api/contracts/{contract_id}/acceptance
POST /api/projects/{project_id}/milestones/{milestone_id}/progress
POST /api/projects/{project_id}/scheduler/run
POST /api/internal/run-scheduled-update-check
POST /api/projects/{project_id}/client-replies
POST /api/projects/{project_id}/scope-changes
GET  /api/projects/{project_id}
GET  /api/projects/{project_id}/timeline
GET  /api/projects/{project_id}/messages
GET  /api/projects/{project_id}/audit
GET  /api/health
```

All public requests and responses use Pydantic models. Errors use stable codes and safe messages: `400`, `404`, `409`, `422`, and generic `500`. Policy blocks are successful workflow results with reason codes, not leaked exceptions.

## 12. Frontend

Preserve the command-center shell and visual tokens in `DESIGN.md`. Build six API-backed screens:

1. **Discussion Intake** — discussion, source, extracted terms, missing terms, fact review.
2. **Contract and Signatures** — FS code/version, contract terms, freelancer acceptance, simulated client acceptance, activation status.
3. **Project Board** — active version, milestones, due dates, progress controls, automation pause.
4. **Client Inbox** — delivered routine messages, simulated replies, classification, scope-change warning.
5. **Communication Centre** — queued, delivered, approval-required, blocked, and safety-reviewed messages.
6. **Timeline and Agent Trace** — contract, signatures, milestones, queue, delivery, replies, scope changes, ADK/MCP trace, and audit.

All visible approval-only drafts are copyable and show the draft warning. Routine demo-inbox messages show delivery state and do not imply external delivery. Timestamps remain UTC in storage and support a display-only GMT selector.

## 13. Test requirements

Required safety and integration tests:

```text
test_no_automation_before_mutual_acceptance
test_ai_cannot_mark_milestone_complete
test_scheduler_does_not_duplicate_message
test_scope_change_pauses_automation
test_contract_v2_requires_both_acceptances
test_delay_message_requires_freelancer_approval
test_dispute_reply_cannot_trigger_payment_reminder
test_prompt_injection_cannot_override_contract_or_send_policy
test_agent_tool_permissions_are_restricted
test_scheduler_and_agent_actions_are_audit_logged
test_no_external_send_or_signing_tools_exist
```

API integration covers the full corrected workflow. Playwright covers the browser story from discussion through V2 creation and audit display. A failed safety test is a hard blocker.

Quality commands:

```bash
cd backend
pytest
ruff check .

cd frontend
npm run lint
npm run test
npm run build
npm run test:e2e
```

## 14. Roadmap

### Milestone 0 — Corrected documentation

Revise all product, build, architecture, API, security, demo, agent, and design documents. Make no application-code changes. Commit: `docs: revise product as contract-driven communication agent`.

### Milestone 1 — Existing scaffold

Retain the React/FastAPI/Docker shell only where it fits the corrected design. Do not treat legacy evidence/payment workflow behavior as accepted product functionality.

### Milestone 2 — Contract, signature, milestone, and audit persistence

Implement the corrected models, migrations, repositories, transactions, state transitions, and service tests. Acceptance: mutual activation, inactive-contract milestone block, V2 supersession only after mutual acceptance, and audit on every write.

### Milestone 3 — `freelance-project-mcp`

Replace the legacy MCP surface with the approved typed tools. Acceptance: no direct agent database access, no external-send/signing tools, audited writes, clean stdout, and permission tests.

### Milestone 4 — ADK agent workflow

Implement `CoordinatorAgent`, `DiscussionAgent`, `ContractAgent`, `CommunicationAgent`, and `SafetyAuditAgent` with typed schemas and narrow toolsets. Acceptance: structured terms, contract from reviewed facts, routine messages tied to active agreement, and scope-change request without an automatic promise.

### Milestone 5 — Scheduler and automation policy

Implement the shared scheduler service, idempotency, pause checks, approval policy, queueing, and demo-inbox delivery. Running the scheduler twice must not duplicate a message.

### Milestone 6 — Workflow API

Implement the target routes, safe errors, project aggregates, messages, timeline, audit, and backend traces.

### Milestone 7 — Complete UI

Build and connect all six screens using real API state. Preserve responsive shell, safety context, enum labels, timezone display, and copy-only approval drafts.

### Milestone 8 — Security and tests

Complete backend safety tests, Vitest coverage, Playwright E2E, Ruff, ESLint, build, prompt-injection cases, forbidden-tool checks, and secret scan.

### Milestone 9 — Demo and submission

Finalize README, screenshots, synthetic seed/reset, Docker guide, known limitations, and video script showing discussion → V1 → mutual acceptance → milestones → demo-inbox update → scope change → V2 → audit.

## 15. Definition of done

Do not call the corrected product complete until:

- a fresh Docker build runs the full corrected browser workflow;
- the five named ADK agents are actively called;
- `freelance-project-mcp` is real, internal, and actively called;
- agent toolsets differ and contain no forbidden tools;
- contract activation and V2 supersession require mutual acceptance;
- milestone progress cannot be inferred by AI;
- scheduler policy and idempotency are deterministic;
- all automatic delivery stays inside the demo inbox;
- scope changes pause automation and require V2 review;
- approval-only messages remain drafts;
- all quality and E2E tests pass;
- documentation matches implementation;
- no secrets or real personal data exist in the repository or demo.

## 16. Execution rules

Work milestone by milestone. Do not scaffold later features early, skip safety tests, or preserve legacy payment-focused behavior merely because it already exists. Prefer deterministic code for signatures, states, scheduler policy, idempotency, delivery authorization, and audit. Stop and fix a failing safety check before proceeding.
