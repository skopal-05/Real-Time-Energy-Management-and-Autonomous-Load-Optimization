import { cn } from "@/lib/utils";
import { clamp } from "@/lib/utils";

interface MeterProps {
  /** 0–100. Null renders a muted "no value" track. */
  value: number | null;
  label?: string;
  valueLabel?: string;
  tone?: "ok" | "warn" | "crit" | "info" | "neutral";
  className?: string;
  /** Optional marker drawn on the track, e.g. a threshold at 85 %. */
  marker?: number;
  size?: "sm" | "md";
}

const TONES = {
  ok: "bg-ok",
  warn: "bg-warn",
  crit: "bg-crit",
  info: "bg-info",
  neutral: "bg-content-faint",
};

/** Horizontal bar used for utilisation, efficiency, state of charge and shares. */
export function Meter({
  value,
  label,
  valueLabel,
  tone = "info",
  className,
  marker,
  size = "sm",
}: MeterProps) {
  const pct = value === null ? 0 : clamp(value, 0, 100);
  return (
    <div className={cn("w-full", className)}>
      {label || valueLabel ? (
        <div className="mb-1 flex items-baseline justify-between gap-2">
          {label ? <span className="text-2xs text-content-muted">{label}</span> : <span />}
          {valueLabel ? (
            <span className="text-2xs font-medium tabular text-content">{valueLabel}</span>
          ) : null}
        </div>
      ) : null}
      <div
        className={cn(
          "relative w-full overflow-hidden rounded-full bg-surface-overlay",
          size === "sm" ? "h-1.5" : "h-2.5",
        )}
        role="progressbar"
        aria-valuenow={value ?? undefined}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label ?? "value"}
      >
        {value === null ? (
          <div className="h-full w-full bg-[repeating-linear-gradient(45deg,#1E2733_0_6px,transparent_6px_12px)]" />
        ) : (
          <div
            className={cn("h-full rounded-full transition-[width] duration-500 ease-out", TONES[tone])}
            style={{ width: `${pct}%` }}
          />
        )}
        {marker !== undefined ? (
          <span
            className="absolute inset-y-0 w-px bg-content/45"
            style={{ left: `${clamp(marker, 0, 100)}%` }}
            aria-hidden
          />
        ) : null}
      </div>
    </div>
  );
}
