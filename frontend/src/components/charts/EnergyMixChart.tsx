"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { EnergySourceShare } from "@/lib/types";
import { formatKwh, formatPct } from "@/lib/format";
import { EmptyState } from "@/components/ui/States";
import { ChartTooltip } from "./ChartTooltip";

interface EnergyMixChartProps {
  shares: EnergySourceShare[];
  height?: number;
  /** Large number rendered in the middle of the ring. */
  centerValue?: string;
  centerLabel?: string;
}

/** Donut showing where the site's energy came from over the selected window. */
export function EnergyMixChart({
  shares,
  height = 200,
  centerValue,
  centerLabel,
}: EnergyMixChartProps) {
  const usable = shares.filter((s) => s.energyKwh > 0);

  if (usable.length === 0) {
    return (
      <EmptyState
        title="No energy recorded"
        description="No source delivered energy in this window."
        className="h-[180px]"
      />
    );
  }

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
      <div className="relative shrink-0" style={{ height, width: height }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={usable}
              dataKey="energyKwh"
              nameKey="source"
              innerRadius="62%"
              outerRadius="92%"
              paddingAngle={2}
              stroke="none"
              isAnimationActive={false}
            >
              {usable.map((s) => (
                <Cell key={s.source} fill={s.colorToken} />
              ))}
            </Pie>
            <Tooltip content={<ChartTooltip unit="kWh" digits={0} />} />
          </PieChart>
        </ResponsiveContainer>
        {centerValue ? (
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-lg font-semibold tabular text-content">{centerValue}</span>
            {centerLabel ? (
              <span className="mt-0.5 text-2xs uppercase tracking-wider text-content-faint">
                {centerLabel}
              </span>
            ) : null}
          </div>
        ) : null}
      </div>

      <ul className="flex-1 space-y-2">
        {usable.map((s) => (
          <li key={s.source} className="flex items-center justify-between gap-3 text-xs">
            <span className="flex items-center gap-2 text-content-muted">
              <span className="h-2 w-2 rounded-[2px]" style={{ backgroundColor: s.colorToken }} aria-hidden />
              {s.source}
            </span>
            <span className="flex items-baseline gap-2">
              <span className="tabular text-content-faint">{formatKwh(s.energyKwh)}</span>
              <span className="w-12 text-right font-medium tabular text-content">
                {formatPct(s.sharePct, 1)}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
