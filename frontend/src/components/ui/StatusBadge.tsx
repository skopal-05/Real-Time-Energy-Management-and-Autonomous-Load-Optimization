import { HEALTH_STYLES, SEVERITY_STYLES } from "@/lib/constants";
import type { HealthState, Severity } from "@/lib/types";
import { cn } from "@/lib/utils";

type Size = "sm" | "md";

interface StatusBadgeProps {
  status: HealthState;
  size?: Size;
  showDot?: boolean;
  label?: string;
  className?: string;
}

const SIZES: Record<Size, string> = {
  sm: "px-1.5 py-0.5 text-2xs",
  md: "px-2 py-1 text-xs",
};

export function StatusBadge({
  status,
  size = "sm",
  showDot = true,
  label,
  className,
}: StatusBadgeProps) {
  const style = HEALTH_STYLES[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border font-medium",
        style.fg,
        style.bg,
        style.border,
        SIZES[size],
        className,
      )}
    >
      {showDot ? <StatusDot status={status} /> : null}
      {label ?? style.label}
    </span>
  );
}

export function StatusDot({ status, className }: { status: HealthState; className?: string }) {
  const style = HEALTH_STYLES[status];
  const animated = status === "warning" || status === "critical";
  return (
    <span className={cn("relative flex h-1.5 w-1.5", className)} aria-hidden>
      <span
        className={cn(
          "inline-flex h-1.5 w-1.5 rounded-full",
          animated && "animate-pulse-dot",
        )}
        style={{ backgroundColor: style.hex }}
      />
    </span>
  );
}

interface SeverityBadgeProps {
  severity: Severity;
  size?: Size;
  className?: string;
}

export function SeverityBadge({ severity, size = "sm", className }: SeverityBadgeProps) {
  const style = SEVERITY_STYLES[severity];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border font-medium uppercase tracking-wide",
        style.fg,
        style.bg,
        style.border,
        SIZES[size],
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: style.hex }} aria-hidden />
      {style.label}
    </span>
  );
}

/** Neutral pill used for non-status metadata (module names, counts, modes). */
export function Chip({
  children,
  tone = "neutral",
  className,
}: {
  children: React.ReactNode;
  tone?: "neutral" | "info" | "ok" | "warn" | "crit";
  className?: string;
}) {
  const tones: Record<string, string> = {
    neutral: "border-line-strong bg-surface-overlay text-content-muted",
    info: "border-info/30 bg-info/10 text-info",
    ok: "border-ok/30 bg-ok/10 text-ok",
    warn: "border-warn/30 bg-warn/10 text-warn",
    crit: "border-crit/30 bg-crit/10 text-crit",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-2xs font-medium",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
