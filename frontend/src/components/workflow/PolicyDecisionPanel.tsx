import type { ReactNode } from "react";

import { Panel } from "./Panel";
import { StatusChip } from "./StatusChip";
import type { ChipTone } from "./types";

interface PolicyDecisionPanelProps {
  allowedLabels: string[];
  blockedLabels?: string[];
  children: ReactNode;
  title: string;
  tone: Extract<ChipTone, "danger" | "success" | "warning">;
}

const toneClasses = {
  danger: "border-[var(--fs-danger-soft)] bg-[var(--fs-danger-soft)] text-[var(--fs-danger)]",
  success: "border-[var(--fs-success-soft)] bg-[var(--fs-success-soft)] text-[var(--fs-success)]",
  warning: "border-amber-300 bg-[var(--fs-warning-soft)] text-[var(--fs-warning)]",
};

export function PolicyDecisionPanel({
  allowedLabels,
  blockedLabels = [],
  children,
  title,
  tone,
}: PolicyDecisionPanelProps) {
  return (
    <Panel className={toneClasses[tone]}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-bold">Policy decision</p>
          <h2 className="mt-1 text-xl font-bold">{title}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--fs-text)]">{children}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {blockedLabels.map((label) => (
            <StatusChip key={label} tone="danger">
              {label}
            </StatusChip>
          ))}
          {allowedLabels.map((label) => (
            <StatusChip key={label} tone="success">
              {label}
            </StatusChip>
          ))}
        </div>
      </div>
    </Panel>
  );
}
