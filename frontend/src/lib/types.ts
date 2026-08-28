/**
 * Domain model for the Generative Digital Twin platform.
 *
 * These interfaces are the contract between the UI and the data layer.
 * When the Python backend is connected, the REST/WebSocket adapters in
 * `src/services` must return exactly these shapes — no component changes
 * are required.
 */

/* ------------------------------------------------------------------ */
/* Shared primitives                                                    */
/* ------------------------------------------------------------------ */

/** ISO-8601 timestamp string, e.g. "2026-08-21T09:15:00.000Z". */
export type ISODateTime = string;

/** Provenance of a value shown in the UI. Never render data without it. */
export type DataOrigin = "live" | "simulated" | "unavailable";

export type HealthState = "online" | "healthy" | "warning" | "critical" | "offline";

export type Severity = "low" | "medium" | "high" | "critical";

export type Trend = "up" | "down" | "flat";

export interface Unit {
  symbol: string;
  label: string;
}

/* ------------------------------------------------------------------ */
/* Assets & digital twins                                               */
/* ------------------------------------------------------------------ */

export type AssetId =
  | "line-a"
  | "line-b"
  | "boiler"
  | "compressor"
  | "hvac"
  | "solar"
  | "battery"
  | "grid";

export type AssetCategory = "production" | "thermal" | "utility" | "generation" | "storage" | "supply";

/** Whether the asset draws power, supplies it, or does both. */
export type AssetRole = "consumer" | "producer" | "storage" | "bidirectional";

export interface AssetMetric {
  key: string;
  label: string;
  value: number | null;
  unit: string;
  /** Optional operating envelope used to render range bars and thresholds. */
  min?: number;
  max?: number;
  /** Value above/below which the twin flags a deviation. */
  warnAbove?: number;
  warnBelow?: number;
}

export interface Asset {
  id: AssetId;
  name: string;
  shortName: string;
  category: AssetCategory;
  role: AssetRole;
  description: string;
  location: string;
  ratedPowerKw: number;
  status: HealthState;
  /** Positive = consuming, negative = exporting/producing, in kW. */
  powerKw: number;
  /** 0–100. Null when the twin cannot compute it from available signals. */
  efficiencyPct: number | null;
  /** 0–100 utilisation against rated capacity. */
  utilisationPct: number | null;
  lastUpdated: ISODateTime;
  activeAlerts: number;
  /** Headline metric surfaced on the asset card. */
  headline: AssetMetric;
  /** Full sensor/state vector held by the digital twin. */
  metrics: AssetMetric[];
  /** Short recent power trace for the card sparkline (kW). */
  sparkline: number[];
  origin: DataOrigin;
}

export interface SensorReading {
  assetId: AssetId;
  metricKey: string;
  timestamp: ISODateTime;
  value: number;
  unit: string;
  quality: "good" | "uncertain" | "bad";
}

/* ------------------------------------------------------------------ */
/* Energy                                                               */
/* ------------------------------------------------------------------ */

export interface EnergyReading {
  timestamp: ISODateTime;
  /** Total site demand in kW. */
  consumptionKw: number;
  /** Total on-site generation in kW. */
  generationKw: number;
  solarKw: number;
  /** Positive = discharging to site, negative = charging. */
  batteryKw: number;
  /** Positive = importing, negative = exporting. */
  gridKw: number;
  batterySocPct: number;
}

export interface EnergySourceShare {
  source: "Solar" | "Battery" | "Grid";
  energyKwh: number;
  sharePct: number;
  colorToken: string;
}

export interface EnergyFlowNode {
  id: string;
  label: string;
  kind: "source" | "hub" | "storage" | "sink";
  powerKw: number;
  status: HealthState;
  assetId?: AssetId;
  detail?: string;
}

export interface EnergyFlowLink {
  from: string;
  to: string;
  powerKw: number;
  colorToken: string;
  /** False when the path exists but is not carrying power right now. */
  active: boolean;
}

export interface EnergyFlowSnapshot {
  timestamp: ISODateTime;
  nodes: EnergyFlowNode[];
  links: EnergyFlowLink[];
  origin: DataOrigin;
}

/* ------------------------------------------------------------------ */
/* Forecasting (Random Forest)                                          */
/* ------------------------------------------------------------------ */

export type ForecastHorizon = "1h" | "6h" | "24h" | "7d";

export interface ForecastPoint {
  timestamp: ISODateTime;
  /** Measured value. Null for future points. */
  actualKw: number | null;
  /** Model output. Null for history the model was not asked to score. */
  predictedKw: number | null;
  /** Prediction interval bounds. Null when the model exposes no uncertainty. */
  lowerKw: number | null;
  upperKw: number | null;
}

