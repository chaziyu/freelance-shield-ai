import type { ReactNode } from "react";

import type { ChipTone } from "./types";

const chipClasses: Record<ChipTone, string> = {
  danger: "status-chip status-chip-danger",
  info: "status-chip status-chip-info",
  neutral: "status-chip status-chip-neutral",
  success: "status-chip status-chip-success",
  warning: "status-chip status-chip-warning",
};

interface StatusChipProps {
  children: ReactNode;
  tone: ChipTone;
}

export function StatusChip({ children, tone }: StatusChipProps) {
  return <span className={chipClasses[tone]}>{children}</span>;
}
