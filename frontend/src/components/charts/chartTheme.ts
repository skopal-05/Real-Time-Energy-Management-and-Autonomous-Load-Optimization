import { CHART_COLORS } from "@/lib/constants";

/** Shared Recharts styling so every chart in the app reads as one system. */
export const chartTheme = {
  grid: {
    stroke: CHART_COLORS.gridline,
    strokeDasharray: "3 4",
    vertical: false,
  },
  axis: {
    stroke: "#2A3644",
    tick: { fill: CHART_COLORS.axis, fontSize: 11 },
    tickLine: false,
    axisLine: false,
  },
  margin: { top: 8, right: 12, bottom: 4, left: 0 },
  legend: {
    iconType: "plainline" as const,
    iconSize: 10,
    wrapperStyle: { paddingTop: 8, fontSize: 12 },
  },
} as const;

/** Axis tick formatter for millisecond timestamps. */
export function timeTick(ms: number): string {
  return new Date(ms).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

export function dayTick(ms: number): string {
  return new Date(ms).toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
}

/** Picks a tick formatter based on how much time the series spans. */
export function autoTick(spanMs: number): (ms: number) => string {
  return spanMs > 3 * 24 * 60 * 60 * 1000 ? dayTick : timeTick;
}
