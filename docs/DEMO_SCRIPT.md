# Demo Script

## Status and purpose

This is the target acceptance script for the corrected MVP and uses synthetic data only. The current application still requires migration from the retired evidence/payment-follow-up workflow before this script can pass.

Target duration: 6–8 minutes.

## Preconditions

- A fresh `docker compose up --build` starts the application.
- The browser UI and `GET /api/health` are available.
- Google model configuration is present.
- The synthetic demo database is empty or reset.
- No real names, discussions, contact details, contracts, signatures, invoices, credentials, or personal data appear.

## Synthetic fixtures

Platform: `Instagram`

Discussion:

```text
Need a poster by Friday. RM800. Two revisions.
```

Freelancer acceptance:

```text
I accept Contract FS-001 Version 1 as the freelancer.
```

Simulated client acceptance:

```text
I accept Contract FS-001 Version 1 as the client.
```

Scope-change reply:

```text
Can you also make an Instagram Story version using the same design?
```

Use presenter-supplied future UTC milestone dates. “Friday” alone remains unresolved until reviewed; the system must not guess it.

## Walkthrough

### 1. Discussion intake

1. Open **Discussion Intake**.
2. Select `Instagram`.
3. Paste the discussion and choose **Analyse discussion**.
4. Show extracted terms and the ADK/MCP trace.

Expected:

- `DiscussionAgent` extracts poster scope, `MYR 800`, and two revisions;
- deadline and payment terms are unresolved;
- deliverables are not invented;
- the informal-platform risk is visible;
- injected instructions would remain inert data;
- trace names `CoordinatorAgent`, `DiscussionAgent`, and actual MCP calls.

### 2. Review terms and create V1

1. Add a synthetic absolute deadline, payment terms, and two milestones:
   - First draft;
   - Final files.
2. Review the facts.
3. Create Contract `FS-001` Version `1`.

Expected:

- `ContractAgent` uses only reviewed facts and the approved template;
- V1 shows scope, deliverables, milestones, revision limit, fee, payment terms, scope-change procedure, and mutual acceptance wording;
- no legal enforceability claim appears;
- project state is `CONTRACT_PENDING_SIGNATURE`;
- no milestone automation is enabled yet.

### 3. Mutual acceptance

1. Click **Accept as freelancer** and confirm the exact freelancer text.
2. Open the built-in simulated client signing view.
3. Click **Accept as client** and confirm the exact client text.

Expected:

- separate `SignatureRecord` rows exist for `FREELANCER` and `CLIENT`;
- AI did not create either record;
- after the first acceptance, V1 remains inactive;
- after the second matching acceptance, V1 becomes `ACTIVE`;
- milestones are created and automation is enabled;
- all transitions are audited.

Optional negative check: try Version `2` acceptance before V2 exists. Expected: `409`, no state change, audited rejection.

### 4. Record milestone progress

1. Open **Project Board**.
2. Show the active contract version and planned milestones.
3. Click **Mark first draft ready**.

Expected:

- the freelancer action records `READY_FOR_REVIEW` with a UTC timestamp;
- no AI agent marks the milestone ready;
- the event makes a delivery confirmation eligible;
- the message is not yet duplicated or externally sent.

### 5. Run routine automation

1. Trigger the project scheduler or internal scheduled-update check.
2. Open **Communication Centre**.
3. Open **Client Inbox**.

Expected:

- scheduler verifies V1 is the latest active mutually accepted contract;
- automation is enabled and no scope-change pause exists;
- the recorded milestone event supports the message;
- `SafetyAuditAgent` approves the routine wording;
- one idempotent `DELIVERY_CONFIRMATION` is queued;
- it is delivered only to the built-in demo inbox;
- the UI states production channel integrations are deferred.

Run the scheduler again. Expected: zero duplicate messages and an audited duplicate skip.

### 6. Record and classify the client reply

1. In **Client Inbox**, choose **Reply as demo client**.
2. Enter the scope-change fixture.
3. Submit the reply.

Expected:

- `CommunicationAgent` classifies it as `SCOPE_CHANGE`;
- reply text is treated as untrusted data;
- a `ScopeChangeRequest` is created;
- affected automation pauses;
- no extra work is promised or added to V1;
- no automatic scope-change response is delivered.

### 7. Create Contract V2

1. Review the detected change request.
2. Accept the proposed change for contract drafting.
3. Show Contract `FS-001` Version `2` with the added Story adaptation.

Expected:

- V2 is immutable and pending both signatures;
- V1 remains the latest active contract until V2 mutual acceptance;
- affected automation remains paused;
- freelancer and client must separately accept exact V2 wording;
- after both accept, V2 becomes active and V1 becomes `SUPERSEDED`.

### 8. Timeline and audit

Open **Timeline and Agent Trace**.

Expected sequence:

```text
discussion analysed
→ reviewed project created
→ Contract FS-001 V1 created
→ freelancer accepted V1
→ client accepted V1
→ V1 activated
→ milestones created
→ freelancer marked first draft ready
→ routine update queued
→ delivered to demo inbox
→ duplicate scheduler run skipped
→ client reply recorded
→ reply classified as scope change
→ automation paused
→ scope-change request created
→ Contract V2 created
→ V2 acceptance pending
```

Show real backend ADK/MCP traces and append-only audit events without raw prompts, secrets, database paths, or stack traces.

## Pass criteria

- The complete story works without manual database edits or refresh workarounds.
- No missing fact, signature, or progress is invented.
- Contract activation and V2 supersession require both exact acceptances.
- Scheduler reruns are idempotent.
- Routine delivery stays inside the demo inbox.
- Scope change pauses automation and never silently modifies V1.
- Approval-only messages remain drafts with the manual-review warning.
- No external send, browser, payment, signing-on-behalf, legal, or complaint action exists.
- Timeline, message states, agent trace, and audit history are visible.
- No secret or real personal data appears in the UI, logs, screenshots, or recording.
