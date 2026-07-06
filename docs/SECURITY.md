# Security Model

## Status

This document defines required controls for the corrected contract-driven communication MVP. The current application still contains the legacy evidence/payment-follow-up domain; security compliance must be reassessed as each corrected milestone is implemented.

## Assets and threats

Protected assets include reviewed terms, contract versions, signature records, milestones, progress records, messages, replies, scope-change requests, audit events, API credentials, and workflow integrity.

The MVP must address:

- prompt injection in discussions or client replies;
- AI-created signatures or invented progress;
- use of an inactive or superseded contract;
- duplicate scheduler queueing or delivery;
- automatic delivery of approval-only messages;
- silent scope expansion;
- broad agent tool permissions or direct database access;
- legal claims, threats, payment guarantees, or external-send implications;
- audit omission or deletion;
- secret, personal-data, stack-trace, prompt, environment, or database-detail leakage;
- STDIO protocol corruption from logs on stdout.

## Mandatory controls

### No external action

No component contacts WhatsApp, email, Telegram, Instagram, payment systems, legal systems, browsers, or complaint services. The only automatic destination is the built-in local demo inbox.

Allowed UI wording:

```text
Delivered to demo inbox.
Production message-channel integrations are deferred.
```

The UI must not imply that a real client or external platform was contacted.

### Signature integrity

- AI cannot sign or accept for either party.
- Freelancer and client acceptance are separate user-triggered records.
- Each record includes party role, display name, exact contract code/version wording, and UTC timestamp.
- A contract activates only when both roles accept the same latest version.
- V1 remains active until V2 receives both acceptances; only then does V1 become `SUPERSEDED`.
- Mismatch and duplicate attempts are rejected without state change and are audited.

The simulated signature flow is product workflow evidence, not a claim of legal enforceability or identity verification.

### Progress integrity

AI may draft milestone definitions from reviewed contract facts, but it cannot mark a milestone ready or complete. Only an explicit freelancer action records progress. Communication policy must verify the required progress event before mentioning readiness, completion, delivery, or invoice availability.

### Prompt-injection boundary

Discussion and reply text is untrusted data. It is passed in typed fields and clearly separated from agent instructions. Model output cannot directly:

- create a signature;
- update milestone progress;
- authorize delivery;
- change contract scope;
- change tool permissions;
- select an external recipient;
- bypass idempotency or audit.

Structured output is schema validated before domain use.

### Contract-version enforcement

Every milestone, message, reply decision, and scope-change request references an agreement version. Automation policy retrieves the latest `ACTIVE` contract from deterministic storage. A draft or superseded version cannot control a message. Scope-change pending state pauses affected automation until review and, when accepted, mutual V2 activation.

### Automation policy levels

Routine automatic types:

```text
KICKOFF_CONFIRMATION
UPCOMING_MILESTONE_REMINDER
REVISION_WINDOW_REMINDER
DELIVERY_CONFIRMATION
INVOICE_AVAILABILITY_NOTICE
```

These can be queued and delivered only when contract state, signatures, automation flag, milestone/event evidence, send mode, safety result, idempotency, and internal destination all pass.

Approval-required types:

```text
DELAY_NOTICE
SCOPE_CHANGE_RESPONSE
PAYMENT_REMINDER
DISPUTE_RESPONSE
```

Any apology, compensation, deadline extension, legal wording, or agreement interpretation is also approval-required. Such messages remain drafts until freelancer approval and include:

```text
Draft only — review and send manually.
```

The scheduler must never auto-deliver them.

### Idempotent scheduler and delivery

The scheduler constructs a deterministic key from project, active contract version, milestone, message type, and scheduled event. A database uniqueness constraint and service-level conflict handling prevent duplicate queueing. Delivery transition is also idempotent; a delivered message cannot be delivered again.

The timer and internal API trigger call the same service method. Every run records counts for queued, delivered, skipped duplicate, and blocked decisions.

### Scope-change containment

A `SCOPE_CHANGE` classification is advisory. Deterministic code:

1. records the reply;
2. creates a `ScopeChangeRequest`;
3. pauses affected automation;
4. prevents promises or additional milestone work;
5. requires freelancer review;
6. creates V2 only after an accepted review decision;
7. requires both V2 acceptances before activation.

### Least-privilege tools

| Agent | Allowed tools |
| --- | --- |
| `CoordinatorAgent` | None |
| `DiscussionAgent` | Project-from-terms, discussion facts |
| `ContractAgent` | Contract template/version, signature request |
| `CommunicationAgent` | Active contract/timeline reads, due communication, queue, scope-change request |
| `SafetyAuditAgent` | Automation policy only |

The deterministic scheduler alone calls demo-inbox delivery. Agents do not import repositories or open SQLite connections. The MCP server runs over internal STDIO only. No external communication occurs in Milestone 3.

### Validation and safe errors

- Pydantic validates API, agent, and MCP boundaries.
- Services validate resource existence, state, active version, signature role, progress actor, queue transition, and idempotency.
- Public errors expose stable codes, safe messages, and request IDs only.
- MCP results are JSON-compatible dictionaries and never expose secrets, prompts, stack traces, environment values, or database details.
- Operational logs go to stderr; stdout is reserved for MCP protocol traffic.

### Append-only audit

Audit events cover discussion extraction, reviewed terms, contracts, signature requests and acceptance, activation, supersession, milestones, progress, agent and MCP calls, scheduler checks, policy outcomes, queueing, approval, delivery, replies, classification, pauses, scope changes, safety blocks, and configuration failures.

The domain write and audit event share a transaction where the operation mutates state. There is no audit update or delete API/tool. Application append-only storage is not tamper-proof against a database operator and does not prove external authenticity or legal admissibility.

### Secrets and data

- `.env` and variants are ignored; `.env.example` contains no secret.
- Demo fixtures are synthetic.
- Never commit real discussions, names, contact details, contracts, invoices, signatures, API keys, or screenshots containing personal data.
- Before a commit or PR, inspect staged files for secrets and accidental personal data.

## Required security tests

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

Any failure is a release blocker.

## Limitations

The MVP is local, single-user, and synthetic-data only. Authentication, hostile multi-tenant isolation, encryption at rest, rate limiting, retention, backup, key rotation, disaster recovery, public hosting, real identity verification, and production messaging privacy controls must be designed before deployment with real users or data.
