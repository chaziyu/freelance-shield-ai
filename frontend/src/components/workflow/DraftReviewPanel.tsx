import { useState } from "react";

import { Panel } from "./Panel";
import { StatusChip } from "./StatusChip";

interface DraftReviewPanelProps {
  body: string;
  draftType: string;
}

export function DraftReviewPanel({ body, draftType }: DraftReviewPanelProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    if (!navigator.clipboard) {
      return;
    }
    await navigator.clipboard.writeText(body);
    setCopied(true);
  }

  return (
    <Panel>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-bold text-[var(--fs-primary)]">{draftType}</p>
          <h2 className="mt-1 text-xl font-bold">Draft review</h2>
        </div>
        <StatusChip tone="warning">Draft only — review and send manually.</StatusChip>
      </div>
      <div className="mt-5 whitespace-pre-line rounded-xl border border-[var(--fs-border)] bg-white p-5 text-[15px] leading-6">
        {body}
      </div>
      <div className="mt-5 flex flex-wrap items-center justify-between gap-4">
        <p className="text-sm text-[var(--fs-text-muted)]">No message will be sent.</p>
        <button className="btn-primary" onClick={handleCopy} type="button">
          {copied ? "Copied" : "Copy draft"}
        </button>
      </div>
    </Panel>
  );
}
