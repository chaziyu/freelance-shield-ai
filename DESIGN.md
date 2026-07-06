# FreelanceShield AI Design System

## 1. Visual Theme and Atmosphere

FreelanceShield AI should feel like a calm evidence command center for freelancers: protective, precise, and easy to follow under stress. The selected UI direction uses a dark left workflow rail, a light operational workspace, compact status chips, and a persistent safety banner.

The product must feel helpful without looking like a legal, debt collection, or payment enforcement tool. The interface should make safety rules obvious: no automatic sending, no legal claims, no hidden agent actions, and every communication is a draft for manual review.

## 2. Selected UI Direction

Use the selected command-center screenshot as the primary app shell direction:

- Dark left navigation with numbered workflow steps.
- Light main workspace with one active task at a time.
- Top project selector and project-state progress rail.
- Persistent warning banner: `Draft only — review and send manually.`
- Right-side safety, agent trace, and audit context.
- Teal primary action color, amber unresolved/warning color, blue trace/tool color, red dispute/block color.

## 3. What Needs Improvement in the Selected UI

The selected UI is strong, but the reminder page needs tighter hierarchy than the intake page.

1. The right panel is useful, but too dense for a reminder decision. On the reminder page, the policy result and safety decision must appear before the long trace list.
2. The top workflow state labels currently use enum-like names such as `ACCEPTANCE_PENDING`. Keep exact backend states in small chips, but use human labels nearby, such as `Acceptance pending`.
3. The primary teal button is visually strong, so reserve it for one main action per page. Reminder pages should make `Copy draft` primary only after safety approval.
4. The intake page shows many successful trace rows at once. On reminder pages, collapse older trace rows by default and show the latest decision first.
5. Missing or blocked states need more visual separation. Use amber for unresolved facts and muted red for blocked draft types.
6. Avoid any button or label that says `Send`, `Submit to client`, `Collect`, `Demand payment`, or `Escalate legally`.
7. The app should not rely only on icons for safety states. Pair icons with short labels so the capstone demo is understandable at a glance.

## 4. Reminder Page UX

The reminder page is the `Follow-Up` step. It must support two policy outcomes:

- Undisputed overdue invoice: allow `PAYMENT_REMINDER`.
- Disputed project: block `PAYMENT_REMINDER` and allow only `DISPUTE_CLARIFICATION`.

### Reminder Page Layout

Use the same app shell as the selected UI.

Left navigation:

- Intake: completed.
- Agreement: completed.
- Acceptance: completed.
- Evidence: completed or current.
- Follow-Up: active.
- Audit: available.

Main workspace order:

1. **Policy decision banner**
   - Shows the allowed draft type and blocked draft types.
   - For dispute: `PAYMENT_REMINDER blocked` and `DISPUTE_CLARIFICATION allowed`.
   - For overdue, no dispute: `PAYMENT_REMINDER allowed`.

2. **Evidence context**
   - Agreement accepted: `FS-001 Version 1`.
   - Delivery recorded.
   - Invoice recorded.
   - Dispute flag or overdue status.
   - Short hash badges only, not full hashes.

3. **Draft review panel**
   - Title: `Draft review`.
   - Draft type chip: `PAYMENT_REMINDER` or `DISPUTE_CLARIFICATION`.
   - Required warning adjacent to the draft body: `Draft only — review and send manually.`
   - Copy-only action: `Copy draft`.
   - Helper text: `No message will be sent.`

4. **Blocked actions**
   - Show only when policy blocks something.
   - Example: `Payment reminder blocked because this project is disputed.`
   - Keep the copy neutral and non-legal.

Right panel:

- Top block: `Safety review`.
- Second block: latest agent trace only.
- Third block: collapsed `Audit trail`.
- A `View full trace` control may open a drawer, but the default reminder page should stay focused on the policy decision and draft.

### Reminder Page Content Rules

Required visible text:

```text
Draft only — review and send manually.
No message will be sent.
```

Allowed labels:

- `Copy draft`
- `Review draft`
- `Policy decision`
- `Safety review`
- `Payment reminder allowed`
- `Payment reminder blocked`
- `Dispute clarification allowed`
- `View audit trail`

Forbidden labels:

- `Send`
- `Auto-send`
- `Collect payment`
- `Demand payment`
- `File claim`
- `Legal notice`
- `Legally binding`
- `Guaranteed recovery`

