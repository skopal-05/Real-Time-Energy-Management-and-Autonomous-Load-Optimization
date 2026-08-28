import type { ReactNode } from "react";
import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";
import type { Trend } from "@/lib/types";
import { cn } from "@/lib/utils";
import { InfoTip } from "./InfoTip";
import { Sparkline } from "./Sparkline";

type Tone = "neutral" | "ok" | "warn" | "crit" | "info";

const TONE_ACCENT: Record<Tone, string> = {
  neutral: "text-content",
  ok: "text-ok",
  warn: "text-warn",
  crit: "text-crit",
  info: "text-info",
};

const TONE_RAIL: Record<Tone, string> = {
  neutral: "bg-line-strong",
  ok: "bg-ok",
  warn: "bg-warn",
  crit: "bg-crit",
  info: "bg-info",
};

export interface MetricCardProps {
  label: string;
  /** Pre-formatted value string — formatting lives in `lib/format`. */
  value: string;
  unit?: string;
  hint?: string;
  tone?: Tone;
  icon?: ReactNode;
  /** Small secondary line, e.g. "vs 742 kW forecast". */
  caption?: string;
  delta?: { value: string; trend: Trend; positiveIsGood?: boolean };
  sparkline?: number[];
  sparklineColor?: string;
  footer?: ReactNode;
  className?: string;
}

function DeltaPill({ value, trend, positiveIsGood = true }: NonNullable<MetricCardProps["delta"]>) {
  const Icon = trend === "up" ? ArrowUpRight : trend === "down" ? ArrowDownRight : ArrowRight;
  const good = trend === "flat" ? null : (trend === "up") === positiveIsGood;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 rounded px-1 py-0.5 text-2xs font-medium tabular",
        good === null ? "text-content-faint" : good ? "text-ok" : "text-warn",
      )}
    >
      <Icon className="h-3 w-3" aria-hidden />
      {value}
    </span>
  );
}

/**
 * The primary KPI tile used across every page. Keep the label short and always
 * pass a unit — unitless numbers are not acceptable on an engineering dashboard.
 */
export function MetricCard({
  label,
  value,
  unit,
  hint,
  tone = "neutral",
  icon,
  caption,
  delta,
  sparkline,
  sparklineColor,
  footer,
  className,
}: MetricCardProps) {
  return (
    <article
      className={cn(
        "panel panel-hover group relative overflow-hidden p-4",
        className,
      )}
    >
      <span className={cn("absolute inset-y-0 left-0 w-px", TONE_RAIL[tone])} aria-hidden />
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <span className="label-eyebrow">{label}</span>
          {hint ? <InfoTip text={hint} /> : null}
        </div>
        {icon ? <span className="text-content-faint">{icon}</span> : null}
      </div>

      <div className="mt-2 flex items-baseline gap-1.5">
        <span className={cn("text-2xl font-semibold tracking-tight tabular", TONE_ACCENT[tone])}>
          {value}
        </span>
        {unit ? <span className="text-xs font-medium text-content-muted">{unit}</span> : null}
        {delta ? <DeltaPill {...delta} /> : null}
      </div>

      {caption ? <p className="mt-1 text-xs text-content-muted">{caption}</p> : null}

      {sparkline && sparkline.length > 0 ? (
        <div className="mt-3 h-8">
          <Sparkline values={sparkline} color={sparklineColor} height={32} />
        </div>
      ) : null}

      {footer ? <div className="mt-3 border-t border-line-soft pt-2">{footer}</div> : null}
    </article>
  );
}
