import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, type ReactNode, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  analyseIntake,
  createAgreement,
  getProjectAudit,
  getProjectDetail,
  getProjectTimeline,
  recordAcceptance,
  recordEvidence,
  requestFollowUp,
  type AuditResponse,
  type FollowUpPayload,
  type FollowUpResponse,
  type IntakeAnalyseResponse,
  type ProjectDetailResponse,
  type TimelineResponse,
} from "../api/workflow";
import {
  DraftReviewPanel,
  Panel,
  PolicyDecisionPanel,
  type AuditRowData,
  type ProjectSummary,
  StatusChip,
  type TraceRowData,
  WorkflowShell,
  type WorkflowStep,
} from "../components/workflow";
import { classNames } from "../components/workflow/classNames";
import { pageCopy } from "../components/workflow/workflowData";
import { TraceRow } from "../components/workflow/TraceRow";
import { platforms } from "../schema";

interface WorkflowPageProps {
  activeStep: WorkflowStep;
}

export function WorkflowPage({ activeStep }: WorkflowPageProps) {
  const { projectId } = useParams();
  const [intakeResult, setIntakeResult] = useState<IntakeAnalyseResponse | null>(
    null,
  );
  const isIntake = activeStep === "intake";
  const shouldLoadProject = Boolean(projectId && !isIntake);
  const shouldLoadTimeline = Boolean(projectId && activeStep === "evidence");
  const projectQuery = useQuery({
    enabled: shouldLoadProject,
    queryFn: () => getProjectDetail(projectId!),
    queryKey: ["project", projectId],
  });
  const auditQuery = useQuery({
    enabled: shouldLoadProject,
    queryFn: () => getProjectAudit(projectId!),
    queryKey: ["project-audit", projectId],
  });
  const timelineQuery = useQuery({
    enabled: shouldLoadTimeline,
    queryFn: () => getProjectTimeline(projectId!),
    queryKey: ["project-timeline", projectId],
  });
  const intakeProject = intakeResult?.project;
  const intakeTraceRows = intakeResult ? toTraceRows(intakeResult.trace) : [];
  const projectDetail = projectQuery.data;
  const loadedProject = projectDetail?.project;
  const shellProjectSummary = isIntake
    ? intakeSummary(intakeProject)
    : loadedProject
      ? projectSummary(loadedProject)
      : undefined;
  const shellTraceRows = isIntake
    ? intakeTraceRows
    : projectDetail
      ? toTraceRows(projectDetail.latest_trace)
      : [];
  const shellAuditRows = isIntake
    ? []
    : auditQuery.data
      ? toAuditRows(auditQuery.data)
      : [];

  return (
    <WorkflowShell
      activeStatus={
        isIntake ? (intakeProject?.status ?? "DRAFT") : loadedProject?.status
      }
      activeStep={activeStep}
      auditRows={shellAuditRows}
      pageCopy={pageCopy[activeStep]}
      projectSummary={shellProjectSummary}
      traceRows={shellTraceRows}
    >
      {activeStep === "intake" && (
        <IntakePage onAnalysed={setIntakeResult} result={intakeResult} />
      )}
      {activeStep === "agreement" && (
        <AgreementPage
          auditQueryKey={["project-audit", projectId]}
          isLoading={projectQuery.isLoading}
          projectDetail={projectDetail}
          projectError={projectQuery.error}
          projectId={projectId}
          projectQueryKey={["project", projectId]}
        />
      )}
      {activeStep === "acceptance" && (
        <AcceptancePage
          auditQueryKey={["project-audit", projectId]}
          isLoading={projectQuery.isLoading}
          projectDetail={projectDetail}
          projectError={projectQuery.error}
          projectId={projectId}
          projectQueryKey={["project", projectId]}
        />
      )}
      {activeStep === "evidence" && (
        <EvidencePage
          auditQueryKey={["project-audit", projectId]}
          isLoading={projectQuery.isLoading || timelineQuery.isLoading}
          projectDetail={projectDetail}
          projectError={projectQuery.error ?? timelineQuery.error}
          projectId={projectId}
          projectQueryKey={["project", projectId]}
          timeline={timelineQuery.data}
          timelineQueryKey={["project-timeline", projectId]}
        />
      )}
      {activeStep === "follow-up" && (
        <FollowUpPage
          auditQueryKey={["project-audit", projectId]}
          isLoading={projectQuery.isLoading}
          projectDetail={projectDetail}
          projectError={projectQuery.error}
          projectId={projectId}
          projectQueryKey={["project", projectId]}
        />
      )}
      {activeStep === "audit" && (
        <AuditPage
          audit={auditQuery.data}
          isLoading={projectQuery.isLoading || auditQuery.isLoading}
          projectDetail={projectDetail}
          projectError={projectQuery.error ?? auditQuery.error}
          projectId={projectId}
        />
      )}
    </WorkflowShell>
  );
}

function IntakePage({
  onAnalysed,
  result,
}: {
  onAnalysed: (result: IntakeAnalyseResponse) => void;
  result: IntakeAnalyseResponse | null;
}) {
  const [chatText, setChatText] = useState(
    "Need a poster by Friday. RM800. Two revisions.",
  );
  const [sourcePlatform, setSourcePlatform] = useState("Instagram");
  const mutation = useMutation({
    mutationFn: analyseIntake,
    onSuccess: onAnalysed,
  });
  const facts = result?.extracted_facts;
  const missingFields = facts?.missing_fields ?? [];
  const projectId = result?.project.id;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate({
      chat_text: chatText,
      source_platform: sourcePlatform,
    });
  }

  return (
    <div className="space-y-4">
      <Panel>
        <form onSubmit={handleSubmit}>
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-base font-bold">Untrusted source chat</h2>
            <label className="flex items-center gap-2 text-sm text-[var(--fs-text-muted)]">
              Platform
              <select
                className="rounded-md border border-[var(--fs-border)] bg-white px-2 py-1 text-sm font-bold text-[var(--fs-text)]"
                onChange={(event) => setSourcePlatform(event.target.value)}
                value={sourcePlatform}
              >
                {platforms.map((platform) => (
                  <option key={platform}>{platform}</option>
                ))}
              </select>
            </label>
          </div>
          <textarea
            className="mt-4 min-h-32 w-full resize-y rounded-lg border border-[var(--fs-border)] bg-[var(--fs-surface-muted)] p-5 text-sm leading-6 outline-none focus:border-[var(--fs-primary)]"
            onChange={(event) => setChatText(event.target.value)}
            value={chatText}
          />
          <div className="mt-4 flex items-center justify-between gap-4">
            <button
              className="btn-primary disabled:cursor-not-allowed disabled:opacity-50"
              disabled={mutation.isPending || chatText.trim().length === 0}
              type="submit"
            >
              {mutation.isPending ? "Analysing..." : "Analyse chat"}
            </button>
            {mutation.isSuccess && (
              <span className="text-sm text-[var(--fs-success)]">
                Intake analysis completed
              </span>
            )}
            {mutation.isError && (
              <span className="text-sm text-[var(--fs-danger)]" role="alert">
                {mutation.error.message}
              </span>
            )}
          </div>
        </form>
      </Panel>

      <FactsPanel facts={facts} sourcePlatform={sourcePlatform} />

      {missingFields.length > 0 && (
        <WarningPanel
          action="Mark as resolved"
          title={`Missing: ${formatMissingFields(missingFields)}`}
        >
          These are not in the chat. Confirm with your client before requesting
          acceptance.
        </WarningPanel>
      )}

      <Panel className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <h2 className="text-base font-bold">Agreement code preview</h2>
          <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
            {projectId
              ? "FS-001 will be assigned to this project."
              : "No intake project has been created yet."}
          </p>
        </div>
        {projectId ? (
          <Link className="btn-primary justify-center" to={`/agreement/${projectId}`}>
            Create FS-001 V1
          </Link>
        ) : (
          <button
            className="btn-primary justify-center opacity-50"
            disabled
            type="button"
          >
            Create FS-001 V1
          </button>
        )}
      </Panel>
    </div>
  );
}

