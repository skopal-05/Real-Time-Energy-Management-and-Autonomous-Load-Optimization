import type { ReactNode } from "react";
import type { DataOrigin } from "@/lib/types";
import { DataOriginBadge } from "@/components/ui/DataOriginBadge";
import { Chip } from "@/components/ui/StatusBadge";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description: string;
  /** Pipeline module this page belongs to, e.g. "Random Forest". */
  module?: string;
  origin?: DataOrigin;
  actions?: ReactNode;
  className?: string;
}

/** Consistent page title block. Every route starts with one. */
export function PageHeader({
  title,
  description,
  module,
  origin,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn("mb-4 flex flex-wrap items-end justify-between gap-3", className)}>
      <div className="min-w-0 max-w-3xl">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-lg font-semibold tracking-tight text-content sm:text-xl">{title}</h2>
          {module ? <Chip tone="info">{module}</Chip> : null}
          {origin ? <DataOriginBadge origin={origin} /> : null}
        </div>
        <p className="mt-1 text-xs leading-relaxed text-content-muted sm:text-[13px]">{description}</p>
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}
