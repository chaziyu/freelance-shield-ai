# Agent Contract

## Status

Milestone 4 implemented. This document defines the runtime agent permissions, orchestration flow, and security boundaries for the ADK agent subsystem.

## Agent inventory

| Agent | Model Mode | MCP Tools (Runtime) | Sub-Agents | Description |
| --- | --- | --- | --- | --- |
| `CoordinatorAgent` | chat | None | None | Routes typed workflow intents; no persistence or delegation |
| `DiscussionAgent` | chat | None | None | Extracts structured facts from untrusted discussion text |
| `ContractAgent` | chat | `get_contract_template` | None | Creates transient DRAFT contract proposals from reviewed terms |
| `CommunicationAgent` | chat | `get_latest_active_contract`, `get_due_communications` | None | Reads contract context and due updates; classifies replies (tool-free variant) |
| `SafetyAuditAgent` | chat | `evaluate_automation_policy` | None | Evaluates safety of proposals; tool-free for discussion/contract audits |

No agent has mutating MCP tools. All mutations pass through named trusted persistence adapters with `SafetyValidationReceipt` verification.

## Orchestration sequence

`AdkWorkflowService` controls the deterministic workflow pattern for every agent invocation:

1. **Method selection.** The service selects an allowlisted workflow method based on the typed API request. No open-ended agent delegation exists.
2. **CoordinatorAgent intent.** `CoordinatorAgent` receives a scoped input and returns a typed intent string (e.g. `analyze_discussion`) and a safe trace event. It has no tools, no sub-agents, and no persistence.
3. **Stage validation.** The service validates that the requested stage sequence matches the chosen workflow method. Mismatched intents are rejected.
4. **Specialist execution.** The service runs the correct specialist agent (`DiscussionAgent`, `ContractAgent`, or `CommunicationAgent`) with its narrow `McpToolset`. The agent returns structured output only; it cannot persist results.
5. **Schema validation.** Agent output is validated against a typed Pydantic model (`ExtractedDiscussionFacts`, `ContractDraftProposal`, `RoutineUpdateCandidate`, or classification result). Invalid output fails the workflow.
6. **Safety audit.** `SafetyAuditAgent` evaluates the validated output. For routine updates it calls `evaluate_automation_policy`; for discussion and contract audits it runs tool-free. A `blocked` decision halts the workflow.
7. **Deterministic checks.** Server-side checks verify evidence-quote presence, forbidden-term absence, attestation validity, policy approval, and SOW completeness. These checks are not model-dependent.
8. **Receipt issuance.** A `SafetyValidationReceipt` is generated with an HMAC-SHA-256 signature covering the candidate type, candidate hash, check results, and expiry. Only receipts where `deterministic_checks_passed` is true and the safety decision is not blocked proceed.
9. **Trusted adapter call.** A named trusted persistence adapter method calls the appropriate mutating MCP tool(s), after re-verifying the receipt signature, candidate hash match, expiry, and check status.

## Workflow methods

Five workflow methods are implemented:

### `analyze_discussion`

Discussion extraction with evidence-quote verification. `DiscussionAgent` extracts `EvidenceBackedField` values from untrusted text. Deterministic checks verify that each `evidence_quote` is a substring of the original discussion and that raw text does not leak into the structured output.

### `create_contract_draft`

Contract creation with `ReviewedTermsAttestation` verification. The service verifies an HMAC-signed attestation proving the freelancer reviewed and approved the extracted terms before `ContractAgent` produces a transient `ContractDraftProposal`. Deterministic checks reject forbidden terms (legal enforceability, external platforms) and missing SOW fields.

### `prepare_due_updates`

Communication preparation with automation policy check. `CommunicationAgent` reads the active contract and due communications via read-only MCP tools. For each candidate, the service calls `evaluate_automation_policy` (via `SafetyAuditAgent`), runs deterministic action validation, and queues approved routine updates through the trusted adapter.

### `classify_client_reply`

Tool-free reply classification with no side effects. A tool-free `CommunicationAgent` variant classifies the reply as `ACKNOWLEDGEMENT`, `FEEDBACK`, `QUESTION`, `SCOPE_CHANGE`, or `CONCERN`. No database writes occur. Trace summaries are sanitized to prevent untrusted reply text from appearing in logs.

### `process_persisted_scope_change`

Scope change creation from a persisted client reply. `SafetyAuditAgent` evaluates the proposed scope-change handling. On approval, the trusted adapter creates a `ScopeChangeRequest` via MCP, which deterministic services use to pause affected automation.

