import type { ReactNode } from "react";

import { classNames } from "./classNames";

interface PanelProps {
  children: ReactNode;
  className?: string;
}

export function Panel({ children, className }: PanelProps) {
  return <div className={classNames("panel", className)}>{children}</div>;
}
