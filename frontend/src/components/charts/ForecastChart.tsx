"use client";

import { useMemo } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS } from "@/lib/constants";
import type { ForecastPoint } from "@/lib/types";
import { EmptyState } from "@/components/ui/States";
import { autoTick, chartTheme } from "./chartTheme";
import { ChartTooltip } from "./ChartTooltip";

interface ForecastChartProps {
  points: ForecastPoint[];
  height?: number;
  /** Epoch ms separating history from prediction. */
  nowMs: number;
  showInterval?: boolean;
  unit?: string;
  peakAt?: string | null;
}

/**
 * Actual vs predicted load with the prediction interval shaded and the future
 * region visually separated. Points with no interval simply render without the
 * band rather than breaking the chart.
 */
export function ForecastChart({
  points,
  height = 300,
  nowMs,
  showInterval = true,
  unit = "kW",
  peakAt = null,
}: ForecastChartProps) {
  const rows = useMemo(
    () =>
      points.map((p) => ({
        t: new Date(p.timestamp).getTime(),
        actual: p.actualKw,
        predicted: p.predictedKw,
        band:
          showInterval && p.lowerKw !== null && p.upperKw !== null
            ? ([p.lowerKw, p.upperKw] as [number, number])
            : null,
      })),
    [points, showInterval],
  );

  if (rows.length === 0) {
    return (
      <EmptyState
        title="No forecast available"
        description="The forecasting service has not returned a series for this horizon yet."
        className="h-[240px]"
      />
    );
  }

  const span = rows[rows.length - 1].t - rows[0].t;
  const tickFormatter = autoTick(span);
  const lastT = rows[rows.length - 1].t;

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rows} margin={chartTheme.margin}>
          <defs>
            <linearGradient id="grad-actual" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_COLORS.load} stopOpacity={0.24} />
              <stop offset="100%" stopColor={CHART_COLORS.load} stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid {...chartTheme.grid} />
          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={["dataMin", "dataMax"]}
            tickFormatter={tickFormatter}
            minTickGap={40}
            {...chartTheme.axis}
          />
          <YAxis width={54} tickFormatter={(v: number) => `${Math.round(v)}`} {...chartTheme.axis} />
          <Tooltip
            content={<ChartTooltip labelFormatter={(l) => tickFormatter(Number(l))} unit={unit} />}
            cursor={{ stroke: "#2A3644", strokeWidth: 1 }}
          />
          <Legend {...chartTheme.legend} />

          {/* Future region — everything right of "now" is model output. */}
          <ReferenceArea x1={nowMs} x2={lastT} fill="#A78BFA" fillOpacity={0.05} />
          <ReferenceLine
            x={nowMs}
            stroke="#7C8BA1"
            strokeDasharray="3 3"
            label={{ value: "now", position: "top", fill: "#93A1B5", fontSize: 10 }}
          />
          {peakAt ? (
            <ReferenceLine
              x={new Date(peakAt).getTime()}
              stroke={CHART_COLORS.forecast}
              strokeDasharray="2 3"
              label={{ value: "predicted peak", position: "insideTopRight", fill: CHART_COLORS.forecast, fontSize: 10 }}
            />
          ) : null}

          {showInterval ? (
            <Area
              dataKey="band"
              name="95 % prediction interval"
              stroke="none"
              fill={CHART_COLORS.forecast}
              fillOpacity={0.16}
              isAnimationActive={false}
              connectNulls
              legendType="rect"
              unit={unit}
            />
          ) : null}

          <Area
            type="monotone"
            dataKey="actual"
            name="Actual load"
            stroke={CHART_COLORS.load}
            strokeWidth={1.9}
            fill="url(#grad-actual)"
            dot={false}
            isAnimationActive={false}
            connectNulls={false}
            unit={unit}
          />
          <Line
            type="monotone"
            dataKey="predicted"
            name="Random Forest prediction"
            stroke={CHART_COLORS.forecast}
            strokeWidth={1.9}
            strokeDasharray="5 4"
            dot={false}
            isAnimationActive={false}
            connectNulls
            unit={unit}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
