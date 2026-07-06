export type WorkflowStep =
  | "intake"
  | "agreement"
  | "acceptance"
  | "evidence"
  | "follow-up"
  | "audit";

export interface StepMeta {
  id: WorkflowStep;
  label: string;
  shortLabel: string;
  status: string;
  path: string;
}

export interface ProjectStateMeta {
  label: string;
  enumValue: string;
}

export type ChipTone = "danger" | "info" | "success" | "warning" | "neutral";
export type TraceTone = "info" | "success";

export interface TraceRowData {
  actor: string;
  action: string;
  time: string;
  tone: TraceTone;
}

export interface AuditRowData {
  time: string;
  title: string;
  detail: string;
}

export interface ProjectSummary {
  id: string;
  sourcePlatform: string;
  status: string;
  title: string;
}

export interface PageCopy {
  title: string;
  eyebrow: string;
  description: string;
}