## Trusted persistence adapter

`AdkWorkflowService` exposes four named adapter methods. Each requires a valid `SafetyValidationReceipt` before calling any mutating MCP tool.

### `persist_validated_discussion_facts()`

Calls `create_project_from_terms` and `save_discussion_facts`. Creates the project record and stores the extracted discussion snapshot.

### `persist_validated_contract_draft()`

Calls `create_contract_version`. Creates an immutable `DRAFT` agreement version from the validated proposal.

### `queue_validated_routine_update()`

Calls `queue_routine_update`. Queues a single routine message with a deterministic idempotency key.

### `create_validated_scope_change_request()`

Calls `create_scope_change_request`. Creates a scope-change request record that triggers automation pause.

### Receipt verification

Every adapter method re-verifies the `SafetyValidationReceipt` before executing. Verification requires:

- **Type match:** `candidate_type` matches the adapter operation (e.g. `discussion_facts`, `contract_draft`, `routine_update`, `scope_change`).
- **Hash match:** `candidate_hash` matches the SHA-256 hash of the canonical JSON payload recomputed at call time.
- **Checks passed:** `deterministic_checks_passed` is `True`.
- **Not expired:** Current time is within the receipt's 5-minute TTL window (`issued_at` ≤ now ≤ `expires_at`).
- **Valid signature:** HMAC-SHA-256 `receipt_signature` matches the recomputed signature using `SAFETY_RECEIPT_HMAC_KEY`.
- **Not blocked:** The preceding `SafetyAuditAgent` decision was not `blocked`.

A failed verification raises `ConfigurationError` and the MCP mutation is never attempted.

## Forbidden operations

No agent may:

- Call mutating MCP tools directly (`create_project_from_terms`, `save_discussion_facts`, `create_contract_version`, `create_signature_request`, `queue_routine_update`, `create_scope_change_request`, `deliver_to_demo_inbox`, `record_client_reply`, `record_milestone_progress`, `pause_project_automation`).
- Sign or accept contracts for either party.
- Mark milestones ready or complete.
- Deliver messages to the demo inbox.
- Contact external platforms (WhatsApp, email, Telegram, Instagram, payment, legal, or browser).
- Access SQLite directly or import repository modules.
- Override deterministic automation policy or bypass receipt verification.

## Cryptographic gates

### `ReviewedTermsAttestation`

Proves that a freelancer reviewed and approved extracted terms before contract drafting begins.

| Property | Value |
| --- | --- |
| Algorithm | HMAC-SHA-256 |
| Key source | `REVIEW_TERMS_ATTESTATION_HMAC_KEY` environment variable |
| Minimum key length | 32 characters |
| TTL | 15 minutes |
| Signed message | `{project_id}\|{canonical_terms_json}\|{issued_at}\|{expires_at}` |
| Verified fields | Project ID match, terms hash match, timestamp window, HMAC signature |

### `SafetyValidationReceipt`

Proves that a candidate output passed both the `SafetyAuditAgent` evaluation and deterministic server-side checks.

| Property | Value |
| --- | --- |
| Algorithm | HMAC-SHA-256 |
| Key source | `SAFETY_RECEIPT_HMAC_KEY` environment variable |
| Minimum key length | 32 characters |
| TTL | 5 minutes |
| Signed message | `{candidate_type}\|{candidate_hash}\|{deterministic_checks_passed}\|{sorted_failed_codes}\|{issued_at}\|{expires_at}` |
| Verified fields | Candidate type match, candidate hash match, checks passed, timestamp window, HMAC signature |

Both keys fall back to deterministic test secrets only when `FREELANCE_SHIELD_ALLOW_LOCAL_WORKFLOW=1` is set. Missing or undersized keys in production raise `ConfigurationError` before any workflow executes.

## Testing approach

All tests use a deterministic fake LLM (`BaseLlm` subclass) that returns structured JSON without making real model API calls. The fake model routes responses based on system instruction content, simulating the multi-agent conversation flow:

- `CoordinatorAgent` instructions produce intent routing output.
- `DiscussionAgent` instructions produce `ExtractedDiscussionFacts` with `EvidenceBackedField` values.
- `ContractAgent` instructions produce `ContractDraftProposal` output.
- `CommunicationAgent` instructions produce classification or due-update output.
- `SafetyAuditAgent` instructions produce `SafetyAuditDecision` output.

This approach verifies the full orchestration sequence — intent routing, schema validation, deterministic checks, receipt issuance, receipt verification, and trusted adapter invocation — without depending on external model availability or non-deterministic outputs.