function AgreementPage({
  auditQueryKey,
  isLoading,
  projectDetail,
  projectError,
  projectId,
  projectQueryKey,
}: {
  auditQueryKey: readonly unknown[];
  isLoading: boolean;
  projectDetail: ProjectDetailResponse | undefined;
  projectError: Error | null;
  projectId: string | undefined;
  projectQueryKey: readonly unknown[];
}) {
  const queryClient = useQueryClient();
  const project = projectDetail?.project;
  const [scope, setScope] = useState("Design one promotional poster.");
  const [deliverables, setDeliverables] = useState("One final digital poster file.");
  const [revisionLimit, setRevisionLimit] = useState("2");
  const [amount, setAmount] = useState<string | null>(null);
  const [currency, setCurrency] = useState<string | null>(null);
  const [paymentTerms, setPaymentTerms] = useState("");
  const createMutation = useMutation({
    mutationFn: () =>
      createAgreement(projectId!, {
        amount: amountForSubmit(amount, project?.amount),
        change_reason: null,
        currency: currencyForSubmit(currency, project?.currency),
        deadline: null,
        deliverables,
        payment_terms: paymentTerms.trim() || null,
        revision_limit: revisionLimit.trim() ? Number(revisionLimit) : null,
        scope,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: projectQueryKey });
      void queryClient.invalidateQueries({ queryKey: auditQueryKey });
    },
  });

  if (!projectId) {
    return (
      <Panel className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <h2 className="text-base font-bold">No project selected</h2>
          <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
            Analyse an intake chat first, then create Agreement FS-001 Version 1.
          </p>
        </div>
        <Link className="btn-primary justify-center" to="/intake">
          Open intake
        </Link>
      </Panel>
    );
  }

  if (isLoading) {
    return (
      <Panel>
        <h2 className="text-base font-bold">Loading project agreement state</h2>
        <p className="mt-2 text-sm text-[var(--fs-text-muted)]">
          Fetching project details and current agreement status.
        </p>
      </Panel>
    );
  }

  if (projectError) {
    return (
      <Panel>
        <h2 className="text-base font-bold text-[var(--fs-danger)]">
          Agreement data unavailable
        </h2>
        <p className="mt-2 text-sm text-[var(--fs-text-muted)]">
          {projectError.message}
        </p>
      </Panel>
    );
  }

  const currentAgreement =
    createMutation.data?.agreement ?? projectDetail?.current_agreement;
  const acceptanceMessage =
    createMutation.data?.acceptance_message ??
    (currentAgreement
      ? `Please reply: "I agree to Agreement ${currentAgreement.agreement_code} Version ${currentAgreement.version_number}."`
      : "Create the agreement to generate exact acceptance text.");
  const agreementCode = currentAgreement?.agreement_code ?? "FS-001";
  const versionNumber = currentAgreement?.version_number ?? 1;
  const acceptanceStatus = currentAgreement?.acceptance_status ?? "DRAFT";
  const displayScope = currentAgreement?.scope ?? scope;
  const displayDeliverables = currentAgreement?.deliverables ?? deliverables;
  const displayRevisionLimit =
    currentAgreement?.revision_limit?.toString() ?? revisionLimit;
  const displayAmount = formatAmount(
    currentAgreement?.amount ?? amountForSubmit(amount, project?.amount),
    currentAgreement?.currency ?? currencyForSubmit(currency, project?.currency),
  );
  const displayPaymentTerms = currentAgreement?.payment_terms ?? paymentTerms;

  function handleAgreementSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!projectId || currentAgreement) {
      return;
    }
    createMutation.mutate();
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_300px]">
      <Panel className="min-h-[620px]">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-bold text-[var(--fs-primary)]">
              Agreement {agreementCode} Version {versionNumber}
            </p>
            <h2 className="mt-1 text-xl font-bold">Statement of Work</h2>
          </div>
          <StatusChip tone={agreementStatusTone(acceptanceStatus)}>
            {acceptanceStatus}
          </StatusChip>
        </div>

        <div className="rounded-xl border border-[var(--fs-border)] bg-white px-8 py-7 shadow-[var(--fs-shadow-sm)]">
          <h3 className="text-center text-xl font-bold">
            {project?.title ?? "Freelance project"}
          </h3>
          <form className="mt-8 space-y-6 text-sm leading-7" onSubmit={handleAgreementSubmit}>
            <EditableDocumentField
              label="Scope"
              onChange={setScope}
              readOnly={Boolean(currentAgreement)}
              value={displayScope}
            />
            <EditableDocumentField
              label="Deliverables"
              onChange={setDeliverables}
              readOnly={Boolean(currentAgreement)}
              value={displayDeliverables}
            />
            <div className="grid gap-2 md:grid-cols-[150px_1fr]">
              <span className="font-bold">Fee</span>
              {currentAgreement ? (
                <span className="rounded-md bg-[var(--fs-surface-muted)] px-2 py-1">
                  {displayAmount}
                </span>
              ) : (
                <div className="grid gap-2 sm:grid-cols-[1fr_96px]">
                  <input
                    className="rounded-md border border-[var(--fs-border)] bg-[var(--fs-surface-muted)] px-2 py-1 outline-none focus:border-[var(--fs-primary)]"
                    onChange={(event) => setAmount(event.target.value)}
                    type="number"
                    value={amount ?? project?.amount?.toString() ?? ""}
                  />
                  <input
                    className="rounded-md border border-[var(--fs-border)] bg-[var(--fs-surface-muted)] px-2 py-1 uppercase outline-none focus:border-[var(--fs-primary)]"
                    maxLength={3}
                    onChange={(event) => setCurrency(event.target.value.toUpperCase())}
                    value={currency ?? project?.currency ?? "MYR"}
                  />
                </div>
              )}
            </div>
            <EditableDocumentField
              label="Revision limit"
              onChange={setRevisionLimit}
              readOnly={Boolean(currentAgreement)}
              value={displayRevisionLimit}
            />
            <DocumentField label="Deadline" unresolved value="Unresolved" />
            <EditableDocumentField
              label="Payment terms"
              onChange={setPaymentTerms}
              readOnly={Boolean(currentAgreement)}
              unresolved={!displayPaymentTerms}
              value={displayPaymentTerms}
            />
            {!currentAgreement && (
              <button
                className="btn-primary disabled:cursor-not-allowed disabled:opacity-50"
                disabled={createMutation.isPending || !scope.trim() || !deliverables.trim()}
                type="submit"
              >
                {createMutation.isPending ? "Creating agreement..." : "Create FS-001 V1"}
              </button>
            )}
          </form>
        </div>
      </Panel>

      <Panel>
        <h2 className="text-base font-bold">Agreement assistant</h2>
        <div className="mt-4 space-y-3">
          <AssistantRow label="Template" value="Freelance SOW" />
          <AssistantRow label="Code" value={agreementCode} />
          <AssistantRow label="Version" value={versionNumber.toString()} />
          <AssistantRow
            label="Unresolved"
            value={displayPaymentTerms ? "Deadline" : "Deadline, payment terms"}
            warning
          />
        </div>
        <div className="mt-5 rounded-lg bg-[var(--fs-warning-soft)] p-4 text-sm">
          {acceptanceMessage}
        </div>
        {createMutation.isError && (
          <p className="mt-3 text-sm text-[var(--fs-danger)]" role="alert">
            {createMutation.error.message}
          </p>
        )}
        <button
          className="btn-secondary mt-4 w-full justify-center"
          disabled={!currentAgreement}
          onClick={() => {
            if (currentAgreement && navigator.clipboard) {
              void navigator.clipboard.writeText(acceptanceMessage);
            }
          }}
          type="button"
        >
          Copy acceptance text
        </button>
        {currentAgreement && (
          <Link
            className="btn-primary mt-3 w-full justify-center"
            to={`/acceptance/${projectId}`}
          >
            Continue to acceptance
          </Link>
        )}
        <p className="mt-3 text-center text-xs text-[var(--fs-text-muted)]">
          No message will be sent. Review before sharing.
        </p>
      </Panel>
    </div>
  );
}

