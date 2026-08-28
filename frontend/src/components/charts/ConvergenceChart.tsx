"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLORS } from "@/lib/constants";
import type { OptimizationResult } from "@/lib/types";
import { EmptyState } from "@/components/ui/States";
import { chartTheme } from "./chartTheme";
import { ChartTooltip } from "./ChartTooltip";

interface ConvergenceChartProps {
  convergence: OptimizationResult["convergence"];
  height?: number;
}

/** Best and mean fitness per generation — how the GA search converged. */
export function ConvergenceChart({ convergence, height = 200 }: ConvergenceChartProps) {
  if (convergence.length === 0) {
    return (
      <EmptyState
        title="No convergence trace"
        description="The optimiser did not report per-generation fitness for this run."
        className="h-[180px]"
      />
    );
  }

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={convergence} margin={chartTheme.margin}>
          <CartesianGrid {...chartTheme.grid} />
          <XAxis
            dataKey="generation"
            {...chartTheme.axis}
            label={{ value: "Generation", position: "insideBottom", fill: "#64748B", fontSize: 10, dy: 10 }}
            height={38}
          />
          <YAxis
            width={58}
            domain={["dataMin - 1500", "dataMax + 1500"]}
            tickFormatter={(v: number) => `${Math.round(v / 1000)}k`}
            {...chartTheme.axis}
          />
          <Tooltip
            content={<ChartTooltip labelFormatter={(l) => `Generation ${l}`} unit="₹" digits={0} />}
            cursor={{ stroke: "#2A3644", strokeWidth: 1 }}
          />
          <Line
            type="monotone"
            dataKey="meanFitness"
            name="Population mean cost"
            stroke={CHART_COLORS.baseline}
            strokeWidth={1.4}
            strokeDasharray="4 3"
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="bestFitness"
            name="Best individual cost"
            stroke={CHART_COLORS.optimised}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
