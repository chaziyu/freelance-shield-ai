import { z } from "zod";

const projectStatusSchema = z.enum([
  "DRAFT",
  "TERMS_READY",
  "ACCEPTANCE_PENDING",
  "ACCEPTED",
  "IN_PROGRESS",
  "DELIVERED",
  "INVOICED",
  "OVERDUE",
  "CLOSED",
  "DISPUTED",
  "RESOLUTION_PENDING",
]);

const traceStatusSchema = z.enum(["STARTED", "SUCCEEDED", "BLOCKED", "FAILED"]);
const acceptanceStatusSchema = z.enum(["DRAFT", "PENDING", "ACCEPTED"]);
const draftTypeSchema = z.enum([
  "ACCEPTANCE_REQUEST",
  "DELIVERY_CONFIRMATION",
  "PAYMENT_REMINDER",
  "DISPUTE_CLARIFICATION",
]);
const draftAuditStatusSchema = z.enum(["PENDING", "APPROVED_TO_SHOW", "BLOCKED"]);
const evidenceTypeSchema = z.enum(["ACCEPTANCE", "DELIVERY", "INVOICE", "SCOPE_CHANGE"]);

const projectSchema = z.object({
  id: z.uuid(),
  title: z.string(),
  client_name: z.string().nullable().optional(),
  source_platform: z.string(),
  amount: z.number().nullable(),
  currency: z.string().nullable(),
  deadline: z.string().nullable(),
  invoice_due_date: z.string().nullable(),
  status: projectStatusSchema,
  dispute_flag: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});

const extractedFactsSchema = z.object({
  project_title: z.string(),
  amount: z.number().nullable(),
  currency: z.string().nullable(),
  deadline: z.string().nullable(),
  revision_limit: z.number().nullable(),
  payment_terms: z.string().nullable(),
  missing_fields: z.array(z.string()),
  risk_flags: z.array(z.string()),
});

const traceEventSchema = z.object({
  actor: z.string(),
  action: z.string(),
  status: traceStatusSchema,
  timestamp: z.string(),
  metadata: z.record(z.string(), z.unknown()).default({}),
});

const agreementVersionSchema = z.object({
  id: z.uuid(),
  project_id: z.uuid(),
  agreement_code: z.string(),
  version_number: z.number(),
  scope: z.string(),
  deliverables: z.string(),
  revision_limit: z.number().nullable(),
  amount: z.number().nullable(),
  currency: z.string().nullable(),
  deadline: z.string().nullable(),
  payment_terms: z.string().nullable(),
  acceptance_status: acceptanceStatusSchema,
  accepted_at: z.string().nullable(),
  created_at: z.string(),
});

const followUpPolicySchema = z.object({
  allowed_draft_type: draftTypeSchema,
  blocked_draft_types: z.array(draftTypeSchema),
  reason_codes: z.array(z.string()),
});

const communicationDraftSchema = z.object({
  audit_status: draftAuditStatusSchema,
  body: z.string(),
  created_at: z.string(),
  draft_type: draftTypeSchema,
  id: z.uuid(),
  project_id: z.uuid(),
});

const safetyResultSchema = z.object({
  blocked: z.boolean(),
  blocked_reasons: z.array(z.string()),
  safe_to_show: z.boolean(),
  warnings: z.array(z.string()),
});

const evidenceEventSchema = z.object({
  content_hash: z.string(),
  created_at: z.string(),
  event_type: evidenceTypeSchema,
  id: z.uuid(),
  project_id: z.uuid(),
  summary: z.string(),
});

const timelineSummarySchema = z.object({
  event_count: z.number(),
  hash_previews: z.array(z.string()),
  latest_event_at: z.string().nullable(),
  latest_event_type: z.string().nullable(),
});

const auditSummarySchema = z.object({
  event_count: z.number(),
  latest_action: z.string().nullable(),
  latest_actor: z.string().nullable(),
  latest_event_at: z.string().nullable(),
});

const auditEventSchema = z.object({
  action: z.string(),
  actor: z.string(),
  created_at: z.string(),
  id: z.uuid(),
  metadata: z.record(z.string(), z.unknown()),
  project_id: z.uuid().nullable(),
});

const timelineEventSchema = z.object({
  content_hash: z.string().nullable().optional(),
  event_type: z.string(),
  reference_id: z.string(),
  summary: z.string(),
  timestamp: z.string(),
});

const intakeAnalyseResponseSchema = z.object({
  project: projectSchema,
  extracted_facts: extractedFactsSchema,
  trace: z.array(traceEventSchema),
});

const createAgreementResponseSchema = z.object({
  acceptance_message: z.string(),
  agreement: agreementVersionSchema,
  project_status: projectStatusSchema,
  trace: z.array(traceEventSchema),
});

const acceptanceResponseSchema = z.object({
  acceptance_evidence: evidenceEventSchema,
  agreement: agreementVersionSchema,
  project_status: projectStatusSchema,
  trace: z.array(traceEventSchema),
});

const evidenceResponseSchema = z.object({
  evidence: evidenceEventSchema,
  project_status: projectStatusSchema,
  trace: z.array(traceEventSchema),
});

const followUpResponseSchema = z.object({
  draft: communicationDraftSchema.nullable(),
  policy: followUpPolicySchema,
  safety: safetyResultSchema,
  trace: z.array(traceEventSchema),
});