## 5. Color Palette and Roles

Use CSS variables and Tailwind static classes. Do not dynamically construct color class names.

| Token | Hex | OKLCH guide | Role |
| --- | --- | --- | --- |
| `--fs-sidebar` | `#071C2D` | `oklch(22% 0.055 245)` | Dark left navigation |
| `--fs-sidebar-2` | `#0A2A40` | `oklch(28% 0.06 238)` | Sidebar raised panels |
| `--fs-canvas` | `#F7FAFC` | `oklch(98% 0.006 225)` | App background |
| `--fs-surface` | `#FFFFFF` | `oklch(100% 0 0)` | Main task surfaces |
| `--fs-surface-muted` | `#F1F6F8` | `oklch(96% 0.01 220)` | Section tint and inactive rows |
| `--fs-border` | `#D7E2EA` | `oklch(89% 0.018 225)` | Dividers and input borders |
| `--fs-text` | `#102033` | `oklch(24% 0.03 245)` | Primary text |
| `--fs-text-muted` | `#5E6B7A` | `oklch(52% 0.025 245)` | Secondary text |
| `--fs-text-subtle` | `#8793A1` | `oklch(65% 0.018 245)` | Captions and metadata |
| `--fs-primary` | `#008C87` | `oklch(56% 0.105 185)` | Primary actions and active step |
| `--fs-primary-hover` | `#00746F` | `oklch(49% 0.105 185)` | Primary hover |
| `--fs-primary-soft` | `#DDF7F3` | `oklch(94% 0.045 185)` | Success and active backgrounds |
| `--fs-warning` | `#C76A00` | `oklch(60% 0.14 60)` | Unresolved fields and draft warning |
| `--fs-warning-soft` | `#FFF3D7` | `oklch(96% 0.055 78)` | Warning surfaces |
| `--fs-danger` | `#B42318` | `oklch(48% 0.15 30)` | Dispute and blocked actions |
| `--fs-danger-soft` | `#FEE4E2` | `oklch(92% 0.055 28)` | Blocked state surfaces |
| `--fs-info` | `#2563EB` | `oklch(55% 0.18 260)` | Trace/tool links and info |
| `--fs-info-soft` | `#E8F0FF` | `oklch(95% 0.035 260)` | Tool call surfaces |
| `--fs-success` | `#168753` | `oklch(55% 0.12 155)` | Completed and approved states |
| `--fs-success-soft` | `#E3F8EC` | `oklch(94% 0.045 155)` | Success surfaces |

### Color Usage

- Primary teal is for the active workflow step and the page's single main safe action.
- Amber is for unresolved facts, manual-review warnings, and missing information.
- Red is only for dispute, blocked, or unsafe outcomes.
- Blue is for trace, informational links, and MCP/tool-call metadata.
- Do not use purple or purple-blue gradients.
- Do not use gray text on colored surfaces. Use the role color at lower contrast instead.

## 6. Typography Rules

Brand words: precise, protective, transparent.

Primary UI font:

```css
font-family: "Public Sans", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Numeric/hash font:

```css
font-family: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
```

`Public Sans` gives the app a public-record, utility, and safety feel without making it look like a generic AI dashboard. Use `JetBrains Mono` only for IDs, timestamps, and hash badges.

| Token | Size | Line height | Weight | Letter spacing | Use |
| --- | --- | --- | --- | --- | --- |
| `display-sm` | `32px` | `40px` | `700` | `-0.022em` | Rare page-level headings |
| `heading-lg` | `24px` | `32px` | `700` | `-0.012em` | Page title |
| `heading-md` | `20px` | `28px` | `700` | `-0.012em` | Panel title |
| `heading-sm` | `16px` | `24px` | `700` | `0` | Section title |
| `body` | `14px` | `22px` | `400` | `0` | Default UI text |
| `body-strong` | `14px` | `22px` | `650` | `0` | Labels and row titles |
| `caption` | `12px` | `18px` | `500` | `0` | Metadata, helper text |
| `micro` | `11px` | `16px` | `700` | `0.02em` | Uppercase status chips only |

Rules:

- Body text should usually be `14px`.
- Long draft bodies use `15px` with `24px` line height for readability.
- Use tabular numbers for amounts, timestamps, counters, and step numbers.
- Do not use all-caps for long labels. Reserve all-caps for backend enum chips.

## 7. Component Styling

### Buttons

All buttons use `8px` radius, `14px` font size, `650` weight, `40px` minimum height, and `active:scale-95`.

Primary button:

- Background: `--fs-primary`.
- Text: white.
- Hover: `--fs-primary-hover`.
- Disabled: `#B8C8D2` background, `#F7FAFC` text.
- Use for: `Analyse chat`, `Create FS-001 V1`, `Copy draft` after safety approval.

