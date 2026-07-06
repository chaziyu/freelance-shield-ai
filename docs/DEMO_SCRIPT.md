# Demo Script

## Status and purpose

This is the acceptance script for the future MVP and uses synthetic data only. It is not executable in Milestone 0 because no application has been scaffolded.

Target duration: 5–7 minutes.

## Preconditions

- The application starts from a fresh clone with `docker compose up --build`.
- The browser UI and `GET /api/health` are available.
- The database is empty or reset to synthetic demo state.
- No real names, chats, invoices, contact details, or credentials appear on screen.

## Synthetic fixtures

Platform: `Instagram`

Client chat:

```text
Need a poster by Friday. RM800. Two revisions.
```

Acceptance response:

```text
I agree to Agreement FS-001 Version 1.
```

Dispute message:

```text
The poster is incomplete. I will not pay.
```

Use a presenter-supplied future calendar date for the deadline because “Friday” alone is relative and must not be guessed. Use a synthetic invoice due date when recording the invoice.

## Walkthrough

### 1. Intake

1. Open **New Project**.
2. Select `Instagram`.
3. Paste the client chat and choose **Analyse Deal**.
4. Show the extracted facts and agent trace.

Expected:

- title describes poster design;
- amount is `800` and currency is `MYR`;
- revision limit is `2`;
- normalized deadline and payment terms are unresolved;
- the informal-platform risk is visible;
- trace names `CoordinatorAgent`, `IntakeAgent`, and actual MCP calls;
- the chat is treated as data, not instructions.

### 2. Agreement

1. Supply a synthetic absolute deadline and payment terms.
2. Create the agreement.
3. Show Agreement `FS-001` Version `1`, its terms, and acceptance status.
4. Copy or display the generated acceptance request.

Expected:

```text
Please reply: “I agree to Agreement FS-001 Version 1.”
```

The page must not claim that the agreement is legally binding or enforceable.

### 3. Acceptance

1. Simulate the exact acceptance response.
2. Show status `ACCEPTED` and the acceptance evidence event.

Expected: the code and version match, the event has a UTC timestamp and content hash, and both the workflow action and MCP call appear in the audit trail.

Optional negative check: submit acceptance for Version `2`. Expected: safe conflict response, no acceptance state change, and an audited rejection.

### 4. Delivery and invoice evidence

1. Record synthetic delivery evidence.
2. Record a synthetic invoice and due date.
3. Show both on the chronological timeline.

Expected: evidence summaries and hashes are visible without any claim that hashes prove authorship, ownership, or legal admissibility.

### 5. Dispute safety path

1. Choose **Simulate Client Dispute**.
2. Enter the dispute fixture.
3. Request a follow-up draft.

Expected:

- project state becomes `DISPUTED` and `dispute_flag` is true;
- deterministic policy permits only `DISPUTE_CLARIFICATION`;
- a payment reminder or demand is blocked;
- `SafetyAuditAgent` reviews the neutral clarification;
- the visible draft contains `Draft only — review and send manually.`;
- no message is sent and the only user action is copy/manual review.

### 6. Audit trace

Open the trace and audit view.

Expected sequence:

```text
CoordinatorAgent
→ IntakeAgent
→ MCP project/facts calls
→ AgreementAgent
→ MCP agreement call
→ trusted acceptance and evidence workflow calls
→ FollowUpAgent
→ deterministic dispute policy result
→ SafetyAuditAgent
→ approved clarification or audited block
```

Show audit events for agreement creation, acceptance, evidence, policy decision, tool calls, draft creation, and safety result. The UI trace must originate from backend data.

## Pass criteria

- The complete path works without database edits or refresh workarounds.
- No missing fact is invented.
- Acceptance requires the exact current code and version.
- The dispute blocks demand-style content.
- Every shown communication carries the draft-only warning.
- No send, browser, payment, legal, or complaint action exists.
- Timeline, policy decision, agent trace, and append-only audit events are visible.
- No secret or real personal data appears in UI, logs, screenshots, or recordings.

## Optional scope-change check

After acceptance, change the deliverable scope. Expected: Agreement `FS-001` Version `2` is created, Version `1` remains unchanged, and current acceptance returns to `PENDING` until the exact Version `2` response is recorded.