export interface ForecastAccuracy {
  mae: number | null;
  rmse: number | null;
  r2: number | null;
  mapePct: number | null;
  /** Number of samples the metrics were computed over. */
  sampleCount: number;
  evaluatedAt: ISODateTime | null;
}

export interface Forecast {
  modelId: string;
  modelName: string;
  algorithm: string;
  target: string;
  horizon: ForecastHorizon;
  resolutionMinutes: number;
  generatedAt: ISODateTime;
  series: ForecastPoint[];
  accuracy: ForecastAccuracy;
  peak: {
    predictedKw: number;
    expectedAt: ISODateTime;
    /** 0–1 model confidence in the peak window, null when unavailable. */
    confidence: number | null;
  } | null;
  origin: DataOrigin;
}

export interface AssetForecastSummary {
  assetId: AssetId;
  assetName: string;
  currentKw: number;
  predictedPeakKw: number;
  changePct: number;
  trend: Trend;
  mapePct: number | null;
}

/* ------------------------------------------------------------------ */
/* Multi-agent decision layer                                           */
/* ------------------------------------------------------------------ */

export type AgentId =
  | "demand-agent"
  | "generation-agent"
  | "storage-agent"
  | "thermal-agent"
  | "cost-agent"
  | "safety-agent";

export interface Agent {
  id: AgentId;
  name: string;
  scope: string;
  state: "active" | "standby" | "disabled";
  /** Rules currently loaded into this agent. */
  ruleCount: number;
  decisionsToday: number;
  lastActionAt: ISODateTime | null;
  watches: AssetId[];
}

export type DecisionStatus = "pending" | "accepted" | "applied" | "rejected" | "expired";

export type Priority = "low" | "medium" | "high" | "critical";

export interface AIRecommendation {
  id: string;
  agentId: AgentId;
  agentName: string;
  title: string;
  /** The rule expression that fired, in readable form. */
  ruleTriggered: string;
  /** One-paragraph, viva-friendly justification. */
  rationale: string;
  targetAssets: AssetId[];
  priority: Priority;
  status: DecisionStatus;
  createdAt: ISODateTime;
  expectedImpact: {
    label: string;
    value: number | null;
    unit: string;
  }[];
  /** Where the recommendation came from in the pipeline. */
  sourceModule: "rules" | "forecast" | "optimizer" | "anomaly";
  origin: DataOrigin;
}

export interface OperatingObjective {
  mode: "cost-optimal" | "peak-shaving" | "carbon-minimal" | "resilience";
  label: string;
  description: string;
  constraints: string[];
  since: ISODateTime;
}

/* ------------------------------------------------------------------ */
/* Optimisation (Genetic Algorithm)                                     */
/* ------------------------------------------------------------------ */

export interface ScheduleSlot {
  timestamp: ISODateTime;
  baselineKw: number;
  optimisedKw: number | null;
}

export interface OptimizationConstraint {
  id: string;
  label: string;
  expression: string;
  satisfied: boolean;
  slack: string;
}

export interface OptimizationResult {
  runId: string;
  algorithm: string;
  status: "idle" | "running" | "converged" | "failed";
  startedAt: ISODateTime;
  finishedAt: ISODateTime | null;
  generations: number;
  populationSize: number;
  /** Best fitness per generation — drives the convergence chart. */
  convergence: { generation: number; bestFitness: number; meanFitness: number }[];
  objective: {
    summary: string;
    terms: { label: string; weight: number; description: string }[];
  };
  constraints: OptimizationConstraint[];
  schedule: ScheduleSlot[];
  cost: {
    currency: string;
    baseline: number | null;
    optimised: number | null;
  };
  peakDemand: {
    baselineKw: number | null;
    optimisedKw: number | null;
  };
  energyKwh: {
    baseline: number | null;
    optimised: number | null;
  };
  origin: DataOrigin;
}

/* ------------------------------------------------------------------ */
/* Anomaly detection (Isolation Forest)                                 */
/* ------------------------------------------------------------------ */

export type AnomalyStatus = "active" | "acknowledged" | "resolved";

export interface Anomaly {
  id: string;
  assetId: AssetId;
  assetName: string;
  metricKey: string;
  metricLabel: string;
  detectedAt: ISODateTime;
  severity: Severity;
  status: AnomalyStatus;
  /** Isolation Forest score; more negative = more anomalous. */
  score: number;
  /** Score below which the detector labels a point anomalous. */
  threshold: number;
  observedValue: number;
  expectedRange: [number, number];
  unit: string;
  summary: string;
  origin: DataOrigin;
}

/** One scored detection window, used for the score-over-time scatter plot. */
export interface AnomalyScorePoint {
  /** Epoch milliseconds. */
  timestamp: number;
  score: number;
  anomalous: boolean;
  label: string;
}

