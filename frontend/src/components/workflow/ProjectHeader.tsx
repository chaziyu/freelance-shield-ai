import type { ReactNode } from "react";

import type { ProjectSummary, WorkflowStep } from "./types";
import { projectStates } from "./workflowData";
import { StateRail } from "./StateRail";

const gmtOffsets = Array.from({ length: 27 }, (_, index) => {
  const offset = index - 12;
  const sign = offset >= 0 ? "+" : "-";
  return `GMT${sign}${String(Math.abs(offset)).padStart(2, "0")}:00`;
});

interface ProjectHeaderProps {
  activeStatus?: string;
  activeStep: WorkflowStep;
  projectSummary?: ProjectSummary;
}

export function ProjectHeader({
  activeStatus,
  activeStep,
  projectSummary,
}: ProjectHeaderProps) {
  const project = projectSummary ?? {
    id: "Pending",
    sourcePlatform: "No project loaded",
    status: activeStatus ?? "DRAFT",
    title: "New intake",
  };
  const displayId = project.id.length > 8 ? project.id.slice(0, 8) : project.id;

  return (
    <header className="border-b border-[var(--fs-border)] bg-white">
      <div className="grid gap-4 px-4 py-3 md:grid-cols-[1fr_auto_1fr] md:items-center lg:px-6">
        <div className="inline-flex max-w-md items-center gap-3 rounded-lg border border-[var(--fs-border)] bg-white px-4 py-2 shadow-[var(--fs-shadow-sm)]">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-[var(--fs-warning-soft)] text-[var(--fs-warning)]">
            ID
          </span>
          <div>
            <p className="font-bold">{project.title}</p>
            <p className="text-xs text-[var(--fs-text-muted)]">
              ID: {displayId} <span className="mx-1">·</span> {project.sourcePlatform}
            </p>
          </div>
        </div>

        <div className="rounded-lg bg-[var(--fs-warning-soft)] px-5 py-3 text-sm text-[var(--fs-text)]">
          <strong className="text-[var(--fs-warning)]">Draft only</strong> — review and send manually.
          <span className="block text-xs text-[var(--fs-text-muted)]">
            This app never sends messages or takes action on your behalf.
          </span>
        </div>

        <div className="hidden justify-end gap-3 md:flex">
          <label className="flex h-10 items-center gap-2 rounded-full border border-[var(--fs-border)] bg-white px-3 text-xs font-bold text-[var(--fs-text-muted)]">
            Display time
            <select
              aria-label="GMT display offset"
              className="rounded-md bg-[var(--fs-surface-muted)] px-2 py-1 text-xs font-bold text-[var(--fs-text)]"
              defaultValue="GMT+08:00"
            >
              {gmtOffsets.map((offset) => (
                <option key={offset}>{offset}</option>
              ))}
            </select>
          </label>
          <CircleButton label="Help">?</CircleButton>
          <CircleButton label="Alerts">!</CircleButton>
          <span className="grid h-10 w-10 place-items-center rounded-full bg-[var(--fs-primary)] text-sm font-bold text-white">
            FS
          </span>
        </div>
      </div>

      <StateRail
        activeStatus={project.status}
        activeStep={activeStep}
        states={projectStates}
      />
    </header>
  );
}

function CircleButton({ children, label }: { children: ReactNode; label: string }) {
  return (
    <button
      aria-label={label}
      className="grid h-10 w-10 place-items-center rounded-full border border-[var(--fs-border)] bg-white text-sm font-bold transition-transform active:scale-95"
      type="button"
    >
      {children}
    </button>
  );
}
