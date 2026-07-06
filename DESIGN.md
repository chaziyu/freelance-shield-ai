# FreelanceShield AI Design System

## 1. Product experience

FreelanceShield AI is a calm contract-and-project communication command center. It should help a freelancer understand the active agreement, record real progress, see what automation will do, and stop safely when a client asks for new scope.

The UI must not resemble a legal, debt-collection, payment-enforcement, or external messaging product. Its core promise is transparent contract-driven workflow.

## 2. Command-center shell

Preserve the established visual direction:

- dark left workflow rail;
- light operational workspace;
- top project and active-contract header;
- human-readable state rail with compact backend enum chips;
- right-side safety, latest agent trace, and audit context;
- mobile bottom workflow navigation;
- teal primary actions, amber unresolved/approval states, red blocks and scope-change pauses, blue trace/tool context.

Persistent header message:

```text
Demo inbox only — no external messages are sent.
```

Approval-only drafts show this adjacent to the body:

```text
Draft only — review and send manually.
```

Routine demo-inbox messages show delivery status instead of a draft warning.

## 3. Workflow navigation

Desktop and mobile steps:

```text
1. Discussion
2. Contract
3. Project
4. Client Inbox
5. Communications
6. Timeline
```

Each step uses a human label. Exact states such as `CONTRACT_PENDING_SIGNATURE`, `READY_FOR_REVIEW`, or `SCOPE_CHANGE_PENDING` appear only in compact secondary chips.

## 4. Screen requirements

### Discussion Intake

Main order:

1. bounded untrusted-discussion textarea;
2. platform and optional reference date;
3. **Analyse discussion** primary action;
4. extracted terms;
5. missing/ambiguous terms;
6. freelancer review and edits;
7. **Create project from reviewed terms** action;
8. latest `DiscussionAgent` trace.

Never display extracted facts as confirmed until the freelancer reviews them.

### Contract and Signatures

Show:

- `Contract FS-001 Version N`;
- scope, deliverables, milestones, revisions, fee, payment terms, effective date, and scope-change procedure;
- separate freelancer and client signature cards;
- exact acceptance text;
- active/superseded state;
- clear statement that the simulated acceptance is not external identity verification or a legal enforceability claim.

Actions:

- **Accept as freelancer**;
- **Open simulated client signing**;
- **Accept as demo client** only inside that view.

Do not combine both acceptances into one control or imply that AI signed.

### Project Board

Show the latest active contract version above milestones. Each milestone row includes title, due date, status, contract version, and the last freelancer-recorded progress event.

Allowed progress controls:

- **Start milestone**;
- **Mark ready for review**;
- **Mark completed**;
- **Record delivery**;
- **Record invoice available**;
- **Pause automation**.

Each progress control explains that it records the freelancer's action. Never present AI-generated progress as fact.

### Client Inbox

This is a visibly simulated inbox inside the application.

Show:

- routine messages with `DELIVERED_TO_DEMO_INBOX` state;
- agreement version and milestone references;
- delivery timestamp;
- **Reply as demo client** action;
- recorded reply and classification;
- prominent scope-change warning when applicable.

Required helper text:

```text
Built-in demo inbox. No WhatsApp, email, Telegram, or Instagram message was sent.
```

### Communication Centre

Group messages by:

- Due;
- Queued;
- Delivered to demo inbox;
- Approval required;
- Blocked;
- Paused by scope change.

For routine messages, show the active version, supporting milestone/event, idempotency status, and destination `DEMO_INBOX`.

For approval-only messages, show policy reasons, the draft warning, **Copy draft**, and helper text `No external message will be sent.` Do not show a generic **Send** action.

### Timeline and Agent Trace

Chronologically show:

```text
discussion → contract → signatures → activation → milestones → progress
→ scheduler decision → queue → demo delivery → reply → classification
→ scope-change pause → V2 → renewed acceptance
```

Trace rows come from backend ADK/MCP data. Audit rows expose only safe allowlisted metadata. Never fabricate success rows in frontend constants.

## 5. Scope-change experience

When a reply may change scope, immediately surface:

- red/amber `Possible scope change` banner;
- paused affected automation;
- active contract remains V1;
- neutral summary of the requested change;
- **Review change request** primary action;
- **Reject change** secondary action;
- no automatic promise or contract mutation.

