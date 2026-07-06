import { classNames } from "./classNames";
import type { TraceTone } from "./types";

interface TraceRowProps {
  action: string;
  actor: string;
  time: string;
  tone: TraceTone;
}

export function TraceRow({ action, actor, time, tone }: TraceRowProps) {
  return (
    <div className="grid grid-cols-[1fr_auto] gap-3 py-3 text-sm">
      <div>
        <h3 className="font-bold">{actor}</h3>
        <p className="text-xs text-[var(--fs-text-muted)]">{action}</p>
      </div>
      <div className="text-right">
        <p className="text-xs text-[var(--fs-text-subtle)]">{time}</p>
        <span
          className={classNames(
            "mt-1 inline-block h-2 w-2 rounded-full",
            tone === "success" ? "bg-[var(--fs-success)]" : "bg-[var(--fs-info)]",
          )}
        />
      </div>
    </div>
  );
}
