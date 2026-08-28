import type { ReactNode } from "react";
import { AlertTriangle, Inbox, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

/* ------------------------------------------------------------------ */
/* Loading                                                              */
/* ------------------------------------------------------------------ */

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn("relative overflow-hidden rounded-md bg-surface-overlay", className)}>
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/[0.045] to-transparent" />
    </div>
  );
}

interface LoadingStateProps {
  label?: string;
  /** Height of the placeholder block, e.g. "h-64". */
  className?: string;
  variant?: "block" | "rows" | "cards";
  rows?: number;
}

export function LoadingState({
  label = "Loading",
  className,
  variant = "block",
  rows = 4,
}: LoadingStateProps) {
  if (variant === "rows") {
    return (
      <div className={cn("space-y-2", className)} role="status" aria-label={label}>
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }
  if (variant === "cards") {
    return (
      <div className={cn("grid gap-3 sm:grid-cols-2 xl:grid-cols-4", className)} role="status" aria-label={label}>
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full" />
        ))}
      </div>
    );
  }
  return (
    <div className={cn("flex items-center justify-center", className ?? "h-48")} role="status" aria-label={label}>
      <div className="flex items-center gap-2 text-xs text-content-faint">
        <RefreshCw className="h-3.5 w-3.5 animate-spin" aria-hidden />
        {label}…
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Empty                                                                */
/* ------------------------------------------------------------------ */

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ title, description, icon, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-line-strong px-6 py-10 text-center",
        className,
      )}
    >
      <div className="text-content-faint">{icon ?? <Inbox className="h-5 w-5" aria-hidden />}</div>
      <p className="text-sm font-medium text-content">{title}</p>
      {description ? (
        <p className="max-w-md text-xs leading-relaxed text-content-muted">{description}</p>
      ) : null}
      {action ? <div className="mt-1">{action}</div> : null}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Error                                                                */
/* ------------------------------------------------------------------ */

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({ title = "Could not load this data", message, onRetry, className }: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-2 rounded-lg border border-crit/30 bg-crit/[0.06] px-6 py-8 text-center",
        className,
      )}
      role="alert"
    >
      <AlertTriangle className="h-5 w-5 text-crit" aria-hidden />
      <p className="text-sm font-medium text-content">{title}</p>
      <p className="max-w-md text-xs leading-relaxed text-content-muted">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-1 inline-flex items-center gap-1.5 rounded-md border border-line-strong bg-surface-overlay px-2.5 py-1.5 text-xs font-medium text-content transition-colors hover:border-info/40 hover:text-info"
        >
          <RefreshCw className="h-3 w-3" aria-hidden />
          Retry
        </button>
      ) : null}
    </div>
  );
}
