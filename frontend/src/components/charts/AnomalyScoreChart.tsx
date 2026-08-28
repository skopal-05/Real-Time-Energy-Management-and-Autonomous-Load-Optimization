"use client";

import {
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS } from "@/lib/constants";
import type { AnomalyScorePoint } from "@/lib/types";
import { formatDateTime, formatNumber } from "@/lib/format";
import { EmptyState } from "@/components/ui/States";
import { chartTheme, timeTick } from "./chartTheme";

interface AnomalyScoreChartProps {
  points: AnomalyScorePoint[];
  threshold: number;
  height?: number;
}

/**
 * Isolation Forest decision-function scores over time. Points below the
 * contamination threshold are labelled anomalous by the detector.
 */
export function AnomalyScoreChart({ points, threshold, height = 240 }: AnomalyScoreChartProps) {
  if (points.length === 0) {
    return (
      <EmptyState
        title="No scored windows"
        description="The detector has not scored any windows in this range."
        className="h-[200px]"
      />
    );
  }

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid {...chartTheme.grid} />
          <XAxis
            dataKey="timestamp"
            type="number"
            scale="time"
            domain={["dataMin", "dataMax"]}
            tickFormatter={timeTick}
            minTickGap={40}
            {...chartTheme.axis}
          />
          <YAxis
            dataKey="score"
            type="number"
            width={58}
            tickFormatter={(v: number) => formatNumber(v, 2)}
            {...chartTheme.axis}
          />
          <ReferenceLine
            y={threshold}
            stroke={CHART_COLORS.negative}
            strokeDasharray="5 4"
            label={{
              value: `threshold ${threshold}`,
              position: "insideBottomRight",
              fill: CHART_COLORS.negative,
              fontSize: 10,
            }}
          />
          <Tooltip
            cursor={{ stroke: "#2A3644", strokeWidth: 1 }}
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) return null;
              const p = payload[0].payload as AnomalyScorePoint;
              return (
                <div className="rounded-lg border border-line-strong bg-surface-overlay/95 p-2.5 text-xs shadow-lift">
                  <p className="mb-1 font-medium text-content">{p.label}</p>
                  <p className="text-content-muted">{formatDateTime(new Date(p.timestamp).toISOString())}</p>
                  <p className="mt-1 flex justify-between gap-4 text-content-muted">
                    <span>Isolation score</span>
                    <span
                      className="tabular"
                      style={{ color: p.anomalous ? CHART_COLORS.negative : CHART_COLORS.positive }}
                    >
                      {formatNumber(p.score, 3)}
                    </span>
                  </p>
                </div>
              );
            }}
          />
          <Scatter data={points} isAnimationActive={false}>
            {points.map((p, i) => (
              <Cell
                key={`${p.timestamp}-${i}`}
                fill={p.anomalous ? CHART_COLORS.negative : CHART_COLORS.load}
                fillOpacity={p.anomalous ? 0.95 : 0.4}
                r={p.anomalous ? 6 : 3}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
