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
import { EmptyState } from "@/components/ui/States";
import { autoTick, chartTheme } from "./chartTheme";
import { ChartTooltip } from "./ChartTooltip";

export interface SeriesSpec {
  key: string;
  label: string;
  color: string;
  type?: "area" | "line";
  /** Dashed stroke — use for modelled or target series. */
  dashed?: boolean;
  strokeWidth?: number;
  fillOpacity?: number;
}

/** Any record carrying an ISO timestamp can be plotted. */
export interface TimeSeriesPoint {
  timestamp: string;
}

interface TimeSeriesChartProps<T extends TimeSeriesPoint> {
  data: T[];
  series: SeriesSpec[];
  height?: number;
  unit?: string;
  yLabel?: string;
  digits?: number;
  showLegend?: boolean;
  referenceLines?: { y: number; label: string; color?: string }[];
  emptyMessage?: string;
  /** Forces the y-axis to include zero — useful for signed power series. */
  includeZero?: boolean;
}

/**
 * The workhorse chart: any number of area/line series against a shared time
 * axis. Handles empty and single-point data without throwing.
 */
export function TimeSeriesChart<T extends TimeSeriesPoint>({
  data,
  series,
  height = 260,
  unit = "kW",
  yLabel,
  digits = 1,
  showLegend = true,
  referenceLines = [],
  emptyMessage = "No samples in the selected range.",
  includeZero = false,
}: TimeSeriesChartProps<T>) {
  const rows = useMemo(
    () =>
      data.map((d) => ({
        ...d,
        t: new Date(d.timestamp).getTime(),
      })),
    [data],
  );

  const span = rows.length > 1 ? rows[rows.length - 1].t - rows[0].t : 0;
  const tickFormatter = autoTick(span);

  if (rows.length === 0) {
    return <EmptyState title="No data to plot" description={emptyMessage} className="h-[220px]" />;
  }

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rows} margin={chartTheme.margin}>
          <defs>
            {series
              .filter((s) => (s.type ?? "area") === "area")
              .map((s) => (
                <linearGradient key={s.key} id={`grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={s.color} stopOpacity={s.fillOpacity ?? 0.26} />
                  <stop offset="100%" stopColor={s.color} stopOpacity={0} />
                </linearGradient>
              ))}
          </defs>

          <CartesianGrid {...chartTheme.grid} />
          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={["dataMin", "dataMax"]}
            tickFormatter={tickFormatter}
            minTickGap={38}
            {...chartTheme.axis}
          />
          <YAxis
            width={54}
            domain={includeZero ? ["auto", "auto"] : ["auto", "auto"]}
            tickFormatter={(v: number) => `${Math.round(v)}`}
            label={
              yLabel
                ? { value: yLabel, angle: -90, position: "insideLeft", fill: "#64748B", fontSize: 11, dy: 34 }
                : undefined
            }
            {...chartTheme.axis}
          />
          <Tooltip
            content={<ChartTooltip labelFormatter={(l) => tickFormatter(Number(l))} unit={unit} digits={digits} />}
            cursor={{ stroke: "#2A3644", strokeWidth: 1 }}
          />
          {showLegend ? <Legend {...chartTheme.legend} /> : null}

          {referenceLines.map((r) => (
            <ReferenceLine
              key={r.label}
              y={r.y}
              stroke={r.color ?? "#F59E0B"}
              strokeDasharray="4 4"
              strokeWidth={1}
              label={{ value: r.label, position: "right", fill: r.color ?? "#F59E0B", fontSize: 10 }}
            />
          ))}

          {series.map((s) =>
            (s.type ?? "area") === "area" ? (
              <Area
                key={s.key}
                type="monotone"
                dataKey={s.key}
                name={s.label}
                stroke={s.color}
                strokeWidth={s.strokeWidth ?? 1.8}
                strokeDasharray={s.dashed ? "5 4" : undefined}
                fill={`url(#grad-${s.key})`}
                dot={false}
                activeDot={{ r: 3, strokeWidth: 0 }}
                isAnimationActive={false}
                connectNulls
                unit={unit}
              />
            ) : (
              <Line
                key={s.key}
                type="monotone"
                dataKey={s.key}
                name={s.label}
                stroke={s.color}
                strokeWidth={s.strokeWidth ?? 1.8}
                strokeDasharray={s.dashed ? "5 4" : undefined}
                dot={false}
                activeDot={{ r: 3, strokeWidth: 0 }}
                isAnimationActive={false}
                connectNulls
                unit={unit}
              />
            ),
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
