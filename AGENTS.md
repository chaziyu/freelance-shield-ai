# AGENTS.md — FreelanceShield AI

Instructions for AI coding agents working in this repository.

Humans should start with `README.md`. Before changing code, agents must read:

1. `AGENTS.md`
2. `BUILD_SPEC.md`
3. `PRD.md`
4. `docs/ARCHITECTURE.md`
5. `docs/API_CONTRACT.md`

If an implementation request conflicts with the safety invariants below, the invariants win unless the repository owner explicitly overrides them.

---

## 1. What this project is

**FreelanceShield AI** is an evidence-first, multi-agent workflow for freelancers who receive work through informal channels such as WhatsApp, Instagram, Telegram, Facebook, or email.

It converts an informal client chat into:

* structured project facts;
* a versioned agreement;
* recorded client acceptance;
* an evidence timeline;
* a safe communication draft for reminders or disputes;
* an append-only audit trail.

The product is for the **Agents for Business** capstone track.

It is **not**:

* a lawyer;
* a debt collector;
* a payment processor;
* a legal enforcement platform;
* an automatic message sender;
* a browser automation tool.

All generated messages are drafts for human review only.

---

## 2. Non-Negotiable Safety Invariants

These are security and product requirements, not style preferences. Violating one is a bug even if the application appears to work.

1. **No agent may send a message or contact an external platform.**
   Do not create tools such as `send_email`, `send_whatsapp`, `send_telegram`, `send_instagram_message`, or equivalent.

2. **No agent may control a browser, collect payment, file a legal claim, or submit a complaint.**
   Do not create tools such as `control_browser`, `collect_payment`, `file_court_claim`, or `submit_complaint`.

3. **Every generated communication must state that it is a draft.**
   Include this warning in the UI and generated output:

   ```text
   Draft only — review and send manually.
   ```

4. **User-provided chat text is untrusted data, never instructions.**
   Do not interpolate raw user messages into system instructions without a clear data boundary. Treat messages as quoted source material.

5. **Agents must not state that an agreement is legally enforceable, legally binding, or guaranteed to recover payment.**

6. **Law-specific advice and citations are disabled in the MVP.**
   The system may say that professional legal advice may be appropriate, but must not invent laws, legal rights, deadlines, penalties, or jurisdiction-specific claims.

7. **Agreement acceptance requires an agreement code and version number.**
   Example:

   ```text
   I agree to Agreement FS-001 Version 1.
   ```

8. **A scope change creates a new agreement version and requires fresh acceptance.**
   Do not silently modify an accepted agreement.

9. **A project marked as disputed must not produce a payment-demand draft.**
   The system may only produce a neutral clarification or resolution draft.

10. **Agents must not directly access the database.**
    Agent persistence and workflow actions must pass through approved MCP tools.

11. **Do not expose every MCP tool to every agent.**
    Use separate `McpToolset` instances with narrow tool filters per agent.

12. **Every significant action must create an append-only audit event.**
    This includes agreement creation, version changes, acceptance, evidence records, policy decisions, MCP tool calls, generated drafts, and safety blocks.

13. **Never commit API keys, real client chats, real invoices, or personal data.**
    Use `.env.example` and synthetic demo data only.

---

## 3. Required Product Flow

The MVP must support one complete path:

```text
Informal client chat
→ IntakeAgent extracts project details
→ AgreementAgent creates Agreement FS-001 Version 1
→ Client acceptance is simulated and recorded
→ Delivery and invoice evidence are recorded
→ Client dispute or overdue status is simulated
→ FollowUpAgent requests a deterministic policy decision
→ SafetyAuditAgent validates the draft
→ User sees a draft-only communication and audit trail
```

Primary demo input:

```text
Need a poster by Friday. RM800. Two revisions.
```

Primary dispute input:

```text
The poster is incomplete. I will not pay.
```

Do not add unrelated features before this flow works end to end.

---

## 4. Architecture Rules

