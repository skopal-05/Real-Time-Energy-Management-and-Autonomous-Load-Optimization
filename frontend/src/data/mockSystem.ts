import type { Asset, PipelineStage, SystemEvent, SystemStatus } from "@/lib/types";
import { clamp, roundTo } from "@/lib/utils";
import { MINUTE_MS, currentEnergyState, siteConsumptionKw } from "./scenario";
import { buildAssets } from "./mockAssets";
import { renewableSharePct } from "./mockEnergy";
import { buildAnomalies } from "./mockAnomalies";
import { buildObjective } from "./mockDecisions";

function pipelineStages(nowMs: number): PipelineStage[] {
  return [
    {
      id: "acquisition",
      label: "Data Acquisition",
      module: "Module 1 · ingest",
      state: "ok",
      detail: "8 twins reporting on a 5-second poll",
    },
    {
      id: "twin",
      label: "Digital Twin",
      module: "Module 2 · state estimation",
      state: "ok",
      detail: "State vectors current",
    },
    {
      id: "forecast",
      label: "Forecasting",
      module: "Random Forest",
      state: "ok",
      detail: "Last inference 4 min ago",
    },
    {
      id: "agents",
      label: "Decision Agents",
      module: "Rule-based multi-agent",
      state: "ok",
      detail: "6 agents active",
    },
    {
      id: "optimizer",
      label: "Optimisation",
      module: "Genetic Algorithm",
      state: "ok",
      detail: "Converged at generation 120",
    },
    {
      id: "anomaly",
      label: "Anomaly Detection",
      module: "Isolation Forest",
      state: "degraded",
      detail: "2 active detections",
    },
    {
      id: "xai",
      label: "Explainability",
      module: "SHAP",
      state: "ok",
      detail: "Explainers fitted for 2 models",
    },
  ].map((s) => ({ ...s, detail: s.detail })) as PipelineStage[];
}

function overallFrom(assets: Asset[], activeAnomalies: number): SystemStatus["overall"] {
  if (assets.some((a) => a.status === "critical") || activeAnomalies > 4) return "critical";
  if (assets.some((a) => a.status === "warning") || activeAnomalies > 0) return "warning";
  if (assets.some((a) => a.status === "offline")) return "warning";
  return "healthy";
}

export function buildSystemStatus(nowMs: number): SystemStatus {
  const assets = buildAssets(nowMs);
  const energy = currentEnergyState(nowMs);
  const anomalies = buildAnomalies(nowMs).filter((a) => a.status === "active");
  const objective = buildObjective(nowMs);
  const online = assets.filter((a) => a.status !== "offline").length;

  const penalty = assets.reduce(
    (acc, a) => acc + (a.status === "critical" ? 14 : a.status === "warning" ? 6 : 0),
    0,
  );

  return {
    timestamp: new Date(nowMs).toISOString(),
    overall: overallFrom(assets, anomalies.length),
    healthScorePct: roundTo(clamp(100 - penalty - anomalies.length * 2, 0, 100), 0),
    operatingMode: objective.mode,
    operatingModeLabel: objective.label,
    twinsOnline: online,
    twinsTotal: assets.length,
    consumptionKw: energy.consumptionKw,
    generationKw: energy.generationKw,
    renewableSharePct: renewableSharePct(energy),
    forecastNextHourKw: roundTo(siteConsumptionKw(nowMs + 60 * MINUTE_MS), 1),
    optimizationStatus: "converged",
    activeAnomalies: anomalies.length,
    aiConfidencePct: 87,
    pipelineStages: pipelineStages(nowMs),
    origin: "simulated",
  };
}

export function buildEvents(nowMs: number): SystemEvent[] {
  const raw: Array<Omit<SystemEvent, "timestamp"> & { minutesAgo: number }> = [
    {
      id: "ev-901",
      kind: "anomaly",
      severity: "high",
      title: "Compressor specific power outside learned envelope",
      detail: "Isolation Forest score −0.312 against a −0.05 threshold.",
      assetId: "compressor",
      minutesAgo: 14,
    },
    {
      id: "ev-900",
      kind: "decision",
      severity: "info",
      title: "Storage Agent applied battery dispatch change",
      detail: "Battery moved to discharge to protect the contracted demand cap.",
      assetId: "battery",
      minutesAgo: 4,
    },
    {
      id: "ev-899",
      kind: "optimization",
      severity: "info",
      title: "Genetic Algorithm run converged",
      detail: "120 generations, population 80. Schedule proposal ready for review.",
      assetId: null,
      minutesAgo: 7,
    },
    {
      id: "ev-898",
      kind: "forecast",
      severity: "info",
      title: "Load forecast refreshed",
      detail: "Random Forest re-scored the next 24 hours at 30-minute resolution.",
      assetId: null,
      minutesAgo: 9,
    },
    {
      id: "ev-897",
      kind: "anomaly",
      severity: "medium",
      title: "Boiler stack loss elevated",
      detail: "16.2 % against a 9.5–13.5 % expected band.",
      assetId: "boiler",
      minutesAgo: 47,
    },
    {
      id: "ev-896",
      kind: "alert",
      severity: "low",
      title: "Solar south string under-performing",
      detail: "Performance ratio 82.4 % — inspection queued, no control action taken.",
      assetId: "solar",
      minutesAgo: 92,
    },
    {
      id: "ev-895",
      kind: "system",
      severity: "info",
      title: "Operating mode switched",
      detail: "Objective changed by schedule as the tariff band advanced.",
      assetId: null,
      minutesAgo: 128,
    },
    {
      id: "ev-894",
      kind: "decision",
      severity: "info",
      title: "Safety Agent vetoed compressor unload",
      detail: "Proposal would have taken header pressure below its process limit.",
      assetId: "compressor",
      minutesAgo: 38,
    },
  ];

  return raw
    .map(({ minutesAgo, ...rest }) => ({
      ...rest,
      timestamp: new Date(nowMs - minutesAgo * MINUTE_MS).toISOString(),
    }))
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}
