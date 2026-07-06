# Product Requirements Document

## 1. Product summary

FreelanceShield AI converts informal freelance discussions into a reviewed, mutually accepted contract and then uses the latest active contract as the source of truth for project communication.

The MVP supports two stages:

```text
Stage 1: informal discussion → reviewed terms → contract → mutual acceptance
Stage 2: active contract → milestones → routine updates → client replies
         → scope-change detection → Contract V2 when needed
```

Documentation now defines this corrected product. The current application still implements the earlier evidence/payment-follow-up workflow and must be migrated milestone by milestone; it must not be presented as satisfying this PRD yet.

## 2. Problem

Freelancers often agree on work through informal chat. Terms remain ambiguous, project updates are repetitive, and client replies can introduce extra scope without a clear versioned decision. Freelancers need a workflow that:

1. structures only the terms actually discussed;
2. records separate acceptance by both parties;
3. derives milestones and communication from the active contract;
4. automates only safe routine updates;
5. pauses when a possible scope change appears;
6. creates a new contract version rather than silently expanding work.

The product does not determine legal rights, create legally enforceable contracts, sign for either party, collect payment, or contact external messaging platforms.

## 3. Primary user and jobs

Primary user: an individual freelancer managing one project at a time in the MVP.

Core jobs:

1. Extract scope, deliverables, fee, deadline, revisions, payment terms, and missing fields from an informal discussion.
2. Review and edit extracted facts before contract generation.
3. Create Contract `FS-001` Version `1` from confirmed terms.
4. Record separate freelancer and simulated-client acceptance.
5. Activate the contract only when both accept the same version.
6. Create and manage milestones from the active contract.
7. Deliver safe routine updates to a built-in demo inbox without repeated manual work.
8. Record and classify simulated client replies.
9. Detect possible scope changes, pause affected automation, and create Contract V2.
10. Inspect the complete timeline, agent trace, queue state, and audit trail.

## 4. Goals

- Complete the synthetic contract-to-scope-change story end to end.
- Keep missing or ambiguous terms visible instead of guessing.
- Make mutual acceptance and active contract version explicit.
- Prevent AI from inventing progress or accepting extra work.
- Automate only deterministic, contract-backed routine messages.
- Keep all delivery inside the built-in demo client inbox.
- Make scheduler execution idempotent and auditable.
- Enforce narrow agent tool permissions through the internal MCP server.
- Preserve the command-center visual system described in `DESIGN.md`.

## 5. Non-goals

- WhatsApp, email, Telegram, Instagram, or other external delivery.
- Real e-signature providers or external client accounts.
- Signing on behalf of either party.
- Payment processing, debt collection, or legal enforcement.
- Legal advice, citations, enforceability claims, court filing, or complaint submission.
- Authentication, multi-user collaboration, file uploads, PDF signature workflows, currency conversion, or external freelancer-platform APIs.

## 6. Required workflow

1. The freelancer pastes a synthetic client discussion and selects its source platform.
2. `DiscussionAgent` extracts stated terms, missing fields, and ambiguity.
3. The freelancer reviews and edits those facts.
4. `ContractAgent` creates Contract `FS-001` Version `1` with milestones and a scope-change procedure.
5. The freelancer explicitly accepts V1.
6. The simulated client explicitly accepts V1 on a built-in signing screen.
7. Deterministic services activate V1, create milestones, and enable automation.
8. The freelancer records milestone progress, such as **Mark first draft ready**.
9. The scheduler finds the resulting due routine communication, verifies policy and idempotency, queues it, and delivers it to the built-in demo inbox.
10. The simulated client submits a reply.
11. `CommunicationAgent` classifies the reply.
12. A possible scope change creates a `ScopeChangeRequest`, pauses affected automation, and causes `ContractAgent` to create V2.
13. V1 remains the latest active contract until freelancer and client both accept V2.
14. The UI shows the complete timeline and audit trace.

Primary discussion fixture:

```text
Need a poster by Friday. RM800. Two revisions.
```

Expected facts: amount `800`, currency `MYR`, revision limit `2`, unresolved normalized deadline unless a reference date is supplied, unresolved payment terms, and no invented deliverables.

Primary scope-change reply:

```text
Can you also make an Instagram Story version using the same design?
```

Expected result: classification `SCOPE_CHANGE`, affected automation paused, change request created, no promise of extra work, and proposed Contract V2 requiring both acceptances.

## 7. Functional requirements

