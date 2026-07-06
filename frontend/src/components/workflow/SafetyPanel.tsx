import { AuditPreview } from "./AuditPreview";
import { classNames } from "./classNames";
import { Panel } from "./Panel";
import { StatusChip } from "./StatusChip";
import { TraceRow } from "./TraceRow";
import type { AuditRowData, TraceRowData, WorkflowStep } from "./types";

interface SafetyPanelProps {
  activeStep: WorkflowStep;
  auditRows: AuditRowData[];
  projectId?: string;
  traceRows: TraceRowData[];
}

export function SafetyPanel({
  activeStep,
  auditRows,
  projectId,
  traceRows,
}: SafetyPanelProps) {
  const isFollowUp = activeStep === "follow-up";
  const visibleTraceRows = isFollowUp ? traceRows.slice(-1) : traceRows.slice(0, 4);

  return (
    <aside className="space-y-4">
      <Panel>
        <div className="flex items-center justify-between gap-3">
          <h2 className="font-bold">Safety review</h2>
          <StatusChip tone={isFollowUp ? "danger" : "success"}>
            {isFollowUp ? "Policy checked" : "Safe"}
          </StatusChip>
        </div>
        <div
          className={classNames(
            "mt-4 rounded-lg border p-4 text-sm",
            isFollowUp
              ? "border-red-200 bg-[var(--fs-danger-soft)] text-[var(--fs-danger)]"
              : "border-emerald-200 bg-[var(--fs-success-soft)] text-[var(--fs-success)]",
          )}
        >
          <strong>{isFollowUp ? "Payment reminder blocked" : "Workflow guardrails active"}</strong>
          <p className="mt-1 text-[var(--fs-text)]">
            {isFollowUp
              ? "Dispute policy respected. Clarification draft only."
              : "Missing fields are not guessed. Draft-only rules remain visible."}
          </p>
        </div>
        <div className="mt-4 divide-y divide-[var(--fs-border)]">
          {visibleTraceRows.length === 0 ? (
            <p className="rounded-lg bg-[var(--fs-surface-muted)] p-3 text-sm text-[var(--fs-text-muted)]">
              No agent trace loaded.
            </p>
          ) : (
            visibleTraceRows.map((row) => (
              <TraceRow
                action={row.action}
                actor={row.actor}
                key={`${row.actor}-${row.action}-panel`}
                time={row.time}
                tone={row.tone}
              />
            ))
          )}
        </div>
      </Panel>

      <Panel>
        <AuditPreview projectId={projectId} rows={auditRows} />
      </Panel>

      <Panel className="bg-[var(--fs-warning-soft)]">
        <h2 className="font-bold">Policy guardrails</h2>
        <ul className="mt-3 space-y-2 text-sm text-[var(--fs-text-muted)]">
          <li>No automatic sending or external contact</li>
          <li>No legal advice or enforceability claims</li>
          <li>Dispute or overdue rules enforced</li>
          <li>Drafts always reviewed by you</li>
        </ul>
      </Panel>
    </aside>
  );
}