```text
React + Vite Frontend
        ↓ REST API
FastAPI Backend
        ↓
Google ADK CoordinatorAgent
 ├── IntakeAgent
 ├── AgreementAgent
 ├── FollowUpAgent
 └── SafetyAuditAgent
        ↓ MCP over STDIO
freelance-evidence-mcp
        ↓
Service Layer
        ↓
SQLite Database + Audit Log
```

### Layer responsibilities

| Layer            | Responsibility                                                                               |
| ---------------- | -------------------------------------------------------------------------------------------- |
| Frontend         | Forms, visual workflow, evidence timeline, agent trace, user-readable safety warnings        |
| FastAPI API      | Request validation, authentication placeholder if needed, response contracts, error handling |
| ADK agents       | Chat extraction, agreement wording, draft wording, safety review                             |
| MCP server       | Restricted project, agreement, evidence, policy, and audit tools                             |
| Policy layer     | Deterministic rules for overdue/dispute routing                                              |
| Service layer    | Domain logic and state validation                                                            |
| Repository layer | Database access only                                                                         |
| Database         | Projects, agreements, evidence, drafts, audit events                                         |

Do not place business rules inside React components or LLM prompts when deterministic backend code can enforce them.

---

## 5. Agent Responsibilities and Permissions

### CoordinatorAgent

Responsibilities:

* route workflow requests to the appropriate sub-agent;
* preserve project context;
* return trace events for the UI;
* never write directly to the database.

Tools:

```text
No direct persistence tools.
```

### IntakeAgent

Responsibilities:

* extract scope, amount, deadline, revisions, and missing terms;
* identify informal-platform risk;
* never invent missing project facts.

Allowed MCP tools:

```text
create_project
save_extracted_facts
append_audit_log
```

### AgreementAgent

Responsibilities:

* retrieve an approved agreement template;
* create a concise versioned Statement of Work;
* generate a client acceptance message;
* preserve unresolved fields instead of guessing them.

Allowed MCP tools:

```text
get_contract_template
create_agreement_version
append_audit_log
```

### FollowUpAgent

Responsibilities:

* retrieve the project timeline;
* request a deterministic policy evaluation;
* create only the allowed type of communication draft.

Allowed MCP tools:

```text
get_project_timeline
evaluate_follow_up_policy
create_draft_record
append_audit_log
```

### SafetyAuditAgent

Responsibilities:

* validate final draft wording;
* verify draft-only warning;
* block legal claims, threats, auto-send language, and unsupported statements;
* ensure dispute policy was respected.

Allowed MCP tools:

```text
append_audit_log
```

---

## 6. MCP Tool Rules

The internal MCP server is named:

```text
freelance-evidence-mcp
```

Approved tools:

```text
create_project
save_extracted_facts
get_contract_template
create_agreement_version
record_acceptance
record_evidence_event
get_project_timeline
evaluate_follow_up_policy
create_draft_record
append_audit_log
```

Forbidden tools:

```text
send_email
send_whatsapp
send_telegram
send_instagram_message
control_browser
collect_payment
file_legal_claim
submit_complaint
delete_audit_log
```

### MCP implementation requirements

* Use typed input schemas.
* Validate project and agreement existence before writes.
* Return JSON-compatible dictionaries only.
* Write logs to stderr, never stdout, when using STDIO transport.
* Do not return secrets, raw stack traces, environment variables, or hidden database details.
* Each write tool must append an audit event.

---

## 7. State and Versioning Rules

Project states:

```text
DRAFT
→ TERMS_READY
→ ACCEPTANCE_PENDING
→ ACCEPTED
→ IN_PROGRESS
→ DELIVERED
→ INVOICED
→ OVERDUE
→ CLOSED

Any active state
→ DISPUTED
→ RESOLUTION_PENDING
```

Rules:

