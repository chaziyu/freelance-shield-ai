# MCP contract: freelance-project-mcp

This document lists all registered tools for the restricted internal STDIO MCP server named `freelance-project-mcp`.

## Registered MCP Tools

### 1. `create_project_from_terms`
- **Purpose**: Creates a new project from discussion terms.
- **Typed Input Fields**:
  - `title`: string (min_length=1, max_length=255)
  - `source_platform`: string (min_length=1, max_length=50)
  - `client_name`: string | null (optional, max_length=255)
- **Typed Output Shape**: `{"ok": true, "data": {"project": Project}}`
- **Safe Error Codes**: `VALIDATION_ERROR`, `INTERNAL_TOOL_ERROR`
- **Mutates State**: Yes
- **Server-Derived Audit Action**: `project_created` (actor: `system`)
- **Future ADK Agent Allowed**: Yes (`DiscussionAgent`)
- **Forbidden Side Effects**: No external platform contact, no signing, no payment, no browser control.

### 2. `save_discussion_facts`
- **Purpose**: Saves extracted discussion facts snapshot.
- **Typed Input Fields**:
  - `project_id`: UUID string
  - `extracted_facts`: dict
  - `missing_fields`: list of strings
  - `risk_flags`: list of strings
  - `raw_input`: string (min_length=1, max_length=100000)
- **Typed Output Shape**: `{"ok": true, "data": {"snapshot_id": string}}`
- **Safe Error Codes**: `VALIDATION_ERROR`, `INTERNAL_TOOL_ERROR`
- **Mutates State**: Yes
- **Server-Derived Audit Action**: `discussion_facts_saved` (actor: `discussion_agent`)
- **Future ADK Agent Allowed**: Yes (`DiscussionAgent`)
- **Forbidden Side Effects**: Raw chat text must never be persisted or logged.

### 3. `get_contract_template`
- **Purpose**: Retrieves the SOW template.
- **Typed Input Fields**: None (extra fields forbidden)
- **Typed Output Shape**: `{"ok": true, "data": {"template": dict}}`
- **Safe Error Codes**: `VALIDATION_ERROR`, `INTERNAL_TOOL_ERROR`
- **Mutates State**: No
- **Server-Derived Audit Action**: None
- **Future ADK Agent Allowed**: Yes (`ContractAgent`)
- **Forbidden Side Effects**: Genuinely read-only, no legal claims or advice.

### 4. `create_contract_version`
- **Purpose**: Creates a DRAFT version of an agreement.
- **Typed Input Fields**:
  - `project_id`: UUID string
  - `agreement_code`: string
  - `scope`: string
  - `deliverables_json`: string
  - `revision_limit`: integer | null
  - `fee_amount_minor`: integer | null
  - `currency`: string | null
  - `payment_terms`: string | null
  - `effective_start_date`: string (ISO date format) | null
  - `milestone_plan_json`: string | null
- **Typed Output Shape**: `{"ok": true, "data": {"agreement": AgreementVersion}}`
- **Safe Error Codes**: `VALIDATION_ERROR`, `INTERNAL_TOOL_ERROR`
- **Mutates State**: Yes
- **Server-Derived Audit Action**: `agreement_draft_created` (actor: `contract_agent`)
- **Future ADK Agent Allowed**: Yes (`ContractAgent`)
- **Forbidden Side Effects**: No activation, no auto-signature.

### 5. `create_signature_request`
- **Purpose**: Prepares signature requests for both freelancer and client.
- **Typed Input Fields**:
  - `agreement_version_id`: UUID string
- **Typed Output Shape**: `{"ok": true, "data": {"agreement_version_id": string}}`
- **Safe Error Codes**: `VALIDATION_ERROR`, `STATE_TRANSITION_ERROR`, `INTERNAL_TOOL_ERROR`
- **Mutates State**: Yes
- **Server-Derived Audit Action**: `agreement_pending_signature` (actor: `contract_agent`)
- **Future ADK Agent Allowed**: Yes (`ContractAgent`)
- **Forbidden Side Effects**: Does not sign or accept.

### 6. `get_latest_active_contract`
- **Purpose**: Retrieves the active contract of a project.
- **Typed Input Fields**:
  - `project_id`: UUID string
- **Typed Output Shape**: `{"ok": true, "data": {"agreement": AgreementVersion}}`
- **Safe Error Codes**: `VALIDATION_ERROR`, `INTERNAL_TOOL_ERROR`
- **Mutates State**: No
- **Server-Derived Audit Action**: None
- **Future ADK Agent Allowed**: Yes (`CommunicationAgent`)
- **Forbidden Side Effects**: Read-only, no audit event.

### 7. `create_milestones_from_contract`
- **Purpose**: Populates milestones based on active contract version milestone plan.
- **Typed Input Fields**:
  - `project_id`: UUID string
  - `agreement_version_id`: UUID string
