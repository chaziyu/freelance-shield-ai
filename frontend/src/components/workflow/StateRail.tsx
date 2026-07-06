import { classNames } from "./classNames";
import { StatusChip } from "./StatusChip";
import type { ProjectStateMeta, WorkflowStep } from "./types";

const activeStateByStep: Record<WorkflowStep, string> = {
  acceptance: "ACCEPTED",
  agreement: "ACCEPTANCE_PENDING",
  audit: "DISPUTED",
  evidence: "INVOICED",
  "follow-up": "DISPUTED",
  intake: "TERMS_READY",
};

interface StateRailProps {
  activeStatus?: string;
  activeStep: WorkflowStep;
  states: ProjectStateMeta[];
}

export function StateRail({ activeStatus, activeStep, states }: StateRailProps) {
  const activeEnum = activeStatus ?? activeStateByStep[activeStep];

  return (
    <div className="overflow-x-auto px-4 pb-0 lg:px-6">
      <ol className="flex min-w-[960px] items-end justify-between gap-4">
        {states.map((state, index) => {
          const isActive = state.enumValue === activeEnum;

          return (
            <li
              className={classNames(
                "min-w-24 border-b-4 px-1 pb-3 text-center",
                isActive
                  ? "border-[var(--fs-primary)] text-[var(--fs-primary)]"
                  : "border-transparent text-[var(--fs-text-subtle)]",
              )}
              key={state.enumValue}
            >
              <span
                className={classNames(
                  "mx-auto mb-2 grid h-8 w-8 place-items-center rounded-full border text-[11px] font-bold tabular-nums",
                  isActive
                    ? "border-[var(--fs-primary)] bg-[var(--fs-primary-soft)]"
                    : "border-[var(--fs-border)] bg-white",
                )}
              >
                {index + 1}
              </span>
              <span className="block text-[12px] font-bold">{state.label}</span>
              {isActive && (
                <span className="mt-1 inline-block">
                  <StatusChip tone="info">{state.enumValue}</StatusChip>
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