function AcceptancePage({
  auditQueryKey,
  isLoading,
  projectDetail,
  projectError,
  projectId,
  projectQueryKey,
}: {
  auditQueryKey: readonly unknown[];
  isLoading: boolean;
  projectDetail: ProjectDetailResponse | undefined;
  projectError: Error | null;
  projectId: string | undefined;
  projectQueryKey: readonly unknown[];
}) {
  const queryClient = useQueryClient();
  const currentAgreement = projectDetail?.current_agreement;
  const expectedText = currentAgreement
    ? `I agree to Agreement ${currentAgreement.agreement_code} Version ${currentAgreement.version_number}.`
    : "";
  const [acceptanceText, setAcceptanceText] = useState(expectedText);
  const acceptanceMutation = useMutation({
    mutationFn: () =>
      recordAcceptance(projectId!, {
        acceptance_text: acceptanceText || expectedText,
        agreement_code: currentAgreement!.agreement_code,
        version_number: currentAgreement!.version_number,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: projectQueryKey });
      void queryClient.invalidateQueries({ queryKey: auditQueryKey });
    },
  });
  const acceptedAgreement = acceptanceMutation.data?.agreement ?? currentAgreement;
  const acceptanceEvidence = acceptanceMutation.data?.acceptance_evidence;
  const isAccepted = acceptedAgreement?.acceptance_status === "ACCEPTED";

  if (!projectId) {
    return (
      <Panel className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <h2 className="text-base font-bold">No project selected</h2>
          <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
            Analyse an intake chat and create an agreement before recording acceptance.
          </p>
        </div>
        <Link className="btn-primary justify-center" to="/intake">
          Open intake
        </Link>
      </Panel>
    );
  }

  if (isLoading) {
    return (
      <Panel>
        <h2 className="text-base font-bold">Loading acceptance state</h2>
        <p className="mt-2 text-sm text-[var(--fs-text-muted)]">
          Fetching the current agreement code and version.
        </p>
      </Panel>
    );
  }

  if (projectError) {
    return (
      <Panel>
        <h2 className="text-base font-bold text-[var(--fs-danger)]">
          Acceptance data unavailable
        </h2>
        <p className="mt-2 text-sm text-[var(--fs-text-muted)]">
          {projectError.message}
        </p>
      </Panel>
    );
  }

  if (!currentAgreement) {
    return (
      <Panel className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <h2 className="text-base font-bold">Agreement required</h2>
          <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
            Create Agreement FS-001 Version 1 before simulating acceptance.
          </p>
        </div>
        <Link className="btn-primary justify-center" to={`/agreement/${projectId}`}>
          Open agreement
        </Link>
      </Panel>
    );
  }

  const displayAgreement = acceptedAgreement ?? currentAgreement;

  function handleAcceptanceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!projectId || !currentAgreement || isAccepted) {
      return;
    }
    acceptanceMutation.mutate();
  }

  return (
    <div className="space-y-4">
      <Panel className="grid gap-5 lg:grid-cols-[1fr_1fr]">
        <div>
          <h2 className="text-base font-bold">Acceptance message</h2>
          <p className="mt-2 text-sm text-[var(--fs-text-muted)]">
            The client response must match the agreement code and version.
          </p>
          <div className="mt-4 rounded-lg bg-[var(--fs-warning-soft)] p-4 text-sm font-semibold">
            Please reply: "{expectedText}"
          </div>
          <button
            className="btn-secondary mt-4"
            onClick={() => {
              if (navigator.clipboard) {
                void navigator.clipboard.writeText(expectedText);
              }
            }}
            type="button"
          >
            Copy acceptance text
          </button>
        </div>
        <div>
          <h2 className="text-base font-bold">Simulated client response</h2>
          <form className="mt-4 space-y-4" onSubmit={handleAcceptanceSubmit}>
            <textarea
              className="min-h-28 w-full resize-y rounded-lg border border-[var(--fs-border)] bg-[var(--fs-surface-muted)] p-4 text-sm outline-none focus:border-[var(--fs-primary)]"
              disabled={isAccepted}
              onChange={(event) => setAcceptanceText(event.target.value)}
              value={acceptanceText || expectedText}
            />
            {!isAccepted && (
              <button
                className="btn-primary disabled:cursor-not-allowed disabled:opacity-50"
                disabled={acceptanceMutation.isPending}
                type="submit"
              >
                {acceptanceMutation.isPending
                  ? "Recording acceptance..."
                  : "Record acceptance"}
              </button>
            )}
          </form>
          {acceptanceMutation.isError && (
            <div className="mt-4 rounded-lg border border-red-200 bg-[var(--fs-danger-soft)] p-4 text-sm text-[var(--fs-danger)]">
              {acceptanceMutation.error.message}
            </div>
          )}
          {isAccepted && (
            <div className="mt-4 rounded-lg border border-emerald-200 bg-[var(--fs-success-soft)] p-4 text-sm text-[var(--fs-success)]">
              Acceptance recorded. Agreement code and version matched.
            </div>
          )}
        </div>
      </Panel>

      <Panel className="grid gap-4 md:grid-cols-3">
        <Metric label="Agreement code" value={displayAgreement.agreement_code} />
        <Metric label="Version" value={displayAgreement.version_number.toString()} />
        <Metric label="Acceptance status" value={displayAgreement.acceptance_status} />
      </Panel>

      {isAccepted && (
        <Panel className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
          <div>
            <h2 className="text-base font-bold">Ready to record evidence</h2>
            <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
              Add delivery and invoice evidence to build the timeline.
              {acceptanceEvidence && (
                <span className="mt-2 block text-xs text-[var(--fs-text-subtle)]">
                  Acceptance hash: {acceptanceEvidence.content_hash.slice(0, 8)}
                </span>
              )}
            </p>
          </div>
          <Link className="btn-primary justify-center" to={`/evidence/${projectId}`}>
            Open evidence timeline
          </Link>
        </Panel>
      )}
    </div>
  );
}

