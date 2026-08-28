"use client";

import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLORS } from "@/lib/constants";
import type { FeatureContribution } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import { EmptyState } from "@/components/ui/States";
import { chartTheme } from "./chartTheme";

interface FeatureImportanceChartProps {
  contributions: FeatureContribution[];
  unit?: string;
  height?: number;
  maxFeatures?: number;
}

/**
 * SHAP-style contribution plot: signed bars ordered by magnitude, positive to
 * the right of the base value and negative to the left.
 */
export function FeatureImportanceChart({
  contributions,
  unit = "kW",
  height = 320,
  maxFeatures = 8,
}: FeatureImportanceChartProps) {
  if (contributions.length === 0) {
    return (
      <EmptyState
        title="No feature attributions"
        description="This model has no SHAP explainer fitted, so no contributions can be shown."
        className="h-[220px]"
      />
    );
  }

  const rows = contributions.slice(0, maxFeatures).map((c) => ({
    ...c,
    name: c.label,
  }));

  // Anomaly scores live around ±0.3, load contributions around ±100 — pick the
  // axis precision from the data so ticks never collapse to "-0".
  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.shapValue)), 0);
  const axisDigits = maxAbs < 1 ? 2 : maxAbs < 10 ? 1 : 0;

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 48, bottom: 4, left: 8 }} barCategoryGap={7}>
          <XAxis
            type="number"
            tickFormatter={(v: number) => formatNumber(v, axisDigits)}
            {...chartTheme.axis}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={168}
            interval={0}
            tick={{ fill: "#93A1B5", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
          />
          <ReferenceLine x={0} stroke="#3A4757" />
          <Tooltip
            cursor={{ fill: "rgba(255,255,255,0.03)" }}
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) return null;
              const row = payload[0].payload as FeatureContribution;
              return (
                <div className="min-w-[13rem] rounded-lg border border-line-strong bg-surface-overlay/95 p-2.5 text-xs shadow-lift">
                  <p className="mb-1.5 border-b border-line-soft pb-1.5 font-medium text-content">{row.label}</p>
                  <p className="flex justify-between gap-4 text-content-muted">
                    <span>Feature value</span>
                    <span className="tabular text-content">
                      {formatNumber(row.featureValue, 2)} {row.unit}
                    </span>
                  </p>
                  <p className="flex justify-between gap-4 text-content-muted">
                    <span>SHAP contribution</span>
                    <span
                      className="tabular"
                      style={{ color: row.shapValue >= 0 ? CHART_COLORS.positive : CHART_COLORS.negative }}
                    >
                      {row.shapValue >= 0 ? "+" : ""}
                      {formatNumber(row.shapValue, 2)} {unit}
                    </span>
                  </p>
                </div>
              );
            }}
          />
          <Bar dataKey="shapValue" radius={[3, 3, 3, 3]} isAnimationActive={false}>
            {rows.map((r) => (
              <Cell
                key={r.feature}
                fill={r.shapValue >= 0 ? CHART_COLORS.positive : CHART_COLORS.negative}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
