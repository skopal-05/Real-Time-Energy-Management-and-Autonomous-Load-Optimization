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

/**
 * The single contract every data source implements.
 *
 * Components depend on this interface — never on `fetch` and never on the mock
 * generators. Connecting the backend means implementing this once.
 */
export interface DataSource {
  readonly name: string;

  getSystemStatus(): Promise<DataEnvelope<SystemStatus>>;
  getEvents(): Promise<DataEnvelope<SystemEvent[]>>;

  getAssets(): Promise<DataEnvelope<Asset[]>>;
  getAsset(assetId: AssetId): Promise<DataEnvelope<Asset | null>>;
  getSensorHistory(
    assetId: AssetId,
    metricKey: string,
    hours: number,
  ): Promise<DataEnvelope<SensorReading[]>>;

  getEnergyWindow(hours: number, stepMinutes: number): Promise<DataEnvelope<EnergyReading[]>>;
  getSourceShares(hours: number): Promise<DataEnvelope<EnergySourceShare[]>>;
  getEnergyFlow(): Promise<DataEnvelope<EnergyFlowSnapshot>>;

  getForecast(horizon: ForecastHorizon): Promise<DataEnvelope<Forecast>>;
  getAssetForecast(assetId: AssetId, horizon: ForecastHorizon): Promise<DataEnvelope<Forecast>>;
  getAssetForecastSummaries(
    horizon: ForecastHorizon,
  ): Promise<DataEnvelope<AssetForecastSummary[]>>;

  getAgents(): Promise<DataEnvelope<Agent[]>>;
  getObjective(): Promise<DataEnvelope<OperatingObjective>>;
  getRecommendations(): Promise<DataEnvelope<AIRecommendation[]>>;

  getOptimization(): Promise<DataEnvelope<OptimizationResult>>;

  getAnomalies(): Promise<DataEnvelope<Anomaly[]>>;
  /** Scored windows for the detection scatter plot, plus the decision threshold. */
  getAnomalyScores(hours: number): Promise<DataEnvelope<{ points: AnomalyScorePoint[]; threshold: number }>>;

  getExplainableModels(): Promise<DataEnvelope<ExplainableModel[]>>;
  /** Returns `null` when no SHAP explainer exists for the model/asset pair. */
  getExplanation(modelId: string, assetId: AssetId | "site"): Promise<DataEnvelope<Explanation | null>>;

  getReport(period: ReportPeriod): Promise<DataEnvelope<PerformanceReport>>;
}

/** Thrown by the HTTP adapter so the UI can render a real error state. */
export class DataSourceError extends Error {
  readonly status: number | null;
  readonly endpoint: string;

  constructor(message: string, endpoint: string, status: number | null = null) {
    super(message);
    this.name = "DataSourceError";
    this.endpoint = endpoint;
    this.status = status;
  }
}
