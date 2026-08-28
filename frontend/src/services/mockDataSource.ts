import type {
  Agent,
  AIRecommendation,
  Anomaly,
  AnomalyScorePoint,
  Asset,
  AssetForecastSummary,
  AssetId,
  DataEnvelope,
  EnergyFlowSnapshot,
  EnergyReading,
  EnergySourceShare,
  ExplainableModel,
  Explanation,
  Forecast,
  ForecastHorizon,
  OperatingObjective,
  OptimizationResult,
  PerformanceReport,
  ReportPeriod,
  SensorReading,
  SystemEvent,
  SystemStatus,
} from "@/lib/types";
import { buildAssets, buildSensorHistory } from "@/data/mockAssets";
import { buildEnergyFlow, buildEnergyWindow, buildSourceShares } from "@/data/mockEnergy";
import { buildAssetForecast, buildAssetForecastSummaries, buildSiteForecast } from "@/data/mockForecast";
import { buildAgents, buildObjective, buildRecommendations } from "@/data/mockDecisions";
import { buildOptimization } from "@/data/mockOptimization";
import { ANOMALY_THRESHOLD, buildAnomalies, buildScoreScatter } from "@/data/mockAnomalies";
import { EXPLAINABLE_MODELS, buildExplanation } from "@/data/mockExplain";
import { buildReport } from "@/data/mockReports";
import { buildEvents, buildSystemStatus } from "@/data/mockSystem";
import { quantize } from "@/data/scenario";
import { apiConfig } from "./config";
import type { DataSource } from "./dataSource";

const NOTICE = "Demo scenario — deterministic simulation, not measured plant data.";

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function envelope<T>(build: (nowMs: number) => T): Promise<DataEnvelope<T>> {
  await delay(apiConfig.mockLatencyMs);
  // Every builder is given the same quantised sampling instant, so figures
  // derived in different modules agree with each other exactly.
  const now = quantize(Date.now());
  return {
    data: build(now),
    origin: "simulated",
    fetchedAt: new Date().toISOString(),
    notice: NOTICE,
  };
}

/**
 * Demo data source.
 *
 * Everything it returns comes from the deterministic scenario model in
 * `src/data`. It is tagged `origin: "simulated"` end-to-end so no screen can
 * present these numbers as measurements.
 */
export const mockDataSource: DataSource = {
  name: "Demo scenario (simulated)",

  getSystemStatus: () => envelope<SystemStatus>((now) => buildSystemStatus(now)),
  getEvents: () => envelope<SystemEvent[]>((now) => buildEvents(now)),

  getAssets: () => envelope<Asset[]>((now) => buildAssets(now)),
  getAsset: (assetId) =>
    envelope<Asset | null>((now) => buildAssets(now).find((a) => a.id === assetId) ?? null),
  getSensorHistory: (assetId: AssetId, metricKey: string, hours: number) =>
    envelope<SensorReading[]>((now) => buildSensorHistory(assetId, metricKey, now, hours)),

  getEnergyWindow: (hours: number, stepMinutes: number) =>
    envelope<EnergyReading[]>((now) => buildEnergyWindow(now, hours, stepMinutes)),
  getSourceShares: (hours: number) =>
    envelope<EnergySourceShare[]>((now) => buildSourceShares(now, hours)),
  getEnergyFlow: () => envelope<EnergyFlowSnapshot>((now) => buildEnergyFlow(now)),

  getForecast: (horizon: ForecastHorizon) =>
    envelope<Forecast>((now) => buildSiteForecast(now, horizon)),
  getAssetForecast: (assetId: AssetId, horizon: ForecastHorizon) =>
    envelope<Forecast>((now) => buildAssetForecast(assetId, now, horizon)),
  getAssetForecastSummaries: (horizon: ForecastHorizon) =>
    envelope<AssetForecastSummary[]>((now) => buildAssetForecastSummaries(now, horizon)),

  getAgents: () => envelope<Agent[]>((now) => buildAgents(now)),
  getObjective: () => envelope<OperatingObjective>((now) => buildObjective(now)),
  getRecommendations: () => envelope<AIRecommendation[]>((now) => buildRecommendations(now)),

  getOptimization: () => envelope<OptimizationResult>((now) => buildOptimization(now)),

  getAnomalies: () => envelope<Anomaly[]>((now) => buildAnomalies(now)),
  getAnomalyScores: (hours: number) =>
    envelope<{ points: AnomalyScorePoint[]; threshold: number }>((now) => ({
      points: buildScoreScatter(now, buildAnomalies(now)).filter(
        (p) => p.timestamp >= now - hours * 60 * 60 * 1000,
      ),
      threshold: ANOMALY_THRESHOLD,
    })),

  getExplainableModels: () => envelope<ExplainableModel[]>(() => EXPLAINABLE_MODELS),

  getExplanation: (modelId: string, assetId: AssetId | "site") =>
    envelope<Explanation | null>((now) => buildExplanation(modelId, assetId, now)),

  getReport: (period: ReportPeriod) => envelope<PerformanceReport>((now) => buildReport(now, period)),
};
