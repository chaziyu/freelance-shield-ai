# Product Requirements Document

## 1. Product summary

FreelanceShield AI is an evidence-first workflow for freelancers whose project terms arrive through informal channels such as WhatsApp, Instagram, Telegram, Facebook, or email. It structures only the facts a user provides, creates versioned agreement text, records simulated client acceptance and project evidence, and produces safety-reviewed communication drafts for manual sending.

This document defines the MVP. Current repository status is Milestone 0: documentation only.

## 2. Problem

Informal conversations can leave scope, fee, due date, revision limits, payment terms, and acceptance unclear. Freelancers need a consistent way to preserve what was stated, identify what is missing, obtain explicit versioned acceptance, and communicate neutrally when delivery or payment is disputed.

The product must help organize records without claiming to determine legal rights, create enforceable contracts, prove ownership, recover money, or act on the user's behalf.

## 3. Users and jobs

Primary user: an individual freelancer managing one project at a time in the MVP.

Core jobs:

1. Extract stated project terms from an informal chat without inventing missing facts.
2. Review and complete a concise Statement of Work.
3. Request and record acceptance of an exact agreement code and version.
4. Record delivery, invoice, acceptance, and scope-change evidence.
5. Determine whether an acceptance request, confirmation, friendly reminder, or dispute clarification is permitted.
6. Copy a clearly labeled draft for manual review and sending.
7. Inspect the project timeline, agent trace, and append-only audit trail.

## 4. Goals

- Complete the required demo path end to end with synthetic data.
- Make unresolved terms visible instead of guessing them.
- Make agreement versions and acceptance state explicit.
- Enforce dispute routing with deterministic backend policy.
- Keep agent permissions narrow and persistence behind approved MCP tools.
- Make every significant workflow action auditable.
- Present safety boundaries clearly in generated text and the UI.

## 5. Non-goals

- Real message sending or external-platform contact.
- Browser automation.
- Payment processing or debt collection.
- Legal research, advice, citations, filing, or enforceability decisions.
- Authentication, multi-user collaboration, external platform APIs, file uploads, currency conversion, or PDF signatures.

## 6. Required workflow

1. The user enters synthetic client chat and selects its source platform.
2. `IntakeAgent` returns structured facts, missing fields, and risk flags.
3. The user reviews the facts and creates Agreement `FS-001` Version `1`.
4. The system provides the exact acceptance request: `Please reply: “I agree to Agreement FS-001 Version 1.”`
5. The user simulates the matching client response and the system records acceptance evidence.
6. The user records delivery and invoice evidence.
7. The user simulates either an overdue invoice or a client dispute.
8. `FollowUpAgent` requests a deterministic policy decision before drafting.
9. `SafetyAuditAgent` approves safe content for display or blocks it with reasons.
10. The UI shows the draft, mandatory warning, timeline, agent trace, and audit events.

Primary intake fixture:

```text
Need a poster by Friday. RM800. Two revisions.
```

Because “Friday” is relative without a reference date, the demo must leave the normalized deadline unresolved until the user supplies a date. The expected extracted amount is `800`, currency is `MYR`, revision limit is `2`, and payment terms remain unresolved.

Primary dispute fixture:

```text
The poster is incomplete. I will not pay.
```

This must set the dispute path and permit only a neutral `DISPUTE_CLARIFICATION` draft.

## 7. Functional requirements

### Intake

- Accept chat text and a supported source-platform label.
- Treat chat as untrusted quoted data.
- Extract project title, amount, currency, deadline, revision limit, payment terms, missing fields, and risk flags into a validated schema.
- Never infer a fact not stated in the source or supplied by the user.

### Agreements and acceptance

- Generate a concise Statement of Work from an approved template.
- Assign a stable agreement code and monotonically increasing version number.
- Preserve unresolved fields visibly.
- Validate acceptance against both the agreement code and version.
- Create a new version and reset acceptance to `PENDING` after a scope change.

### Evidence and audit

- Record acceptance, delivery, invoice, and scope-change evidence with UTC timestamps and SHA-256 content hashes.
- Display events chronologically.
- Append an audit event for each significant action, policy decision, MCP call, generated draft, and safety block.
- Do not expose an audit deletion operation.

### Follow-up policy and drafts

- Evaluate deterministic policy before generating any draft.
- Route no accepted agreement to `ACCEPTANCE_REQUEST`.
- Route accepted but not-due work to `DELIVERY_CONFIRMATION` when appropriate.
- Route overdue, undisputed invoices to `PAYMENT_REMINDER`.
- Route any dispute to `DISPUTE_CLARIFICATION` and block demand wording.
- Store a draft only after safety approval.
- Include `Draft only — review and send manually.` in every generated communication.

### Traceability

- Return actual backend trace events; the frontend must not fabricate them.
- Identify agent, action, status, timestamp, and safe public metadata without exposing prompts, secrets, stack traces, or hidden database details.

## 8. State model

```text
DRAFT → TERMS_READY → ACCEPTANCE_PENDING → ACCEPTED → IN_PROGRESS
→ DELIVERED → INVOICED → OVERDUE → CLOSED

Any active state → DISPUTED → RESOLUTION_PENDING
```

Constraints:

- Acceptance is allowed only from `TERMS_READY` or `ACCEPTANCE_PENDING` and only for the current code and version.
- `OVERDUE` requires an invoice due date.
- A dispute sets `dispute_flag = true` and overrides reminder routing.
- A new agreement version requires fresh acceptance.

## 9. Safety requirements

The invariants in `AGENTS.md` are release blockers. In particular, no agent can send, browse, collect, file, or submit; user content cannot alter policy; disputed work cannot produce a payment demand; law-specific content is disabled; and no agent receives broad database or MCP access.

Evidence hashing is an integrity aid only. It does not prove who authored content, when an external event happened, whether the content is authentic, or whether it is legally admissible.

## 10. User experience requirements

- Responsive pages for intake, agreement, evidence, follow-up, and trace/audit.
- Clear loading, error, empty, blocked, unresolved, and accepted states.
- Copy controls for agreement acceptance text and all visible drafts.
- Prominent draft-only warning adjacent to every draft.
- Human-readable policy reasons and safety blocks.
- No control or wording that implies automatic sending.

## 11. Success and acceptance criteria

The MVP succeeds when a fresh clone can run with Docker Compose and a user can complete the synthetic demo without manual database edits or refresh workarounds. Automated checks must prove:

- prompt injection cannot override policy;
- disputes block payment-demand drafts;
- no agent has send-message or browser-control tools;
- no legal enforceability claim is generated;
- scope changes require reacceptance;
- missing acceptance produces lower-certainty wording;
- every agent tool call is audit logged.

All backend, frontend, safety, integration, and browser tests defined in `AGENTS.md` and `BUILD_SPEC.md` must pass before the project is called complete.

## 12. Assumptions and open decisions

- Initial deployment is single-user and local; authentication is intentionally out of scope.
- The display timezone is not yet chosen; persisted timestamps will be UTC.
- “High value” and “cross-border” policy thresholds are not yet defined. Until defined, they must not trigger numeric or jurisdiction-specific claims.
- The exact Google ADK model and production hosting environment are not yet selected.
- Team names and attribution are pending.