export interface AnomalyStats {
  total: number;
  active: number;
  acknowledged: number;
  resolved: number;
  bySeverity: Record<Severity, number>;
  meanTimeToResolveMinutes: number | null;
}

/* ------------------------------------------------------------------ */
/* Explainability (SHAP)                                                */
/* ------------------------------------------------------------------ */

export interface FeatureContribution {
  feature: string;
  label: string;
  /** SHAP value — signed contribution in target units. */
  shapValue: number;
  /** The feature's value for this instance. */
  featureValue: number;
  unit: string;
}

/** A model that has a SHAP explainer fitted, and the assets it covers. */
export interface ExplainableModel {
  id: string;
  name: string;
  algorithm: string;
  target: string;
  scope: (AssetId | "site")[];
}

export interface Explanation {
  id: string;
  modelId: string;
  modelName: string;
  algorithm: string;
  assetId: AssetId | "site";
  assetName: string;
  target: string;
  /** Model output being explained. */
  prediction: number;
  /** Expected value E[f(x)] — the SHAP base value. */
  baseValue: number;
  unit: string;
  generatedAt: ISODateTime;
  contributions: FeatureContribution[];
  /** Plain-language narrative for non-specialist viewers. */
  narrative: string;
  origin: DataOrigin;
}

/* ------------------------------------------------------------------ */
/* System status & events                                               */
/* ------------------------------------------------------------------ */

export interface SystemStatus {
  timestamp: ISODateTime;
  overall: HealthState;
  healthScorePct: number;
  operatingMode: OperatingObjective["mode"];
  operatingModeLabel: string;
  twinsOnline: number;
  twinsTotal: number;
  consumptionKw: number;
  generationKw: number;
  renewableSharePct: number;
  forecastNextHourKw: number | null;
  optimizationStatus: OptimizationResult["status"];
  activeAnomalies: number;
  /** 0–100 aggregate model confidence, null when no model has reported. */
  aiConfidencePct: number | null;
  pipelineStages: PipelineStage[];
  origin: DataOrigin;
}

export interface PipelineStage {
  id: string;
  label: string;
  module: string;
  state: "ok" | "degraded" | "down" | "idle";
  detail: string;
}

export type EventKind = "alert" | "anomaly" | "decision" | "optimization" | "forecast" | "system";

export interface SystemEvent {
  id: string;
  kind: EventKind;
  severity: Severity | "info";
  title: string;
  detail: string;
  assetId: AssetId | null;
  timestamp: ISODateTime;
}

/* ------------------------------------------------------------------ */
/* Reporting                                                            */
/* ------------------------------------------------------------------ */

export type ReportPeriod = "day" | "week" | "month";

export interface PerformanceReport {
  period: ReportPeriod;
  rangeStart: ISODateTime;
  rangeEnd: ISODateTime;
  totals: {
    consumptionKwh: number;
    generationKwh: number;
    gridImportKwh: number;
    gridExportKwh: number;
    renewableSharePct: number;
    peakDemandKw: number;
    averageLoadKw: number;
    loadFactorPct: number;
  };
  series: { label: string; consumptionKwh: number; generationKwh: number; peakKw: number }[];
  assetBreakdown: {
    assetId: AssetId;
    assetName: string;
    energyKwh: number;
    sharePct: number;
    efficiencyPct: number | null;
    availabilityPct: number;
  }[];
  forecastPerformance: ForecastAccuracy;
  anomalyStats: AnomalyStats;
  optimizationImpact: {
    runsCompleted: number;
    peakReductionKw: number | null;
    energyShiftedKwh: number | null;
    costDelta: number | null;
    currency: string;
  };
  origin: DataOrigin;
}

/* ------------------------------------------------------------------ */
/* Authentication                                                       */
/* ------------------------------------------------------------------ */

export type UserRole = "operator" | "engineer" | "viewer";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  organisation: string;
}

export interface AuthSession {
  user: AuthUser;
  /** Bearer token issued by the backend. Empty in demo mode. */
  token: string;
  issuedAt: ISODateTime;
  expiresAt: ISODateTime | null;
  /** True when no real identity provider verified these credentials. */
  demo: boolean;
}

export interface SignInInput {
  email: string;
  password: string;
}

export interface SignUpInput {
  name: string;
  email: string;
  password: string;
  organisation: string;
}

/* ------------------------------------------------------------------ */
/* Transport envelope                                                   */
/* ------------------------------------------------------------------ */

/** Every service call returns this so the UI can render provenance honestly. */
export interface DataEnvelope<T> {
  data: T;
  origin: DataOrigin;
  fetchedAt: ISODateTime;
  /** Populated when the adapter fell back or the source is degraded. */
  notice?: string;
}
