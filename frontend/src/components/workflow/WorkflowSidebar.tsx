import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { classNames } from "./classNames";
import type { StepMeta, WorkflowStep } from "./types";

interface WorkflowSidebarProps {
  activeStep: WorkflowStep;
  steps: StepMeta[];
}

export function WorkflowSidebar({ activeStep, steps }: WorkflowSidebarProps) {
  const activeIndex = steps.findIndex((step) => step.id === activeStep);

  return (
    <aside className="hidden bg-[var(--fs-sidebar)] text-white lg:flex lg:flex-col">
      <Link className="flex items-center gap-3 border-b border-white/10 px-6 py-6" to="/intake">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-[var(--fs-primary)] font-bold">
          FS
        </span>
        <span className="text-xl font-bold tracking-[-0.012em]">FreelanceShield AI</span>
      </Link>

      <nav aria-label="Workflow steps" className="flex-1 px-4 py-8">
        <ol className="space-y-3">
          {steps.map((step, index) => {
            const isActive = step.id === activeStep;
            const isComplete = index < activeIndex;

            return (
              <li key={step.id}>
                <Link
                  className={classNames(
                    "group flex min-h-14 items-center gap-3 rounded-xl px-3 py-2 text-sm font-semibold transition-transform active:scale-95",
                    isActive && "bg-white/10 text-white",
                    !isActive && "text-slate-200 hover:bg-white/5",
                  )}
                  to={step.path}
                >
                  <span
                    className={classNames(
                      "grid h-9 w-9 shrink-0 place-items-center rounded-full font-bold tabular-nums",
                      isActive && "bg-[var(--fs-primary)] text-white",
                      isComplete &&
                        !isActive &&
                        "bg-[var(--fs-primary-soft)] text-[var(--fs-primary)]",
                      !isActive && !isComplete && "bg-slate-300 text-[var(--fs-sidebar)]",
                    )}
                  >
                    {index + 1}
                  </span>
                  <span className="min-w-0 flex-1">{step.label}</span>
                  <span
                    className={classNames(
                      "rounded-full px-2 py-1 text-[11px] font-bold",
                      isActive
                        ? "bg-[var(--fs-primary-soft)] text-[var(--fs-primary)]"
                        : "bg-white/12 text-slate-200",
                    )}
                  >
                    {step.status}
                  </span>
                </Link>
              </li>
            );
          })}
        </ol>
      </nav>

      <div className="space-y-4 px-4 pb-6">
        <InfoBox title="Policy guardrails">
          Deterministic rules protect you and your client.
        </InfoBox>
        <InfoBox title="Need help?">
          Learn how drafts, evidence, and safety boundaries work.
        </InfoBox>
      </div>
    </aside>
  );
}

function InfoBox({ children, title }: { children: ReactNode; title: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-slate-200">
      <h2 className="font-bold text-white">{title}</h2>
      <p className="mt-2 leading-6 text-slate-300">{children}</p>
    </div>
  );
}