const projectDetailResponseSchema = z.object({
  audit_summary: auditSummarySchema.nullable(),
  current_agreement: agreementVersionSchema.nullable(),
  latest_draft: communicationDraftSchema.nullable(),
  latest_policy: followUpPolicySchema.nullable(),
  latest_trace: z.array(traceEventSchema),
  project: projectSchema,
  timeline_summary: timelineSummarySchema.nullable(),
});

const auditResponseSchema = z.object({
  events: z.array(auditEventSchema),
  project_id: z.uuid(),
});

const timelineResponseSchema = z.object({
  events: z.array(timelineEventSchema),
  project_id: z.uuid(),
});

export type IntakeAnalyseResponse = z.infer<typeof intakeAnalyseResponseSchema>;
export type CreateAgreementResponse = z.infer<typeof createAgreementResponseSchema>;
export type AcceptanceResponse = z.infer<typeof acceptanceResponseSchema>;
export type EvidenceResponse = z.infer<typeof evidenceResponseSchema>;
export type FollowUpResponse = z.infer<typeof followUpResponseSchema>;
export type ProjectDetailResponse = z.infer<typeof projectDetailResponseSchema>;
export type AuditResponse = z.infer<typeof auditResponseSchema>;
export type TimelineResponse = z.infer<typeof timelineResponseSchema>;

export interface IntakeAnalysePayload {
  chat_text: string;
  source_platform: string;
}

export interface CreateAgreementPayload {
  amount: number | null;
  change_reason?: string | null;
  currency: string | null;
  deadline: string | null;
  deliverables: string;
  payment_terms: string | null;
  revision_limit: number | null;
  scope: string;
}

export interface AcceptancePayload {
  acceptance_text: string;
  agreement_code: string;
  version_number: number;
}

export interface EvidencePayload {
  event_type: "DELIVERY" | "INVOICE";
  invoice_due_date: string | null;
  summary: string;
}

export interface FollowUpPayload {
  dispute: {
    declared: boolean;
    message: string;
  } | null;
}

export async function analyseIntake(
  payload: IntakeAnalysePayload,
): Promise<IntakeAnalyseResponse> {
  const response = await fetch("/api/intake/analyse", {
    body: JSON.stringify(payload),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });

  const body: unknown = await response.json();

  if (!response.ok) {
    throw new Error(readApiError(body, "Unable to analyse the intake chat."));
  }

  return intakeAnalyseResponseSchema.parse(body);
}

export async function getProjectDetail(
  projectId: string,
): Promise<ProjectDetailResponse> {
  const response = await fetch(`/api/projects/${projectId}`);
  const body: unknown = await response.json();

  if (!response.ok) {
    throw new Error(readApiError(body, "Unable to load the project."));
  }

  return projectDetailResponseSchema.parse(body);
}

export async function getProjectAudit(projectId: string): Promise<AuditResponse> {
  const response = await fetch(`/api/projects/${projectId}/audit`);
  const body: unknown = await response.json();

  if (!response.ok) {
    throw new Error(readApiError(body, "Unable to load the audit trail."));
  }

  return auditResponseSchema.parse(body);
}

export async function getProjectTimeline(
  projectId: string,
): Promise<TimelineResponse> {
  const response = await fetch(`/api/projects/${projectId}/timeline`);
  const body: unknown = await response.json();

  if (!response.ok) {
    throw new Error(readApiError(body, "Unable to load the evidence timeline."));
  }

  return timelineResponseSchema.parse(body);
}

export async function createAgreement(
  projectId: string,
  payload: CreateAgreementPayload,
): Promise<CreateAgreementResponse> {
  const response = await fetch(`/api/projects/${projectId}/agreements`, {
    body: JSON.stringify(payload),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });

  const body: unknown = await response.json();

  if (!response.ok) {
    throw new Error(readApiError(body, "Unable to create the agreement."));
  }

  return createAgreementResponseSchema.parse(body);
}

export async function recordAcceptance(
  projectId: string,
  payload: AcceptancePayload,
): Promise<AcceptanceResponse> {
  const response = await fetch(`/api/projects/${projectId}/acceptance`, {
    body: JSON.stringify(payload),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });

  const body: unknown = await response.json();

  if (!response.ok) {
    throw new Error(readApiError(body, "Unable to record acceptance."));
  }

  return acceptanceResponseSchema.parse(body);
}

export async function recordEvidence(
  projectId: string,
  payload: EvidencePayload,
): Promise<EvidenceResponse> {
  const response = await fetch(`/api/projects/${projectId}/evidence`, {
    body: JSON.stringify(payload),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });

  const body: unknown = await response.json();

  if (!response.ok) {
    throw new Error(readApiError(body, "Unable to record evidence."));
  }

  return evidenceResponseSchema.parse(body);
}

export async function requestFollowUp(
  projectId: string,
  payload: FollowUpPayload,
): Promise<FollowUpResponse> {
  const response = await fetch(`/api/projects/${projectId}/follow-up`, {
    body: JSON.stringify(payload),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });

  const body: unknown = await response.json();

  if (!response.ok) {
    throw new Error(readApiError(body, "Unable to evaluate follow-up policy."));
  }

  return followUpResponseSchema.parse(body);
}

function readApiError(body: unknown, fallback: string): string {
  const parsed = z
    .object({
      detail: z
        .object({
          message: z.string(),
        })
        .optional(),
    })
    .safeParse(body);

  return parsed.success ? (parsed.data.detail?.message ?? fallback) : fallback;
}