function EvidencePage({
  auditQueryKey,
  isLoading,
  projectDetail,
  projectError,
  projectId,
  projectQueryKey,
  timeline,
  timelineQueryKey,
}: {
  auditQueryKey: readonly unknown[];
  isLoading: boolean;
  projectDetail: ProjectDetailResponse | undefined;
  projectError: Error | null;
  projectId: string | undefined;
  projectQueryKey: readonly unknown[];
  timeline: TimelineResponse | undefined;
  timelineQueryKey: readonly unknown[];
}) {
  const queryClient = useQueryClient();
  const [deliverySummary, setDeliverySummary] = useState(
    "Synthetic poster delivery recorded.",
  );
  const [invoiceSummary, setInvoiceSummary] = useState(
    "Synthetic invoice INV-DEMO-001 recorded.",
  );
  const [invoiceDueDate, setInvoiceDueDate] = useState("2026-07-13");
  const deliveryMutation = useMutation({
    mutationFn: () =>
      recordEvidence(projectId!, {
        event_type: "DELIVERY",
        invoice_due_date: null,
        summary: deliverySummary,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: projectQueryKey });
      void queryClient.invalidateQueries({ queryKey: timelineQueryKey });
      void queryClient.invalidateQueries({ queryKey: auditQueryKey });
    },
  });
  const invoiceMutation = useMutation({
    mutationFn: () =>
      recordEvidence(projectId!, {
        event_type: "INVOICE",
        invoice_due_date: invoiceDueDate,
        summary: invoiceSummary,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: projectQueryKey });
      void queryClient.invalidateQueries({ queryKey: timelineQueryKey });
      void queryClient.invalidateQueries({ queryKey: auditQueryKey });
    },
  });

  if (!projectId) {
    return (
      <Panel className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <h2 className="text-base font-bold">No project selected</h2>
          <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
            Complete intake, agreement, and acceptance before recording evidence.
          </p>
        </div>
        <Link className="btn-primary justify-center" to="/intake">
          Open intake
        </Link>
      </Panel>
    );
  }

  if (isLoading) {
    return (
      <Panel>
        <h2 className="text-base font-bold">Loading evidence timeline</h2>
        <p className="mt-2 text-sm text-[var(--fs-text-muted)]">
          Fetching project state, evidence rows, and audit context.
        </p>
      </Panel>
    );
  }

  if (projectError) {
    return (
      <Panel>
        <h2 className="text-base font-bold text-[var(--fs-danger)]">
          Evidence data unavailable
        </h2>
        <p className="mt-2 text-sm text-[var(--fs-text-muted)]">
          {projectError.message}
        </p>
      </Panel>
    );
  }

  const project = projectDetail?.project;
  const agreement = projectDetail?.current_agreement;
  const timelineEvents = timeline?.events ?? [];
  const optimisticEvents = [
    ...timelineEvents,
    ...(deliveryMutation.data ? [toTimelineEvent(deliveryMutation.data.evidence)] : []),
    ...(invoiceMutation.data ? [toTimelineEvent(invoiceMutation.data.evidence)] : []),
  ];
  const hasDelivery = optimisticEvents.some((event) => event.event_type === "DELIVERY");
  const hasInvoice = optimisticEvents.some((event) => event.event_type === "INVOICE");
  const isAccepted = agreement?.acceptance_status === "ACCEPTED";

  if (!agreement || !isAccepted) {
    return (
      <Panel className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <h2 className="text-base font-bold">Acceptance required</h2>
          <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
            Record exact agreement acceptance before adding delivery or invoice evidence.
          </p>
        </div>
        <Link className="btn-primary justify-center" to={`/acceptance/${projectId}`}>
          Open acceptance
        </Link>
      </Panel>
    );
  }

  function handleDeliverySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!deliverySummary.trim()) {
      return;
    }
    deliveryMutation.mutate();
  }

  function handleInvoiceSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!invoiceSummary.trim() || !invoiceDueDate) {
      return;
    }
    invoiceMutation.mutate();
  }

  return (
    <div className="space-y-4">
      <Panel className="grid gap-4 md:grid-cols-3">
        <Metric
          label="Agreement"
          value={`${agreement.agreement_code} V${agreement.version_number}`}
        />
        <Metric label="Evidence events" value={optimisticEvents.length.toString()} />
        <Metric label="Current state" value={project?.status ?? "ACCEPTED"} />
      </Panel>

      <Panel className="grid gap-4 lg:grid-cols-2">
        <form className="space-y-3" onSubmit={handleDeliverySubmit}>
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-base font-bold">Delivery evidence</h2>
            <StatusChip tone={hasDelivery ? "success" : "neutral"}>
              {hasDelivery ? "RECORDED" : "READY"}
            </StatusChip>
          </div>
          <textarea
            className="min-h-24 w-full resize-y rounded-lg border border-[var(--fs-border)] bg-[var(--fs-surface-muted)] p-4 text-sm outline-none focus:border-[var(--fs-primary)]"
            onChange={(event) => setDeliverySummary(event.target.value)}
            value={deliverySummary}
          />
          <button
            className="btn-primary disabled:cursor-not-allowed disabled:opacity-50"
            disabled={deliveryMutation.isPending || !deliverySummary.trim()}
            type="submit"
          >
            {deliveryMutation.isPending ? "Recording delivery..." : "Record delivery"}
          </button>
          {deliveryMutation.isError && (
            <p className="text-sm text-[var(--fs-danger)]" role="alert">
              {deliveryMutation.error.message}
            </p>
          )}
        </form>

        <form className="space-y-3" onSubmit={handleInvoiceSubmit}>
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-base font-bold">Invoice evidence</h2>
            <StatusChip tone={hasInvoice ? "success" : "neutral"}>
              {hasInvoice ? "RECORDED" : "READY"}
            </StatusChip>
          </div>
          <textarea
            className="min-h-24 w-full resize-y rounded-lg border border-[var(--fs-border)] bg-[var(--fs-surface-muted)] p-4 text-sm outline-none focus:border-[var(--fs-primary)]"
            onChange={(event) => setInvoiceSummary(event.target.value)}
            value={invoiceSummary}
          />
          <label className="block text-sm font-bold text-[var(--fs-text-muted)]">
            Invoice due date
            <input
              className="mt-1 h-10 w-full rounded-lg border border-[var(--fs-border)] bg-white px-3 text-sm text-[var(--fs-text)] outline-none focus:border-[var(--fs-primary)]"
              onChange={(event) => setInvoiceDueDate(event.target.value)}
              type="date"
              value={invoiceDueDate}
            />
          </label>
          <button
            className="btn-primary disabled:cursor-not-allowed disabled:opacity-50"
            disabled={invoiceMutation.isPending || !invoiceSummary.trim() || !invoiceDueDate}
            type="submit"
          >
            {invoiceMutation.isPending ? "Creating invoice..." : "Create invoice"}
          </button>
          {invoiceMutation.isError && (
            <p className="text-sm text-[var(--fs-danger)]" role="alert">
              {invoiceMutation.error.message}
            </p>
          )}
        </form>
      </Panel>

      <Panel>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-bold">Chronological case file</h2>
            <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
              Hashes are integrity aids only. They do not prove legal ownership or admissibility.
            </p>
          </div>
          {hasInvoice ? (
            <Link className="btn-primary" to={`/follow-up/${projectId}`}>
              Run follow-up policy
            </Link>
          ) : (
            <button className="btn-primary opacity-50" disabled type="button">
              Run follow-up policy
            </button>
          )}
        </div>
        <ol className="mt-6 space-y-4">
          {optimisticEvents.length === 0 ? (
            <li className="rounded-lg bg-[var(--fs-surface-muted)] p-4 text-sm text-[var(--fs-text-muted)]">
              No evidence events recorded yet.
            </li>
          ) : (
            optimisticEvents.map((event, index) => (
              <li
                className="grid gap-4 border-l border-[var(--fs-border)] pl-5 md:grid-cols-[160px_1fr_auto]"
                key={`${event.event_type}-${event.reference_id}-${index}`}
              >
                <div>
                  <span className="grid h-8 w-8 place-items-center rounded-full bg-[var(--fs-primary-soft)] text-sm font-bold text-[var(--fs-primary)]">
                    {index + 1}
                  </span>
                  <p className="mt-2 text-xs text-[var(--fs-text-subtle)]">
                    {formatTraceTime(event.timestamp)}
                  </p>
                </div>
                <div>
                  <h3 className="font-bold">
                    {titleCase(event.event_type.replaceAll("_", " ").toLowerCase())}
                  </h3>
                  <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
                    {event.summary}
                  </p>
                </div>
                <span className="mono-chip">
                  sha:{(event.content_hash ?? event.reference_id).slice(0, 6)}
                </span>
              </li>
            ))
          )}
        </ol>
      </Panel>
    </div>
  );
}

