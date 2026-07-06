import { Link } from "react-router-dom";

import { classNames } from "./classNames";
import type { StepMeta, WorkflowStep } from "./types";

interface MobileStepNavProps {
  activeStep: WorkflowStep;
  steps: StepMeta[];
}

export function MobileStepNav({ activeStep, steps }: MobileStepNavProps) {
  return (
    <nav
      aria-label="Mobile workflow steps"
      className="fixed inset-x-0 bottom-0 z-20 border-t border-[var(--fs-border)] bg-white px-2 py-2 shadow-[0_-8px_24px_rgba(16,32,51,0.08)] lg:hidden"
    >
      <div className="grid grid-cols-6 gap-1">
        {steps.map((step, index) => {
          const isActive = step.id === activeStep;

          return (
            <Link
              className={classNames(
                "flex min-h-12 flex-col items-center justify-center rounded-lg px-1 text-[10px] font-bold transition-transform active:scale-95",
                isActive
                  ? "bg-[var(--fs-primary-soft)] text-[var(--fs-primary)]"
                  : "text-[var(--fs-text-muted)]",
              )}
              key={step.id}
              to={step.path}
            >
              <span className="tabular-nums">{index + 1}</span>
              <span>{step.shortLabel}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