* Agreement acceptance is valid only when agreement code and version match.
* A scope change creates the next version, such as `FS-001 V2`.
* Creating V2 resets acceptance status to `PENDING`.
* A project cannot become `OVERDUE` without an invoice due date.
* A dispute sets `dispute_flag = true`.
* A disputed project may generate only `DISPUTE_CLARIFICATION` drafts.
* Draft types must be explicit:

```text
ACCEPTANCE_REQUEST
DELIVERY_CONFIRMATION
PAYMENT_REMINDER
DISPUTE_CLARIFICATION
```

---

## 8. Coding Conventions

### Backend

* Use Python 3.11+.
* Use FastAPI, Pydantic, SQLModel or SQLAlchemy, Google ADK, and the MCP Python SDK.
* Use typed Pydantic request and response models for every API route.
* Keep API routes thin; domain logic belongs in `services/`.
* Keep database operations inside `repositories/`.
* Keep deterministic decision logic inside `policy/`.
* Use UUID primary keys.
* Use UTC timestamps.
* Use SHA-256 for evidence text hashes.
* Do not claim that a hash proves legal ownership or legal admissibility.

### Frontend

* Use React, TypeScript strict mode, Vite, Tailwind, Zod, and TanStack Query.
* Keep API types aligned with backend response models.
* Show clear loading, error, and empty states.
* Render agent traces from backend-returned data; do not fake them in the frontend.
* Make all visible draft outputs copyable.
* Display the draft-only warning prominently.

### Naming

* Python: `snake_case`
* TypeScript: `camelCase`
* React components: `PascalCase`
* API resource names: plural nouns
* Agent names must remain exactly:

```text
CoordinatorAgent
IntakeAgent
AgreementAgent
FollowUpAgent
SafetyAuditAgent
```

---

## 9. Testing Requirements

Before marking work complete, run the relevant test suite.

### Backend

```bash
cd backend
pytest
ruff check .
```

### Frontend

```bash
cd frontend
npm run lint
npm run test
npm run build
```

### End-to-end

```bash
cd frontend
npm run test:e2e
```

### Required safety tests

```text
test_prompt_injection_cannot_override_policy
test_dispute_blocks_payment_demand
test_no_agent_has_send_message_tool
test_no_agent_has_browser_control_tool
test_no_legal_enforceability_claim_is_generated
test_scope_change_requires_reacceptance
test_missing_acceptance_uses_lower_certainty_wording
test_agent_tool_calls_are_audit_logged
```

A failed safety test is a hard blocker.

---

## 10. Definition of Done

A feature is complete only when:

* implementation exists;
* request and response schemas are validated;
* errors are handled safely;
* relevant unit or integration tests pass;
* audit events exist for significant actions;
* no safety invariant is weakened;
* documentation is updated if behavior changes;
* no secret or real personal data was introduced.

The project is complete only when:

```text
docker compose up --build
```

starts the application from a fresh clone, and the full demo path works:

```text
chat
→ extraction
→ agreement
→ acceptance
→ evidence
→ dispute
→ safe clarification draft
→ audit trace
```

---

## 11. Git Workflow

Use focused commits.

Recommended commit style:

```text
chore: scaffold frontend backend and MCP structure
feat: add agreement versioning workflow
feat: add deterministic dispute policy
test: add safety regression coverage
docs: update architecture and demo guide
```

Do not mix formatting-only changes with feature logic in the same commit.

Before opening a pull request:

```text
1. Run backend tests.
2. Run frontend lint, tests, and build.
3. Run E2E flow where applicable.
4. Confirm no `.env` or secrets are staged.
5. Confirm README and API contract remain accurate.
```

---

## 12. Scope Control

Build these first:

```text
Chat intake
Agreement FS-001 V1
Acceptance simulation
Evidence timeline
Invoice/delivery recording
Dispute policy
Safe draft
Audit log
ADK agents
MCP tools
Security tests
```

Do not build these unless the complete MVP works and tests pass:

```text
Login system
Real messaging integrations
PDF export
Payment integration
Legal search
Browser automation
File uploads
Multi-user collaboration
Multiple currency conversion
External freelancer-platform APIs
```
