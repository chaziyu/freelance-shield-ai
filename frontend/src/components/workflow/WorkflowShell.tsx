import type { ReactNode } from "react";

import { MobileStepNav } from "./MobileStepNav";
import { ProjectHeader } from "./ProjectHeader";
import { SafetyPanel } from "./SafetyPanel";
import type {
  AuditRowData,
  PageCopy,
  ProjectSummary,
  TraceRowData,
  WorkflowStep,
} from "./types";
import {
  auditRows as scaffoldAuditRows,
  traceRows as scaffoldTraceRows,
  workflowSteps,
} from "./workflowData";
import { WorkflowSidebar } from "./WorkflowSidebar";

interface WorkflowShellProps {
  activeStatus?: string;
  activeStep: WorkflowStep;
  auditRows?: AuditRowData[];
  children: ReactNode;
  pageCopy: PageCopy;
  projectSummary?: ProjectSummary;
  traceRows?: TraceRowData[];
}

export function WorkflowShell({
  activeStatus,
  activeStep,
  auditRows,
  children,
  pageCopy,
  projectSummary,
  traceRows,
}: WorkflowShellProps) {
  const shellTraceRows = traceRows ?? scaffoldTraceRows;
  const shellAuditRows = auditRows ?? scaffoldAuditRows;
  const projectId = projectSummary?.id;
  const hasProjectId = Boolean(projectId && projectId !== "Pending");
  const steps = workflowSteps.map((step) =>
    step.id === activeStep && activeStatus
      ? {
          ...step,
          path: stepPath(step.id, hasProjectId ? projectId : undefined),
          status: activeStatus,
        }
      : { ...step, path: stepPath(step.id, hasProjectId ? projectId : undefined) },
  );

  return (
    <div className="min-h-screen bg-[var(--fs-canvas)] pb-20 text-[var(--fs-text)] lg:pb-0">
      <div className="grid min-h-screen lg:grid-cols-[280px_minmax(0,1fr)]">
        <WorkflowSidebar activeStep={activeStep} steps={steps} />

        <div className="min-w-0">
          <ProjectHeader
            activeStatus={activeStatus}
            activeStep={activeStep}
            projectSummary={projectSummary}
          />

          <main className="grid gap-6 px-4 py-6 xl:grid-cols-[minmax(0,1fr)_360px] lg:px-6">
            <section className="min-w-0">
              <div className="mb-5">
                <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--fs-primary)]">
                  {pageCopy.eyebrow}
                </p>
                <h1 className="mt-1 text-2xl font-bold tracking-[-0.012em] text-[var(--fs-text)]">
                  {pageCopy.title}
                </h1>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--fs-text-muted)]">
                  {pageCopy.description}
                </p>
              </div>

              {children}
            </section>

            <SafetyPanel
              activeStep={activeStep}
              auditRows={shellAuditRows}
              projectId={projectId}
              traceRows={shellTraceRows}
            />
          </main>
        </div>
      </div>
      <MobileStepNav activeStep={activeStep} steps={steps} />
    </div>
  );
}

function stepPath(step: WorkflowStep, projectId?: string) {
  if (step === "intake") {
    return "/intake";
  }
  if (!projectId) {
    return `/${step}`;
  }
  return `/${step}/${projectId}`;
}