function FollowUpPage({
  auditQueryKey,
  isLoading,
  projectDetail,
  projectError,
  projectId,
  projectQueryKey,
}: {
  auditQueryKey: readonly unknown[];
  isLoading: boolean;
  projectDetail: ProjectDetailResponse | undefined;
  projectError: Error | null;
  projectId: string | undefined;
  projectQueryKey: readonly unknown[];
}) {
  const queryClient = useQueryClient();
  const [disputeMessage, setDisputeMessage] = useState(
    "The poster is incomplete. I will not pay.",
  );
  const followUpMutation = useMutation({
    mutationFn: (payload: FollowUpPayload) => requestFollowUp(projectId!, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: projectQueryKey });
      void queryClient.invalidateQueries({ queryKey: auditQueryKey });
    },
  });

  if (!projectId) {
    return (
      <Panel className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <h2 className="text-base font-bold">No project selected</h2>
          <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
            Complete intake, agreement, acceptance, and evidence before follow-up.
          </p>
        </div>
        <Link className="btn-primary justify-center" to="/intake">
          Open intake
        </Link>
      </Panel>
    );
  }

  if (isLoading) {
    return (
      <Panel>
        <h2 className="text-base font-bold">Loading follow-up context</h2>
        <p className="mt-2 text-sm text-[var(--fs-text-muted)]">
          Fetching project state, latest policy, draft, and audit context.
        </p>
      </Panel>
    );
  }

  if (projectError) {
    return (
      <Panel>
        <h2 className="text-base font-bold text-[var(--fs-danger)]">
          Follow-up data unavailable
        </h2>
        <p className="mt-2 text-sm text-[var(--fs-text-muted)]">
          {projectError.message}
        </p>
      </Panel>
    );
  }

  const project = projectDetail?.project;
  const currentAgreement = projectDetail?.current_agreement;
  const latestPolicy = followUpMutation.data?.policy ?? projectDetail?.latest_policy;
  const latestDraft = followUpMutation.data?.draft ?? projectDetail?.latest_draft;
  const latestSafety = followUpMutation.data?.safety;
  const isFollowUpReady = ["INVOICED", "OVERDUE", "DISPUTED"].includes(
    project?.status ?? "",
  );

  if (!project || !isFollowUpReady) {
    return (
      <Panel className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <h2 className="text-base font-bold">Invoice evidence required</h2>
          <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
            Record delivery and invoice evidence before requesting a follow-up policy decision.
          </p>
        </div>
        <Link className="btn-primary justify-center" to={`/evidence/${projectId}`}>
          Open evidence
        </Link>
      </Panel>
    );
  }

  function handleEvaluateCurrentStatus() {
    followUpMutation.mutate({ dispute: null });
  }

  function handleDisputeSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!disputeMessage.trim()) {
      return;
    }
    followUpMutation.mutate({
      dispute: {
        declared: true,
        message: disputeMessage.trim(),
      },
    });
  }

  return (
    <div className="space-y-4">
      <Panel className="grid gap-4 md:grid-cols-4">
        <Metric
          label="Agreement"
          value={currentAgreement?.acceptance_status ?? "UNKNOWN"}
        />
        <Metric label="Invoice due" value={project.invoice_due_date ?? "Not recorded"} />
        <Metric label="Project state" value={project.status} />
        <Metric label="Dispute" value={project.dispute_flag ? "Active" : "Not flagged"} />
      </Panel>

      <Panel>
        <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-start">
          <form className="space-y-3" onSubmit={handleDisputeSubmit}>
            <div>
              <h2 className="text-base font-bold">Client dispute simulation</h2>
              <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
                The message is stored as untrusted evidence for deterministic policy evaluation.
              </p>
            </div>
            <textarea
              className="min-h-24 w-full resize-y rounded-lg border border-[var(--fs-border)] bg-[var(--fs-surface-muted)] p-4 text-sm outline-none focus:border-[var(--fs-primary)]"
              onChange={(event) => setDisputeMessage(event.target.value)}
              value={disputeMessage}
            />
            <div className="flex flex-wrap gap-3">
              <button
                className="btn-primary disabled:cursor-not-allowed disabled:opacity-50"
                disabled={followUpMutation.isPending || !disputeMessage.trim()}
                type="submit"
              >
                {followUpMutation.isPending
                  ? "Evaluating dispute..."
                  : "Simulate client dispute"}
              </button>
              <button
                className="btn-secondary disabled:cursor-not-allowed disabled:opacity-50"
                disabled={followUpMutation.isPending}
                onClick={handleEvaluateCurrentStatus}
                type="button"
              >
                Evaluate current status
              </button>
            </div>
            {followUpMutation.isError && (
              <p className="text-sm text-[var(--fs-danger)]" role="alert">
                {followUpMutation.error.message}
              </p>
            )}
          </form>
          <div className="rounded-lg bg-[var(--fs-surface-muted)] p-4 text-sm text-[var(--fs-text-muted)] lg:w-64">
            <p className="font-bold text-[var(--fs-text)]">Safety gate</p>
            <p className="mt-2 leading-6">
              FollowUpAgent requests policy first. SafetyAuditAgent must approve the returned draft before display.
            </p>
          </div>
        </div>
      </Panel>

      {latestPolicy ? (
        <PolicyDecisionPanel
          allowedLabels={[`${latestPolicy.allowed_draft_type} allowed`]}
          blockedLabels={latestPolicy.blocked_draft_types.map(
            (draftType) => `${draftType} blocked`,
          )}
          title={policyTitle(latestPolicy)}
          tone={policyTone(latestPolicy)}
        >
          {policyReason(latestPolicy.reason_codes)}
        </PolicyDecisionPanel>
      ) : (
        <Panel>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-bold text-[var(--fs-primary)]">Policy decision</p>
              <h2 className="mt-1 text-xl font-bold">Not requested yet</h2>
            </div>
            <StatusChip tone="neutral">PENDING</StatusChip>
          </div>
        </Panel>
      )}

      {latestSafety && (
        <Panel>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-bold text-[var(--fs-primary)]">Safety audit</p>
              <h2 className="mt-1 text-xl font-bold">
                {latestSafety.safe_to_show ? "Draft approved to show" : "Draft blocked"}
              </h2>
            </div>
            <StatusChip tone={latestSafety.blocked ? "danger" : "success"}>
              {latestSafety.blocked ? "BLOCKED" : "APPROVED"}
            </StatusChip>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {[...latestSafety.warnings, ...latestSafety.blocked_reasons].map((item) => (
              <span className="mono-chip" key={item}>
                {item}
              </span>
            ))}
          </div>
        </Panel>
      )}

      {latestDraft ? (
        <DraftReviewPanel body={latestDraft.body} draftType={latestDraft.draft_type} />
      ) : (
        <Panel>
          <h2 className="text-base font-bold">No draft available</h2>
          <p className="mt-2 text-sm text-[var(--fs-text-muted)]">
            A communication draft appears only after policy evaluation and safety review.
          </p>
        </Panel>
      )}
    </div>
  );
}

