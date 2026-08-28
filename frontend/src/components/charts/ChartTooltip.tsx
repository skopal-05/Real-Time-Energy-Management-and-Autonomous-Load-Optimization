"use client";

import type { TooltipProps } from "recharts";
import type { NameType, ValueType } from "recharts/types/component/DefaultTooltipContent";
import { formatNumber } from "@/lib/format";

interface ChartTooltipProps extends TooltipProps<ValueType, NameType> {
  /** Formats the tooltip heading from the x-axis value. */
  labelFormatter?: (label: string | number) => string;
  unit?: string;
  digits?: number;
}

/**
 * Tooltip shared by every chart: dark card, aligned numbers, explicit units,
 * and null-safe rows so a gap in the data never renders "NaN".
 */
export function ChartTooltip({
  active,
  payload,
  label,
  labelFormatter,
  unit,
  digits = 1,
}: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  const heading =
    labelFormatter && label !== undefined
      ? labelFormatter(label as string | number)
      : String(label ?? "");

  return (
    <div className="min-w-[10rem] rounded-lg border border-line-strong bg-surface-overlay/95 p-2.5 shadow-lift backdrop-blur-sm">
      {heading ? (
        <p className="mb-1.5 border-b border-line-soft pb-1.5 text-2xs uppercase tracking-wider text-content-faint">
          {heading}
        </p>
      ) : null}
      <ul className="space-y-1">
        {payload
          .filter((entry) => entry.value !== null && entry.value !== undefined)
          .map((entry, i) => (
            <li key={`${entry.name}-${i}`} className="flex items-center justify-between gap-4 text-xs">
              <span className="flex items-center gap-1.5 text-content-muted">
                <span
                  className="h-2 w-2 shrink-0 rounded-[2px]"
                  style={{ backgroundColor: entry.color ?? "#7C8BA1" }}
                  aria-hidden
                />
                {entry.name}
              </span>
              <span className="font-medium tabular text-content">
                {Array.isArray(entry.value)
                  ? `${formatNumber(Number(entry.value[0]), digits)} – ${formatNumber(Number(entry.value[1]), digits)}`
                  : typeof entry.value === "number"
                    ? formatNumber(entry.value, digits)
                    : String(entry.value)}
                {entry.unit ? ` ${entry.unit}` : unit ? ` ${unit}` : ""}
              </span>
            </li>
          ))}
      </ul>
    </div>
  );
}
