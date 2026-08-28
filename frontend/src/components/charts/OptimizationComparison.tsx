"use client";

import { useMemo } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS } from "@/lib/constants";
import type { ScheduleSlot } from "@/lib/types";
import { EmptyState } from "@/components/ui/States";
import { chartTheme, timeTick } from "./chartTheme";
import { ChartTooltip } from "./ChartTooltip";

interface OptimizationComparisonProps {
  schedule: ScheduleSlot[];
  height?: number;
  /** Contracted maximum demand drawn as a hard limit line. */
  demandCapKw?: number;
  nowMs?: number;
}

/** Baseline vs GA-optimised load schedule over the planning horizon. */
export function OptimizationComparison({
  schedule,
  height = 300,
  demandCapKw,
  nowMs,
}: OptimizationComparisonProps) {
  const rows = useMemo(
    () =>
      schedule.map((s) => ({
        t: new Date(s.timestamp).getTime(),
        baseline: s.baselineKw,
        optimised: s.optimisedKw,
        delta: s.optimisedKw === null ? null : Number((s.optimisedKw - s.baselineKw).toFixed(1)),
      })),
    [schedule],
  );

  if (rows.length === 0) {
    return (
      <EmptyState
        title="No schedule to compare"
        description="The optimiser has not produced a schedule for this horizon."
        className="h-[240px]"
      />
    );
  }

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rows} margin={chartTheme.margin}>
          <defs>
            <linearGradient id="grad-optimised" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_COLORS.optimised} stopOpacity={0.24} />
              <stop offset="100%" stopColor={CHART_COLORS.optimised} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid {...chartTheme.grid} />
          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={["dataMin", "dataMax"]}
            tickFormatter={timeTick}
            minTickGap={40}
            {...chartTheme.axis}
          />
          <YAxis width={54} tickFormatter={(v: number) => `${Math.round(v)}`} {...chartTheme.axis} />
          <Tooltip
            content={<ChartTooltip labelFormatter={(l) => timeTick(Number(l))} unit="kW" />}
            cursor={{ stroke: "#2A3644", strokeWidth: 1 }}
          />
          <Legend {...chartTheme.legend} />

          {demandCapKw ? (
            <ReferenceLine
              y={demandCapKw}
              stroke={CHART_COLORS.negative}
              strokeDasharray="5 4"
              label={{
                value: `Demand cap ${demandCapKw} kW`,
                position: "insideTopLeft",
                fill: CHART_COLORS.negative,
                fontSize: 10,
              }}
            />
          ) : null}
          {nowMs ? <ReferenceLine x={nowMs} stroke="#7C8BA1" strokeDasharray="3 3" /> : null}

          <Line
            type="monotone"
            dataKey="baseline"
            name="Baseline schedule"
            stroke={CHART_COLORS.baseline}
            strokeWidth={1.7}
            dot={false}
            isAnimationActive={false}
            unit="kW"
          />
          <Area
            type="monotone"
            dataKey="optimised"
            name="GA-optimised schedule"
            stroke={CHART_COLORS.optimised}
            strokeWidth={2}
            fill="url(#grad-optimised)"
            dot={false}
            isAnimationActive={false}
            connectNulls
            unit="kW"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