### Discussion and review

- Discussion text is bounded, typed, and treated as untrusted quoted data.
- Output includes project title, scope, deliverables, fee, currency, deadline, revision limit, payment terms, missing fields, and risk flags.
- Relative dates remain unresolved without a supplied reference date.
- The freelancer can edit facts before contract generation.
- Agents never invent missing facts.

### Contract and signatures

- The backend assigns a stable code and monotonically increasing version.
- Contracts contain scope, deliverables, milestones, revision limit, fee, payment terms, scope-change procedure, and mutual acceptance wording.
- Freelancer and client acceptance are distinct records tied to the exact version.
- AI cannot create either signature record.
- A contract becomes `ACTIVE` only after both records are accepted.
- A newer version supersedes the old version only after both parties accept it.

### Milestones and progress

- Milestones come only from the latest active contract.
- AI may propose milestone definitions but cannot change milestone progress.
- Only a freelancer action can record `READY_FOR_REVIEW` or `COMPLETED`.
- Progress events store UTC timestamps, actor, contract version, and audit metadata.

### Communication automation

Routine automatic message types:

```text
KICKOFF_CONFIRMATION
UPCOMING_MILESTONE_REMINDER
REVISION_WINDOW_REMINDER
DELIVERY_CONFIRMATION
INVOICE_AVAILABILITY_NOTICE
```

They are eligible only when supported by the active contract and recorded project state. Delivery confirmation requires a freelancer-recorded delivery event; invoice availability requires a freelancer-recorded invoice event.

Approval-required types include delay, scope change, payment reminder, dispute response, apology, compensation, deadline extension, legal wording, or agreement interpretation. These remain drafts and include:

```text
Draft only — review and send manually.
```

The scheduler, not an agent, delivers approved routine messages only to the demo inbox. Its idempotency key covers project, active contract version, milestone, message type, and scheduled event.

### Client replies and scope changes

- A simulated inbox reply is classified as `ACKNOWLEDGEMENT`, `FEEDBACK`, `QUESTION`, `SCOPE_CHANGE`, or `CONCERN`.
- Classification does not mutate contract scope.
- `SCOPE_CHANGE` creates a reviewable request and pauses affected automation.
- A rejected change resumes the existing active contract workflow.
- An accepted change creates V2 and requires renewed mutual acceptance.

### Traceability and audit

- Frontend traces come from backend ADK and MCP events; the frontend does not fabricate them.
- Every contract, signature, milestone, policy, scheduler, queue, delivery, reply, scope change, safety decision, and MCP call creates an append-only audit event.
- Public metadata is allowlisted and never exposes prompts, secrets, database paths, environment values, or stack traces.

## 8. State models

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

## 9. Safety requirements

The invariants in `AGENTS.md` are release blockers. In particular:

- AI cannot sign, infer progress, or silently accept extra scope.
- Automation uses only the latest mutually accepted active contract.
- Scope changes pause affected automation.
- Routine auto-delivery is internal-demo-inbox only.
- Approval-only messages never auto-deliver.
- Prompt injection cannot widen tools, change policy, or cause delivery.
- No legal enforceability, payment guarantee, or external-send claim is allowed.

## 10. User experience

The responsive command center contains six workflow screens:

1. Discussion Intake
2. Contract and Signatures
3. Project Board
4. Client Inbox
5. Communication Centre
6. Timeline and Agent Trace

The UI shows loading, error, empty, paused, approval-required, delivered, and scope-change states. It pairs exact backend enum chips with human labels, renders UTC timestamps using a user-selected GMT offset, and never changes stored UTC values.

## 11. Success criteria

The MVP succeeds when a fresh Docker run completes the synthetic workflow without database edits or external messaging. Automated checks prove:

1. no automation before mutual acceptance;
2. AI cannot mark a milestone complete;
3. scheduler reruns do not duplicate messages;
4. scope changes pause automation;
5. V2 requires both acceptances;
6. delay and other non-routine messages require approval;
7. dispute replies cannot trigger payment reminders;
8. prompt injection cannot override contract or delivery policy;
9. agent MCP permissions are narrow;
10. every scheduler and agent action is audit logged.

## 12. Assumptions and open decisions

- The MVP is local, single-user, and synthetic-data only.
- The simulated client inbox and signing page are application views, not external accounts.
- Production messaging integrations, authentication, retention, and hosting remain deferred.
- The exact Google ADK model remains configurable.
- Team attribution is pending.