Secondary button:

- Background: white.
- Border: `1px solid --fs-border`.
- Text: `--fs-text`.
- Hover background: `--fs-surface-muted`.
- Use for: `View full trace`, `View audit trail`, `Mark as resolved`.

Warning outline button:

- Background: white.
- Border: `1px solid #F0B45A`.
- Text: `--fs-warning`.
- Hover background: `--fs-warning-soft`.
- Use for unresolved-term actions.

Danger ghost button:

- Background: transparent.
- Text: `--fs-danger`.
- Hover background: `--fs-danger-soft`.
- Use only for blocked-state explanation affordances, not destructive actions in the MVP.

### Status Chips

Use `999px` pill radius, `11px` text, `700` weight.

- Success: `--fs-success-soft` background, `--fs-success` text.
- Warning: `--fs-warning-soft` background, `--fs-warning` text.
- Danger: `--fs-danger-soft` background, `--fs-danger` text.
- Info: `--fs-info-soft` background, `--fs-info` text.
- Neutral: `--fs-surface-muted` background, `--fs-text-muted` text.

### Surfaces

Use cards only for real grouped objects: chat source, extracted facts, policy decision, draft review, trace panel, audit panel.

- Radius: `12px` for primary surfaces.
- Border: `1px solid --fs-border`.
- Shadow: `0 1px 3px rgba(16, 32, 51, 0.08)`.
- Avoid cards inside cards. Lists inside a surface use row separators.

### Inputs and Textareas

- Height: `40px` for inputs and selects.
- Textarea minimum height: `120px`.
- Radius: `8px`.
- Border: `1px solid --fs-border`.
- Focus: `2px` ring using `rgba(0, 140, 135, 0.24)` plus `--fs-primary` border.
- Placeholder text: `--fs-text-subtle`.

### Navigation

Sidebar:

- Width desktop: `280px`.
- Background: `--fs-sidebar`.
- Active step: teal circle and soft teal line.
- Completed step: muted success state.
- Pending step: muted gray-blue.
- Step labels: human text, not backend enum text.
- Backend enum chip may appear as secondary metadata.

Top state rail:

- Use icon, connector line, human label, and small enum chip where useful.
- Active state gets teal icon and underline.
- Avoid making the rail visually louder than the active page task.

## 8. Layout Principles

Spacing scale:

```text
4, 8, 12, 16, 20, 24, 32, 40, 48
```

Desktop app shell:

- Sidebar: `280px`.
- Main content: fluid, max useful width around `760px` to `840px`.
- Right panel: `340px` to `380px`.
- Page padding: `24px`.
- Panel gap: `24px`.

Reminder page desktop grid:

```text
280px sidebar | flexible main workspace | 360px safety panel
```

Main workspace should be scannable in this order:

1. Policy result.
2. Evidence context.
3. Draft review.
4. Blocked actions or audit context.

Do not use a marketing hero. This is a work surface.

## 9. Depth and Elevation

Use background steps and very light shadows.

| Level | Treatment | Use |
| --- | --- | --- |
| `base` | `--fs-canvas`, no shadow | Page canvas |
| `surface` | white, border only | Main panels |
| `raised` | white, border, `0 1px 3px rgba(16, 32, 51, 0.08)` | Active task surfaces |
| `overlay` | white, border, `0 12px 28px rgba(16, 32, 51, 0.16)` | Drawers and popovers |

Do not use heavy shadows or glassmorphism. The interface should feel trustworthy, not glossy.

## 10. Responsive Behavior

Breakpoints:

- `sm`: `640px`.
- `md`: `768px`.
- `lg`: `1024px`.
- `xl`: `1280px`.

Desktop:

- Full three-column shell.
- Right safety panel is visible.
- State rail is horizontal.

Tablet:

- Sidebar collapses to icon rail.
- Right safety panel becomes a slide-over drawer.
- Main workspace remains full width.

Mobile:

- Bottom step navigation with labels shortened to Intake, Agreement, Accept, Evidence, Follow-Up, Audit.
- Top state rail becomes a horizontal scroll area.
- Safety and audit context become accordions below the draft.
- All tap targets at least `40px`.
- Primary action remains natural width unless the surrounding layout is full-width form-first.

## 11. Reminder Page States

### State A: Overdue, undisputed

Policy panel:

- Title: `Payment reminder allowed`.
- Draft type: `PAYMENT_REMINDER`.
- Reason: `Invoice due date has passed and no dispute is recorded.`

Draft action:

- Primary button: `Copy draft`.
- Helper: `No message will be sent.`

### State B: Disputed

Policy panel:

- Title: `Payment reminder blocked`.
- Block chip: `PAYMENT_REMINDER blocked`.
- Allow chip: `DISPUTE_CLARIFICATION allowed`.
- Reason: `Client has disputed the work, so only a neutral clarification draft is allowed.`

Draft action:

- Primary button: `Copy draft`.
- Draft type: `DISPUTE_CLARIFICATION`.
- Helper: `No message will be sent.`

### State C: No accepted agreement

Policy panel:

- Title: `Acceptance request needed`.
- Draft type: `ACCEPTANCE_REQUEST`.
- Reason: `Current agreement has not been accepted with matching code and version.`

Draft wording should use lower-certainty language and never imply the agreement is already accepted.

## 12. Do's and Don'ts

Do:

- Show the draft-only warning beside every generated communication.
- Put the policy decision above draft text on the reminder page.
- Use exact agreement code and version wherever acceptance is discussed.
- Keep raw chat text visually bounded as untrusted source material.
- Use copy-only interactions for generated messages.
- Show audit and trace as evidence of workflow, not decoration.
- Use short, neutral wording for disputes.

Don't:

- Do not show a send button.
- Do not imply the app contacts Instagram, WhatsApp, Telegram, Facebook, or email.
- Do not say an agreement is legally binding or enforceable.
- Do not use payment collection, debt recovery, court, or complaint language.
- Do not hide blocked policy outcomes in a collapsed drawer.
- Do not fabricate agent trace events in frontend-only UI.
- Do not make every row a separate card.
- Do not use purple-blue AI gradients.

## 13. Agent Prompt Guide

Quick color reference:

```text
sidebar #071C2D
canvas #F7FAFC
surface #FFFFFF
text #102033
muted text #5E6B7A
border #D7E2EA
primary #008C87
primary hover #00746F
warning #C76A00
warning soft #FFF3D7
danger #B42318
danger soft #FEE4E2
info #2563EB
success #168753
```

Example component prompts:

1. Create the Follow-Up reminder page using a `280px` dark `#071C2D` sidebar, `#F7FAFC` canvas, `24px` page padding, `24px` grid gap, `360px` right safety panel, `Public Sans` font, `24px/32px` page title at weight `700` and letter spacing `-0.012em`, `14px/22px` body text, `12px` panel radius, and primary button background `#008C87` with `8px` radius and `40px` height.
2. Create a policy decision panel for disputed projects with `#FEE4E2` soft danger background, `#B42318` title/chip text, `12px` radius, `1px solid #D7E2EA` border, body text `14px/22px`, chips at `11px` weight `700`, and visible copy: `PAYMENT_REMINDER blocked`, `DISPUTE_CLARIFICATION allowed`.
3. Create a draft review panel with white `#FFFFFF` surface, `12px` radius, border `#D7E2EA`, long draft body at `15px/24px`, warning banner `#FFF3D7` with `#C76A00` text, required text `Draft only — review and send manually.`, primary `Copy draft` button in `#008C87`, and helper text `No message will be sent.`
4. Create the right Safety Review panel with latest trace first, collapsed older trace rows, blue info chips using `#E8F0FF` and `#2563EB`, success chips using `#E3F8EC` and `#168753`, and a secondary `View full trace` button with white background and `#D7E2EA` border.
5. Create the responsive mobile reminder page where the sidebar becomes bottom navigation, the right safety panel becomes accordions below the draft, all hit targets are at least `40px`, and the primary action remains `Copy draft` only.