- **Typed Output Shape**: `{"ok": true, "data": {"milestones": list}}`
- **Safe Error Codes**: `VALIDATION_ERROR`, `STATE_TRANSITION_ERROR`, `INTERNAL_TOOL_ERROR`
- **Mutates State**: Yes
- **Server-Derived Audit Action**: `milestones_created` (actor: `system`)
- **Future ADK Agent Allowed**: No (System only)
- **Forbidden Side Effects**: Idempotent milestone generation, no duplicates.

### 8. `get_due_communications`
- **Purpose**: Lists eligible due messages.
- **Typed Input Fields**:
  - `project_id`: UUID string
- **Typed Output Shape**: `{"ok": true, "data": {"communications": list}}`
- **Safe Error Codes**: `VALIDATION_ERROR`, `INTERNAL_TOOL_ERROR`
- **Mutates State**: No
- **Server-Derived Audit Action**: None
- **Future ADK Agent Allowed**: Yes (`CommunicationAgent`)
- **Forbidden Side Effects**: Read-only, does not queue/deliver/mutate messages.

### 9. `queue_routine_update`
- **Purpose**: Queues routine messages.
- **Typed Input Fields**:
  - `project_id`: UUID string
  - `agreement_version_id`: UUID string
  - `requested_action`: string
  - `idempotency_key`: string
  - `milestone_id`: UUID string | null
- **Typed Output Shape**: `{"ok": true, "data": {"message": ClientMessage}}`
- **Safe Error Codes**: `VALIDATION_ERROR`, `INTERNAL_TOOL_ERROR`
- **Mutates State**: Yes
- **Server-Derived Audit Action**: `client_message_queued` (actor: `system`)
- **Future ADK Agent Allowed**: Yes (`CommunicationAgent`)
- **Forbidden Side Effects**: No auto-delivery, only routine types.

### 10. `create_scope_change_request`
- **Purpose**: Pauses automation and creates a change request from client reply.
- **Typed Input Fields**:
  - `client_reply_id`: UUID string
  - `summary`: string
- **Typed Output Shape**: `{"ok": true, "data": {"scope_change_request_id": string}}`
- **Safe Error Codes**: `VALIDATION_ERROR`, `INTERNAL_TOOL_ERROR`
- **Mutates State**: Yes
- **Server-Derived Audit Action**: `scope_change_detected` (actor: `client`), `project_automation_paused` (actor: `system`)
- **Future ADK Agent Allowed**: Yes (`CommunicationAgent`)
- **Forbidden Side Effects**: Cannot modify agreement directly.

### 11. `evaluate_automation_policy`
- **Purpose**: Checks policy safety for messaging.
- **Typed Input Fields**:
  - `project_id`: UUID string
  - `agreement_version_id`: UUID string
  - `requested_action`: string
  - `milestone_id`: UUID string | null
  - `message_type`: string | null
- **Typed Output Shape**: `{"ok": true, "data": {"allowed": boolean, "send_mode": string, "reason_code": string}}`
- **Safe Error Codes**: `VALIDATION_ERROR`, `INTERNAL_TOOL_ERROR`
- **Mutates State**: No
- **Server-Derived Audit Action**: None
- **Future ADK Agent Allowed**: Yes (`SafetyAuditAgent`)
- **Forbidden Side Effects**: Read-only.

### 12. `get_project_timeline`
- **Purpose**: Chronological timeline retrieval.
- **Typed Input Fields**:
  - `project_id`: UUID string
- **Typed Output Shape**: `{"ok": true, "data": {"events": list}}`
- **Safe Error Codes**: `VALIDATION_ERROR`, `INTERNAL_TOOL_ERROR`
- **Mutates State**: No
- **Server-Derived Audit Action**: None
- **Future ADK Agent Allowed**: Yes (All agents)
- **Forbidden Side Effects**: Read-only, no chat text returned.

---

## Backend-Only Actions (No MCP tool registration)

These actions are kept strictly as trusted `DomainService` methods for future FastAPI/UI controllers and are absent from MCP and ADK tool groups.

### 1. `record_signature_acceptance`
- **Purpose**: Records explicit acceptance of a contract version by a party.
- **Side Effect**: Triggers contract activation if mutual acceptance is reached.
- **Auditing**: Writes `signature_recorded` and `agreement_activated` (if Mutual Acceptance achieved).

### 2. `record_milestone_progress`
- **Purpose**: Freelancer-triggered milestone progress update.
- **Side Effect**: Updates milestone status (e.g., PLANNED -> IN_PROGRESS -> READY_FOR_REVIEW -> COMPLETED).
- **Auditing**: Writes `milestone_progress_recorded`.

### 3. `pause_project_automation`
- **Purpose**: Pauses all automatic message scheduling.
- **Side Effect**: Sets `automation_enabled = False` on the project.
- **Auditing**: Writes `project_automation_paused`.

### 4. `record_client_reply`
- **Purpose**: Persists a client's reply.
- **Side Effect**: Performs reply classification and automatic scope change detection.
- **Auditing**: Writes `client_reply_recorded`.

### 5. `append_audit_log`
- **Purpose**: Writes arbitrary audit events. (Strictly trusted backend operation).
- **Side Effect**: Appends an event to the `audit_events` database table.
