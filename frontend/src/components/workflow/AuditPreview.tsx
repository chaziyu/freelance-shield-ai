import { Link } from "react-router-dom";

import type { AuditRowData } from "./types";

interface AuditPreviewProps {
  projectId?: string;
  rows: AuditRowData[];
}

export function AuditPreview({ projectId, rows }: AuditPreviewProps) {
  const auditPath = projectId ? `/audit/${projectId}` : "/audit";

  return (
    <div>
      <div className="flex items-center justify-between">
        <h2 className="font-bold">Audit trail</h2>
        <Link className="text-sm font-semibold text-[var(--fs-info)]" to={auditPath}>
          View all
        </Link>
      </div>
      <div className="mt-4 space-y-3">
        {rows.length === 0 ? (
          <p className="rounded-lg bg-[var(--fs-surface-muted)] p-3 text-sm text-[var(--fs-text-muted)]">
            No audit events loaded.
          </p>
        ) : (
          rows.slice(-4).map((row) => (
            <div
              className="grid grid-cols-[58px_1fr] gap-3 text-sm"
              key={`${row.title}-panel`}
            >
              <span className="text-xs text-[var(--fs-text-subtle)]">{row.time}</span>
              <div>
                <h3 className="font-bold">{row.title}</h3>
                <p className="text-xs text-[var(--fs-text-muted)]">{row.detail}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
