# Security Model

## Status

This document specifies required controls for the planned MVP. Milestone 0 contains no runtime implementation and therefore makes no claim that these controls are already operational.

## Assets and threats

Protected assets are project facts, agreement versions, acceptance records, evidence summaries and hashes, communication drafts, audit events, API credentials, and workflow integrity.

The MVP must address:

- prompt injection embedded in client chat;
- unauthorized or over-broad agent tool access;
- unsafe payment demands, legal claims, threats, or implied automatic action;
- dispute-state bypasses;
- invalid agreement acceptance or silent version replacement;
- audit omission or deletion;
- secret, personal-data, stack-trace, or environment leakage;
- STDIO protocol corruption from logs written to stdout.

Authentication, hostile multi-tenant isolation, public production hardening, and real personal-data handling are outside the single-user synthetic demo. They must be designed before any public or multi-user deployment.

## Mandatory controls

### No external action

The application produces copyable text only. It has no send-message, browser-control, payment, claim-filing, or complaint-submission tool or integration. Every generated communication includes:

```text
Draft only — review and send manually.
```

The UI must not label a copy action as sending or imply that the system contacted a client.

### Prompt-injection boundary

Client chat is untrusted data. The API passes it in a typed field, and agent instructions identify it as quoted source material. Raw chat must not be interpolated into system or tool instructions. Model output is schema validated and cannot directly select a forbidden policy path or database operation.

### Policy before draft

Backend policy determines the only permitted draft type before an agent generates wording. The order is:

```text
validated project state
→ deterministic policy decision
→ draft wording constrained to that decision
→ SafetyAuditAgent review
→ store and display, or block and audit
```

When `dispute_flag` is true or project state is `DISPUTED`, the permitted type is only `DISPUTE_CLARIFICATION`. A model cannot override this with payment-demand language.

### Least-privilege tools

Each agent receives a distinct filtered `McpToolset`:

| Agent | Tool access |
| --- | --- |
| `CoordinatorAgent` | No persistence tools |
| `IntakeAgent` | Project creation, extracted facts, audit append |
| `AgreementAgent` | Contract template, agreement version creation, audit append |
| `FollowUpAgent` | Timeline read, policy evaluation, draft creation, audit append |
| `SafetyAuditAgent` | Audit append only |

Agents do not import repositories or open SQLite connections. The internal MCP server is reachable only over STDIO and is never exposed as a network service.

### Validation and safe errors

- Pydantic validates API, agent, and MCP inputs at trust boundaries.
- Services validate referenced projects and agreements and enforce state transitions.
- UUIDs, UTC timestamps, enum values, agreement codes, version numbers, and acceptance text are validated explicitly.
- Public 500 responses contain a request identifier and generic message, never a stack trace, prompt, environment value, database path, or secret.
- MCP returns JSON-compatible dictionaries and writes operational logs to stderr only.

### Agreement integrity

Acceptance is recorded only when both the agreement code and version match the current version. A scope change creates a new immutable version and resets acceptance to `PENDING`. The application must not edit an accepted version in place.

### Append-only audit trail

Significant actions include agreement creation and version changes, acceptance, evidence events, policy decisions, MCP calls, draft generation, approvals, and blocks. Each appends an audit event in the same transaction as its associated domain write. No API or MCP audit deletion tool exists.

Append-only at the application layer is not tamper-proof against an operator with filesystem or database access. Stronger guarantees would require restricted operational access, backups, signed records, and external anchoring; these are outside the MVP.

### Evidence hashing limitations

For deterministic hashing, replace CRLF and lone CR line endings in the submitted evidence summary with LF, preserve all other characters and whitespace, encode as UTF-8, and store the lowercase SHA-256 hex digest. The hash can later detect a content mismatch. It does not prove:

- who authored or submitted the content;
- that the content was authentic or complete;
- when the external event occurred;
- legal ownership, enforceability, or admissibility.

The UI and documentation must not make those claims.

### Secrets and data handling

- Commit `.env.example` with empty or synthetic values only; ignore `.env` and variants.
- Never commit API keys, real client chats, invoices, contact details, or personal data.
- Use the synthetic demo fixtures from `docs/DEMO_SCRIPT.md`.
- Do not return or log secrets, full prompts, environment variables, hidden database details, or raw exception data.
- Before a pull request, inspect staged changes for secret and personal-data exposure.

## Required safety checks

The implemented system cannot pass its quality gate unless these tests pass:

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

A failed safety test is a release blocker.

## Security limitations and unresolved decisions

- The MVP is local and single-user; authentication and authorization are absent by scope.
- API rate limiting, encrypted backups, key rotation, retention, disaster recovery, and public hosting controls are not yet specified.
- SQLite files are not application-level encrypted by this design.
- The exact model and model-data retention configuration are not selected.
- Real data must not be used until privacy, retention, access control, and incident-response requirements are defined.
