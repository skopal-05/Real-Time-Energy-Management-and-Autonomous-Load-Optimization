import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { InfoTip } from "./InfoTip";

interface PanelProps {
  children: ReactNode;
  className?: string;
}

export function Panel({ children, className }: PanelProps) {
  return <section className={cn("panel", className)}>{children}</section>;
}

interface PanelHeaderProps {
  title: string;
  /** Small grey line under the title. Keep it to one short sentence. */
  subtitle?: string;
  /** Explains a technical term on hover — used for model and metric names. */
  hint?: string;
  eyebrow?: string;
  actions?: ReactNode;
  className?: string;
}

export function PanelHeader({
  title,
  subtitle,
  hint,
  eyebrow,
  actions,
  className,
}: PanelHeaderProps) {
  return (
    <header
      className={cn(
        "flex flex-wrap items-start justify-between gap-3 border-b border-line px-4 py-3 sm:px-5",
        className,
      )}
    >
      <div className="min-w-0">
        {eyebrow ? <p className="label-eyebrow mb-1">{eyebrow}</p> : null}
        <div className="flex items-center gap-1.5">
          <h2 className="truncate text-sm font-semibold tracking-tight text-content">{title}</h2>
          {hint ? <InfoTip text={hint} /> : null}
        </div>
        {subtitle ? <p className="mt-0.5 text-xs text-content-muted">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </header>
  );
}

export function PanelBody({ children, className }: PanelProps) {
  return <div className={cn("p-4 sm:p-5", className)}>{children}</div>;
}
