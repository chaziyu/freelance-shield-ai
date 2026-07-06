import type {
  AuditRowData,
  PageCopy,
  ProjectStateMeta,
  StepMeta,
  TraceRowData,
  WorkflowStep,
} from "./types";

export const workflowSteps: StepMeta[] = [
  {
    id: "intake",
    label: "Intake",
    shortLabel: "Intake",
    status: "TERMS_READY",
    path: "/intake",
  },
  {
    id: "agreement",
    label: "Agreement",
    shortLabel: "Agreement",
    status: "READY",
    path: "/agreement/f90c4421",
  },
  {
    id: "acceptance",
    label: "Acceptance",
    shortLabel: "Accept",
    status: "ACCEPTED",
    path: "/acceptance/f90c4421",
  },
  {
    id: "evidence",
    label: "Evidence",
    shortLabel: "Evidence",
    status: "RECORDED",
    path: "/evidence/f90c4421",
  },
  {
    id: "follow-up",
    label: "Follow-Up",
    shortLabel: "Follow",
    status: "ACTIVE",
    path: "/follow-up/f90c4421",
  },
  {
    id: "audit",
    label: "Audit",
    shortLabel: "Audit",
    status: "LIVE",
    path: "/audit/f90c4421",
  },
];

export const projectStates: ProjectStateMeta[] = [
  { label: "Draft", enumValue: "DRAFT" },
  { label: "Terms ready", enumValue: "TERMS_READY" },
  { label: "Acceptance pending", enumValue: "ACCEPTANCE_PENDING" },
  { label: "Accepted", enumValue: "ACCEPTED" },
  { label: "In progress", enumValue: "IN_PROGRESS" },
  { label: "Delivered", enumValue: "DELIVERED" },
  { label: "Invoiced", enumValue: "INVOICED" },
  { label: "Overdue", enumValue: "OVERDUE" },
  { label: "Disputed", enumValue: "DISPUTED" },
];

export const traceRows: TraceRowData[] = [
  {
    actor: "CoordinatorAgent",
    action: "Workflow started",
    time: "10:42:21 AM",
    tone: "success",
  },
  {
    actor: "IntakeAgent",
    action: "Extracted facts from chat",
    time: "10:42:24 AM",
    tone: "success",
  },
  {
    actor: "AgreementAgent",
    action: "Created FS-001 Version 1",
    time: "10:44:03 AM",
    tone: "success",
  },
  {
    actor: "FollowUpAgent",
    action: "Policy decision requested",
    time: "10:51:12 AM",
    tone: "info",
  },
  {
    actor: "SafetyAuditAgent",
    action: "Draft approved to show",
    time: "10:51:14 AM",
    tone: "success",
  },
];

export const auditRows: AuditRowData[] = [
  {
    time: "10:42 AM",
    title: "IntakeAgent analysed chat",
    detail: "Facts extracted without guessing",
  },
  {
    time: "10:44 AM",
    title: "Agreement FS-001 V1 created",
    detail: "Acceptance pending",
  },
  {
    time: "10:46 AM",
    title: "Acceptance recorded",
    detail: "Agreement code and version matched",
  },
  {
    time: "10:49 AM",
    title: "Delivery and invoice recorded",
    detail: "Evidence hashes created",
  },
  {
    time: "10:51 AM",
    title: "Policy decision logged",
    detail: "Dispute blocks payment reminder",
  },
];

export const pageCopy = {
  intake: {
    title: "New project intake",
    eyebrow: "Step 1",
    description:
      "Paste the client chat as untrusted source material. FreelanceShield extracts only what is stated and keeps missing terms visible.",
  },
  agreement: {
    title: "Agreement studio",
    eyebrow: "Step 2",
    description:
      "Review the concise Statement of Work, keep unresolved fields marked, and prepare Agreement FS-001 Version 1.",
  },
  acceptance: {
    title: "Acceptance recording",
    eyebrow: "Step 3",
    description:
      "Simulate the exact client acceptance text. The code and version must match before the project can move forward.",
  },
  evidence: {
    title: "Evidence timeline",
    eyebrow: "Step 4",
    description:
      "Review the chronological case file with content-hash badges for chat, agreement, acceptance, delivery, invoice, and dispute events.",
  },
  "follow-up": {
    title: "Reminder and dispute policy",
    eyebrow: "Step 5",
    description:
      "Run deterministic policy before any draft is shown. Disputed work blocks payment reminders and allows only neutral clarification.",
  },
  audit: {
    title: "Agent trace and audit",
    eyebrow: "Step 6",
    description:
      "Inspect the public workflow trace and append-only audit trail without exposing prompts, secrets, stack traces, or database details.",
  },
} satisfies Record<WorkflowStep, PageCopy>;