function AuditPage({
  audit,
  isLoading,
  projectDetail,
  projectError,
  projectId,
}: {
  audit: AuditResponse | undefined;
  isLoading: boolean;
  projectDetail: ProjectDetailResponse | undefined;
  projectError: Error | null;
  projectId: string | undefined;
}) {
  if (!projectId) {
    return (
      <Panel className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <h2 className="text-base font-bold">No project selected</h2>
          <p className="mt-1 text-sm text-[var(--fs-text-muted)]">
            Complete the workflow before reviewing trace and audit history.
          </p>
        </div>
        <Link className="btn-primary justify-center" to="/intake">
          Open intake
        </Link>
      </Panel>
    );
  }

  if (isLoading) {
    return (
      <Panel>
        <h2 className="text-base font-bold">Loading audit trail</h2>
        <p className="mt-2 text-sm text-[var(--fs-text-muted)]">
          Fetching backend trace rows and append-only audit events.
        </p>
      </Panel>
    );
  }

  if (projectError) {
    return (
      <Panel>
        <h2 className="text-base font-bold text-[var(--fs-danger)]">
          Audit data unavailable
        </h2>
        <p className="mt-2 text-sm text-[var(--fs-text-muted)]">
          {projectError.message}
        </p>
      </Panel>
    );
  }

  const backendTraceRows = projectDetail ? toTraceRows(projectDetail.latest_trace) : [];
  const backendAuditRows = audit ? toAuditRows(audit) : [];
  const safetyChecks = buildSafetyChecks(projectDetail);

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Panel>
        <h2 className="text-base font-bold">Agent trace</h2>
        <div className="mt-4 divide-y divide-[var(--fs-border)]">
          {backendTraceRows.length === 0 ? (
            <div className="py-5 text-sm text-[var(--fs-text-muted)]">
              No backend trace rows returned yet.
            </div>
          ) : (
            backendTraceRows.map((row) => (
              <TraceRow
                action={row.action}
                actor={row.actor}
                key={`${row.actor}-${row.action}-${row.time}`}
                time={row.time}
                tone={row.tone}
              />
            ))
          )}
        </div>
      </Panel>
      <Panel>
        <h2 className="text-base font-bold">Append-only audit trail</h2>
        <div className="mt-4 space-y-4">
          {backendAuditRows.length === 0 ? (
            <div className="rounded-lg bg-[var(--fs-surface-muted)] p-4 text-sm text-[var(--fs-text-muted)]">
              No audit events returned yet.
            </div>
          ) : (
            backendAuditRows.map((row) => (
              <div
                className="grid grid-cols-[72px_1fr] gap-4 text-sm"
                key={`${row.title}-${row.time}`}
              >
                <span className="text-xs text-[var(--fs-text-subtle)]">{row.time}</span>
                <div>
                  <h3 className="font-bold">{row.title}</h3>
                  <p className="mt-1 text-[var(--fs-text-muted)]">{row.detail}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </Panel>
      <Panel className="xl:col-span-2">
        <h2 className="text-base font-bold">Safety boundaries verified</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {safetyChecks.map((item) => (
            <div
              className="flex items-center justify-between gap-3 rounded-lg bg-[var(--fs-surface-muted)] p-3 text-sm"
              key={item.label}
            >
              <span className="font-semibold text-[var(--fs-text)]">{item.label}</span>
              <StatusChip tone={item.tone}>{item.status}</StatusChip>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function FactsPanel({
  facts,
  sourcePlatform,
}: {
  facts: IntakeAnalyseResponse["extracted_facts"] | undefined;
  sourcePlatform: string;
}) {
  const factRows = facts ? buildFactRows(facts, sourcePlatform) : [];

  return (
    <Panel>
      <h2 className="text-base font-bold">
        Extracted facts{" "}
        <span className="font-normal text-[var(--fs-text-muted)]">(only what's stated)</span>
      </h2>
      <div className="mt-4 divide-y divide-[var(--fs-border)] overflow-hidden rounded-lg border border-[var(--fs-border)]">
        {factRows.length === 0 ? (
          <div className="bg-white px-4 py-5 text-sm text-[var(--fs-text-muted)]">
            No intake analysis yet.
          </div>
        ) : (
          factRows.map(([label, value, status]) => (
            <div
              className="grid grid-cols-[1fr_1fr_auto] items-center gap-4 bg-white px-4 py-3 text-sm"
              key={label}
            >
              <span className="font-bold">{label}</span>
              <span className="text-[var(--fs-text-muted)]">{value}</span>
              <StatusChip tone={factTone(status)}>{status}</StatusChip>
            </div>
          ))
        )}
      </div>
    </Panel>
  );
}

function WarningPanel({
  action,
  children,
  title,
}: {
  action: string;
  children: ReactNode;
  title: string;
}) {
  return (
    <div className="rounded-xl border border-amber-300 bg-[var(--fs-warning-soft)] p-4">
      <div className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <h2 className="font-bold text-[var(--fs-text)]">{title}</h2>
          <p className="mt-1 text-sm text-[var(--fs-text-muted)]">{children}</p>
        </div>
        <button className="btn-warning" type="button">
          {action}
        </button>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-[var(--fs-surface-muted)] p-4">
      <p className="text-xs font-semibold text-[var(--fs-text-muted)]">{label}</p>
      <p className="mt-1 text-lg font-bold tracking-[-0.012em]">{value}</p>
    </div>
  );
}

function DocumentField({
  label,
  unresolved,
  value,
}: {
  label: string;
  unresolved?: boolean;
  value: string;
}) {
  return (
    <div className="grid gap-2 md:grid-cols-[150px_1fr]">
      <span className="font-bold">{label}</span>
      <span
        className={classNames(
          "rounded-md px-2 py-1",
          unresolved ? "bg-[var(--fs-warning-soft)] text-[var(--fs-warning)]" : "bg-[var(--fs-surface-muted)]",
        )}
      >
        {value}
      </span>
    </div>
  );
}

function EditableDocumentField({
  label,
  onChange,
  readOnly,
  unresolved,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  readOnly: boolean;
  unresolved?: boolean;
  value: string;
}) {
  if (readOnly) {
    return (
      <DocumentField
        label={label}
        unresolved={unresolved || !value}
        value={value || "Unresolved"}
      />
    );
  }

  return (
    <div className="grid gap-2 md:grid-cols-[150px_1fr]">
      <span className="font-bold">{label}</span>
      <input
        className={classNames(
          "rounded-md border px-2 py-1 outline-none focus:border-[var(--fs-primary)]",
          unresolved || !value
            ? "border-amber-300 bg-[var(--fs-warning-soft)] text-[var(--fs-warning)]"
            : "border-[var(--fs-border)] bg-[var(--fs-surface-muted)]",
        )}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Unresolved"
        value={value}
      />
    </div>
  );
}

function AssistantRow({
  label,
  value,
  warning,
}: {
  label: string;
  value: string;
  warning?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg bg-[var(--fs-surface-muted)] px-3 py-2 text-sm">
      <span className="text-[var(--fs-text-muted)]">{label}</span>
      <span className={classNames("font-bold", warning && "text-[var(--fs-warning)]")}>{value}</span>
    </div>
  );
}

type FactRow = [string, string, "Extracted" | "Identified" | "Not stated"];

function buildFactRows(
  facts: IntakeAnalyseResponse["extracted_facts"],
  sourcePlatform: string,
): FactRow[] {
  const hasRisk = facts.risk_flags.includes("informal_platform");

  return [
    ["Project title", facts.project_title, "Extracted"],
    ["Amount", formatAmount(facts.amount, facts.currency), factStatus(facts.amount)],
    ["Currency", facts.currency ?? "Unresolved", factStatus(facts.currency)],
    ["Deadline", facts.deadline ?? "Unresolved", factStatus(facts.deadline)],
    [
      "Revision limit",
      facts.revision_limit?.toString() ?? "Unresolved",
      factStatus(facts.revision_limit),
    ],
    [
      "Payment terms",
      facts.payment_terms ?? "Unresolved",
      factStatus(facts.payment_terms),
    ],
    [
      "Source platform risk",
      hasRisk ? `Informal platform (${sourcePlatform})` : "None detected",
      hasRisk ? "Identified" : "Not stated",
    ],
  ];
}

function factStatus(value: unknown): "Extracted" | "Not stated" {
  return value === null || value === undefined ? "Not stated" : "Extracted";
}

function factTone(status: FactRow[2]) {
  if (status === "Extracted") {
    return "success";
  }
  if (status === "Identified") {
    return "info";
  }
  return "warning";
}

function policyTitle(policy: FollowUpResponse["policy"]) {
  if (
    policy.allowed_draft_type === "DISPUTE_CLARIFICATION" &&
    policy.blocked_draft_types.includes("PAYMENT_REMINDER")
  ) {
    return "Payment reminder blocked";
  }
  if (policy.allowed_draft_type === "PAYMENT_REMINDER") {
    return "Payment reminder allowed";
  }
  if (policy.allowed_draft_type === "DELIVERY_CONFIRMATION") {
    return "Delivery confirmation allowed";
  }
  return "Acceptance request allowed";
}

function policyTone(
  policy: FollowUpResponse["policy"],
): "danger" | "success" | "warning" {
  if (policy.blocked_draft_types.includes("PAYMENT_REMINDER")) {
    return policy.allowed_draft_type === "DISPUTE_CLARIFICATION" ? "danger" : "warning";
  }
  return "success";
}

function policyReason(reasonCodes: string[]) {
  const labels: Record<string, string> = {
    INVOICE_OVERDUE:
      "The invoice due date has passed, so a gentle payment reminder is permitted.",
    NO_ACCEPTED_AGREEMENT:
      "Agreement acceptance is missing, so the workflow can only request acceptance.",
    NO_OVERDUE_INVOICE:
      "The invoice is not overdue, so the workflow blocks payment-reminder wording.",
    PROJECT_DISPUTED:
      "Client dispute is recorded, so only a neutral clarification draft is allowed.",
  };

  return reasonCodes.map((code) => labels[code] ?? titleCase(code)).join(" ");
}

function buildSafetyChecks(
  projectDetail: ProjectDetailResponse | undefined,
): Array<{
  label: string;
  status: string;
  tone: "danger" | "neutral" | "success" | "warning";
}> {
  const draft = projectDetail?.latest_draft;
  const policy = projectDetail?.latest_policy;
  const disputeBlocksPayment =
    Boolean(projectDetail?.project.dispute_flag) &&
    Boolean(policy?.blocked_draft_types.includes("PAYMENT_REMINDER"));
  const draftHasWarning =
    draft?.body.includes("Draft only — review and send manually.") ?? false;

  return [
    {
      label: "No automatic sending or external contact",
      status: "ENFORCED",
      tone: "success",
    },
    {
      label: "No legal advice or enforceability claims",
      status: "ENFORCED",
      tone: "success",
    },
    {
      label: "Dispute blocks payment-demand wording",
      status: disputeBlocksPayment ? "VERIFIED" : "PENDING",
      tone: disputeBlocksPayment ? "success" : "warning",
    },
    {
      label: "Every generated communication is draft-only",
      status: draft ? (draftHasWarning ? "VERIFIED" : "MISSING") : "PENDING",
      tone: draft ? (draftHasWarning ? "success" : "danger") : "warning",
    },
  ];
}

function agreementStatusTone(status: string) {
  if (status === "ACCEPTED") {
    return "success";
  }
  if (status === "PENDING") {
    return "warning";
  }
  return "neutral";
}

function formatAmount(amount: number | null, currency: string | null) {
  if (amount === null) {
    return "Unresolved";
  }
  return `${currency ?? ""} ${amount.toLocaleString()}`.trim();
}

function amountForSubmit(
  amountOverride: string | null,
  backendAmount: number | null | undefined,
) {
  if (amountOverride !== null) {
    return amountOverride.trim() ? Number(amountOverride) : null;
  }
  return backendAmount ?? null;
}

function currencyForSubmit(
  currencyOverride: string | null,
  backendCurrency: string | null | undefined,
) {
  if (currencyOverride !== null) {
    return currencyOverride.trim() || null;
  }
  return backendCurrency ?? "MYR";
}

function formatMissingFields(fields: string[]) {
  return fields.map((field) => field.replaceAll("_", " ")).join(", ");
}

function intakeSummary(
  project: IntakeAnalyseResponse["project"] | undefined,
): ProjectSummary {
  return {
    id: project?.id ?? "Pending",
    sourcePlatform: project?.source_platform ?? "Instagram",
    status: project?.status ?? "DRAFT",
    title: project?.title ?? "New intake",
  };
}

function projectSummary(project: ProjectDetailResponse["project"]): ProjectSummary {
  return {
    id: project.id,
    sourcePlatform: project.source_platform,
    status: project.status,
    title: project.title,
  };
}

function toAuditRows(audit: AuditResponse): AuditRowData[] {
  return audit.events.map((event) => ({
    detail: formatAuditDetail(event.metadata),
    time: formatTraceTime(event.created_at),
    title: `${event.actor} ${titleCase(event.action.replaceAll("_", " "))}`,
  }));
}

function toTimelineEvent(
  evidence: NonNullable<TimelineResponse["events"][number]> | {
    content_hash: string;
    created_at: string;
    event_type: string;
    id: string;
    summary: string;
  },
): TimelineResponse["events"][number] {
  if ("timestamp" in evidence) {
    return evidence;
  }

  return {
    content_hash: evidence.content_hash,
    event_type: evidence.event_type,
    reference_id: evidence.id,
    summary: evidence.summary,
    timestamp: evidence.created_at,
  };
}

function formatAuditDetail(metadata: Record<string, unknown>) {
  const entries = Object.entries(metadata);
  if (entries.length === 0) {
    return "Audit event recorded";
  }
  return entries
    .map(([key, value]) => `${key.replaceAll("_", " ")}: ${String(value)}`)
    .join(", ");
}

function toTraceRows(
  trace: IntakeAnalyseResponse["trace"] | ProjectDetailResponse["latest_trace"],
): TraceRowData[] {
  return trace.map((event) => ({
    action: titleCase(event.action.replaceAll("_", " ")),
    actor: event.actor,
    time: formatTraceTime(event.timestamp),
    tone: event.status === "SUCCEEDED" ? ("success" as const) : ("info" as const),
  }));
}

function titleCase(value: string) {
  return value.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatTraceTime(timestamp: string) {
  return new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(timestamp));
}