When V2 is created, display V1 as active and V2 as pending signatures until mutual acceptance. After activation, label V1 `SUPERSEDED` and V2 `ACTIVE`.

## 6. Safety and content rules

Allowed labels:

- `Analyse discussion`
- `Accept as freelancer`
- `Accept as demo client`
- `Mark ready for review`
- `Run update check`
- `Delivered to demo inbox`
- `Reply as demo client`
- `Review change request`
- `Copy draft`
- `Pause automation`
- `View audit trail`

Forbidden labels or claims:

- `Send WhatsApp`
- `Send email`
- `Auto-send to client`
- `Sign for client`
- `Sign for freelancer`
- `Collect payment`
- `Demand payment`
- `File claim`
- `Legal notice`
- `Legally binding`
- `Guaranteed recovery`

Do not rely on color or icons alone. Every safety, approval, pause, and delivery state has a short text label.

## 7. Color tokens

Use CSS variables and static Tailwind classes; do not construct dynamic color class names.

| Token | Hex | Role |
| --- | --- | --- |
| `--fs-sidebar` | `#071C2D` | Workflow navigation |
| `--fs-sidebar-2` | `#0A2A40` | Raised sidebar surfaces |
| `--fs-canvas` | `#F7FAFC` | App background |
| `--fs-surface` | `#FFFFFF` | Main surfaces |
| `--fs-surface-muted` | `#F1F6F8` | Inactive/grouped areas |
| `--fs-border` | `#D7E2EA` | Dividers and input borders |
| `--fs-text` | `#102033` | Primary text |
| `--fs-text-muted` | `#5E6B7A` | Secondary text |
| `--fs-text-subtle` | `#8793A1` | Captions |
| `--fs-primary` | `#008C87` | Primary action/active step |
| `--fs-primary-hover` | `#00746F` | Primary hover |
| `--fs-primary-soft` | `#DDF7F3` | Active/safe routine state |
| `--fs-warning` | `#C76A00` | Missing terms/approval required |
| `--fs-warning-soft` | `#FFF3D7` | Warning surfaces |
| `--fs-danger` | `#B42318` | Scope change/block/pause |
| `--fs-danger-soft` | `#FEE4E2` | Blocked surfaces |
| `--fs-info` | `#2563EB` | Agent/MCP/scheduler trace |
| `--fs-info-soft` | `#E8F0FF` | Trace surfaces |
| `--fs-success` | `#168753` | Accepted/active/delivered |
| `--fs-success-soft` | `#E3F8EC` | Success surfaces |

Use teal for one primary safe action per page, amber for review-required state, red only for blocks or scope-change pauses, and blue for technical trace context. Avoid purple AI gradients, glassmorphism, and heavy shadows.

## 8. Typography and components

Primary font:

```css
font-family: "Public Sans", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

IDs, timestamps, versions, and idempotency previews use:

```css
font-family: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
```

Body text is normally `14px/22px`; page titles `24px/32px` at weight `700`; status chips `11px` at weight `700`; long draft/message bodies `15px/24px`.

Buttons have `8px` radius, `40px` minimum height, visible focus, disabled state, and `active:scale-95`. Inputs have labels, `40px` minimum height, and a teal focus ring. Primary cards use `12px` radius, one border, and a subtle shadow. Avoid cards inside cards.

## 9. Layout and responsiveness

Desktop grid:

```text
280px workflow sidebar | flexible main workspace | 360px safety/trace panel
```

Use `24px` page padding and panel gaps. Keep the active task between roughly `760px` and `840px` when space allows.

Tablet: collapse the sidebar to an icon rail; move safety context to a drawer.

Mobile: use bottom navigation, horizontally scrollable state rail, safety/audit accordions below content, and `40px` minimum tap targets. Contract terms, milestone rows, and inbox messages must remain readable without horizontal page scrolling.

## 10. Accessibility and trust

- Use semantic headings, labels, buttons, lists, and tables.
- Maintain WCAG-compatible contrast and keyboard focus.
- Announce async success/error and blocked policy outcomes.
- Pair every icon and color with text.
- Keep raw discussion/reply data visually bounded and labeled untrusted.
- Show exact contract code/version wherever signatures, milestones, messages, or scope changes are discussed.
- Never hide the active contract version, automation pause, approval requirement, or demo-only destination.
