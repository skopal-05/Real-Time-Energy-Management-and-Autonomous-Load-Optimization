import { ASSET_REGISTRY } from "@/lib/constants";
import type { Anomaly, AnomalyStats, AssetId, Severity } from "@/lib/types";
import { roundTo } from "@/lib/utils";
import { MINUTE_MS, HOUR_MS } from "./scenario";

interface AnomalySeed {
  id: string;
  assetId: AssetId;
  metricKey: string;
  metricLabel: string;
  minutesAgo: number;
  severity: Severity;
  status: Anomaly["status"];
  score: number;
  observedValue: number;
  expectedRange: [number, number];
  unit: string;
  summary: string;
}

/**
 * Isolation Forest detections.
 *
 * `score` follows the scikit-learn convention: `decision_function` output where
 * values below the contamination threshold are labelled anomalous. Lower is
 * more anomalous.
 */
const THRESHOLD = -0.05;

const SEEDS: AnomalySeed[] = [
  {
    id: "an-2291",
    assetId: "compressor",
    metricKey: "specificPower",
    metricLabel: "Specific Power",
    minutesAgo: 14,
    severity: "high",
    status: "active",
    score: -0.312,
    observedValue: 8.14,
    expectedRange: [6.4, 7.2],
    unit: "kW/m³/min",
    summary:
      "Specific power has drifted above the learned envelope while flow stayed flat — consistent with a developing air leak or a fouled intake filter.",
  },
  {
    id: "an-2290",
    assetId: "boiler",
    metricKey: "stackLoss",
    metricLabel: "Stack Loss",
    minutesAgo: 47,
    severity: "medium",
    status: "active",
    score: -0.184,
    observedValue: 16.2,
    expectedRange: [9.5, 13.5],
    unit: "%",
    summary:
      "Flue-gas losses are elevated relative to the firing rate. The detector isolated this point on the joint (stack loss, outlet temp, feedwater temp) feature vector.",
  },
  {
    id: "an-2289",
    assetId: "solar",
    metricKey: "performanceRatio",
    metricLabel: "Performance Ratio",
    minutesAgo: 92,
    severity: "low",
    status: "acknowledged",
    score: -0.091,
    observedValue: 82.4,
    expectedRange: [88, 96],
    unit: "%",
    summary:
      "South string output sits below the irradiance-derived expectation for a sustained window. Typical of soiling rather than a hardware fault.",
  },
  {
    id: "an-2288",
    assetId: "line-a",
    metricKey: "vibration",
    metricLabel: "Vibration RMS",
    minutesAgo: 168,
    severity: "medium",
    status: "acknowledged",
    score: -0.147,
    observedValue: 4.72,
    expectedRange: [1.6, 3.8],
    unit: "mm/s",
    summary:
      "Spindle vibration exceeded its normal band during a high-throughput window. Flagged for the maintenance queue; no interlock triggered.",
  },
  {
    id: "an-2287",
    assetId: "hvac",
    metricKey: "cop",
    metricLabel: "Coefficient of Performance",
    minutesAgo: 260,
    severity: "low",
    status: "resolved",
    score: -0.073,
    observedValue: 2.71,
    expectedRange: [3.0, 3.8],
    unit: "",
    summary:
      "Chiller efficiency dipped during the afternoon ambient peak. Recovered without intervention once the load profile eased.",
  },
  {
    id: "an-2286",
    assetId: "grid",
    metricKey: "thd",
    metricLabel: "Voltage THD",
    minutesAgo: 402,
    severity: "high",
    status: "resolved",
    score: -0.268,
    observedValue: 6.1,
    expectedRange: [1.5, 4.0],
    unit: "%",
    summary:
      "Harmonic distortion spiked at the point of common coupling during a line-B drive restart. Cleared once the drive completed its ramp.",
  },
  {
    id: "an-2285",
    assetId: "battery",
    metricKey: "cellTemp",
    metricLabel: "Cell Temp",
    minutesAgo: 640,
    severity: "critical",
    status: "resolved",
    score: -0.401,
    observedValue: 46.8,
    expectedRange: [26, 40],
    unit: "°C",
    summary:
      "Cell temperature crossed the thermal guard band during a deep discharge. The BMS derated output and the Safety Agent halted further discharge.",
  },
  {
    id: "an-2284",
    assetId: "line-b",
    metricKey: "powerFactor",
    metricLabel: "Power Factor",
    minutesAgo: 880,
    severity: "medium",
    status: "resolved",
    score: -0.159,
    observedValue: 0.81,
    expectedRange: [0.88, 0.97],
    unit: "",
    summary:
      "Power factor fell below the tariff penalty threshold while the line ran lightly loaded. Capacitor bank stage was re-enabled.",
  },
];

export function buildAnomalies(nowMs: number): Anomaly[] {
  return SEEDS.map((s) => ({
    id: s.id,
    assetId: s.assetId,
    assetName: ASSET_REGISTRY[s.assetId].name,
    metricKey: s.metricKey,
    metricLabel: s.metricLabel,
    detectedAt: new Date(nowMs - s.minutesAgo * MINUTE_MS).toISOString(),
    severity: s.severity,
    status: s.status,
    score: s.score,
    threshold: THRESHOLD,
    observedValue: s.observedValue,
    expectedRange: s.expectedRange,
    unit: s.unit,
    summary: s.summary,
    origin: "simulated" as const,
  }));
}

export function buildAnomalyStats(anomalies: Anomaly[]): AnomalyStats {
  const bySeverity: Record<Severity, number> = { low: 0, medium: 0, high: 0, critical: 0 };
  for (const a of anomalies) bySeverity[a.severity] += 1;

  const resolved = anomalies.filter((a) => a.status === "resolved");
  return {
    total: anomalies.length,
    active: anomalies.filter((a) => a.status === "active").length,
    acknowledged: anomalies.filter((a) => a.status === "acknowledged").length,
    resolved: resolved.length,
    bySeverity,
    meanTimeToResolveMinutes: resolved.length > 0 ? 74 : null,
  };
}

/** Anomaly-score scatter for the detection chart: one point per sampled window. */
export function buildScoreScatter(nowMs: number, anomalies: Anomaly[]) {
  const points: { timestamp: number; score: number; anomalous: boolean; label: string }[] = [];
  for (let i = 96; i >= 0; i -= 1) {
    const t = nowMs - i * 15 * MINUTE_MS;
    // Normal points sit above the threshold with mild spread.
    const base = 0.06 + 0.11 * Math.abs(Math.sin(i * 1.7));
    points.push({ timestamp: t, score: roundTo(base, 3), anomalous: false, label: "Normal window" });
  }
  for (const a of anomalies) {
    const t = new Date(a.detectedAt).getTime();
    if (t >= nowMs - 24 * HOUR_MS) {
      points.push({
        timestamp: t,
        score: a.score,
        anomalous: true,
        label: `${a.assetName} · ${a.metricLabel}`,
      });
    }
  }
  return points.sort((x, y) => x.timestamp - y.timestamp);
}

export const ANOMALY_THRESHOLD = THRESHOLD;
