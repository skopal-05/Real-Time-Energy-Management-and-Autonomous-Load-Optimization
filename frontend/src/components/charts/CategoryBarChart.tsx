"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { EmptyState } from "@/components/ui/States";
import { chartTheme } from "./chartTheme";
import { ChartTooltip } from "./ChartTooltip";

export interface BarSeriesSpec {
  key: string;
  label: string;
  color: string;
  stackId?: string;
}

interface CategoryBarChartProps<T> {
  data: T[];
  categoryKey: string;
  series: BarSeriesSpec[];
  height?: number;
  unit?: string;
  digits?: number;
  showLegend?: boolean;
}

/** Grouped/stacked bars against a labelled category axis (days, buckets, assets). */
export function CategoryBarChart<T extends object>({
  data,
  categoryKey,
  series,
  height = 260,
  unit = "kWh",
  digits = 0,
  showLegend = true,
}: CategoryBarChartProps<T>) {
  if (data.length === 0) {
    return <EmptyState title="No data in this period" className="h-[200px]" />;
  }

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={chartTheme.margin} barGap={3}>
          <CartesianGrid {...chartTheme.grid} />
          <XAxis dataKey={categoryKey} {...chartTheme.axis} interval="preserveStartEnd" />
          <YAxis
            width={58}
            tickFormatter={(v: number) => (Math.abs(v) >= 1000 ? `${Math.round(v / 1000)}k` : `${Math.round(v)}`)}
            {...chartTheme.axis}
          />
          <Tooltip
            cursor={{ fill: "rgba(255,255,255,0.03)" }}
            content={<ChartTooltip unit={unit} digits={digits} />}
          />
          {showLegend ? <Legend {...chartTheme.legend} iconType="square" /> : null}
          {series.map((s) => (
            <Bar
              key={s.key}
              dataKey={s.key}
              name={s.label}
              fill={s.color}
              fillOpacity={0.85}
              stackId={s.stackId}
              radius={[3, 3, 0, 0]}
              isAnimationActive={false}
              unit={unit}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
