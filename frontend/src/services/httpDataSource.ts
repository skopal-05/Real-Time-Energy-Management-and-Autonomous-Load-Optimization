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
import { apiConfig } from "./config";
import { DataSourceError, type DataSource } from "./dataSource";

/**
 * REST adapter for the Python backend.
 *
 * Endpoint paths below are the contract this frontend expects. Each one must
 * return the corresponding interface from `src/lib/types.ts` as raw JSON — the
 * envelope (origin/fetchedAt) is added here, so the backend does not need to
 * know about it.
 *
 * Wire it up by setting, in `.env.local`:
 *   NEXT_PUBLIC_API_MODE=live
 *   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
 */
async function request<T>(path: string, params?: Record<string, string | number>): Promise<DataEnvelope<T>> {
  if (!apiConfig.baseUrl) {
    throw new DataSourceError("No API base URL is configured.", path);
  }
  const url = new URL(`${apiConfig.baseUrl.replace(/\/$/, "")}${path}`);
  for (const [k, v] of Object.entries(params ?? {})) url.searchParams.set(k, String(v));

  let response: Response;
  try {
    response = await fetch(url.toString(), {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
  } catch {
    throw new DataSourceError(
      `Could not reach the backend at ${url.origin}. Is the API server running?`,
      path,
    );
  }

  if (!response.ok) {
    throw new DataSourceError(
      `Backend responded with ${response.status} ${response.statusText}.`,
      path,
      response.status,
    );
  }

  const data = (await response.json()) as T;
  return { data, origin: "live", fetchedAt: new Date().toISOString() };
}

export const httpDataSource: DataSource = {
  name: `Live API (${apiConfig.baseUrl || "not configured"})`,

  getSystemStatus: () => request<SystemStatus>("/system/status"),
  getEvents: () => request<SystemEvent[]>("/system/events"),

  getAssets: () => request<Asset[]>("/assets"),
  getAsset: (assetId) => request<Asset | null>(`/assets/${assetId}`),
  getSensorHistory: (assetId: AssetId, metricKey: string, hours: number) =>
    request<SensorReading[]>(`/assets/${assetId}/sensors/${metricKey}`, { hours }),

  getEnergyWindow: (hours: number, stepMinutes: number) =>
    request<EnergyReading[]>("/energy/window", { hours, step_minutes: stepMinutes }),
  getSourceShares: (hours: number) => request<EnergySourceShare[]>("/energy/sources", { hours }),
  getEnergyFlow: () => request<EnergyFlowSnapshot>("/energy/flow"),

  getForecast: (horizon: ForecastHorizon) => request<Forecast>("/forecast/site", { horizon }),
  getAssetForecast: (assetId: AssetId, horizon: ForecastHorizon) =>
    request<Forecast>(`/forecast/asset/${assetId}`, { horizon }),
  getAssetForecastSummaries: (horizon: ForecastHorizon) =>
    request<AssetForecastSummary[]>("/forecast/assets/summary", { horizon }),

  getAgents: () => request<Agent[]>("/agents"),
  getObjective: () => request<OperatingObjective>("/agents/objective"),
  getRecommendations: () => request<AIRecommendation[]>("/agents/recommendations"),

  getOptimization: () => request<OptimizationResult>("/optimization/latest"),

  getAnomalies: () => request<Anomaly[]>("/anomalies"),
  getAnomalyScores: (hours: number) =>
    request<{ points: AnomalyScorePoint[]; threshold: number }>("/anomalies/scores", { hours }),

  getExplainableModels: () => request<ExplainableModel[]>("/explain/models"),

  getExplanation: (modelId: string, assetId: AssetId | "site") =>
    request<Explanation | null>("/explain", { model_id: modelId, asset_id: assetId }),

  getReport: (period: ReportPeriod) => request<PerformanceReport>("/reports", { period }),
};
