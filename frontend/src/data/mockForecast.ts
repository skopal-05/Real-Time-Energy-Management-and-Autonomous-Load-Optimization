import { ASSET_REGISTRY, CONSUMER_ASSET_IDS } from "@/lib/constants";
import type {
  AssetForecastSummary,
  AssetId,
  Forecast,
  ForecastAccuracy,
  ForecastHorizon,
  ForecastPoint,
} from "@/lib/types";
import { createRng, hashString, mean, roundTo } from "@/lib/utils";
import { MINUTE_MS, consumerLoadKw, quantize, siteConsumptionKw } from "./scenario";

interface HorizonConfig {
  label: string;
  stepMinutes: number;
  historySteps: number;
  futureSteps: number;
}

export const HORIZONS: Record<ForecastHorizon, HorizonConfig> = {
  "1h": { label: "Next 1 hour", stepMinutes: 5, historySteps: 24, futureSteps: 12 },
  "6h": { label: "Next 6 hours", stepMinutes: 15, historySteps: 24, futureSteps: 24 },
  "24h": { label: "Next 24 hours", stepMinutes: 30, historySteps: 24, futureSteps: 48 },
  "7d": { label: "Next 7 days", stepMinutes: 180, historySteps: 24, futureSteps: 56 },
};

/**
 * Random-Forest-style residual model.
 *
 * A tree ensemble does not extrapolate smoothly, so its error grows in steps as
 * the horizon extends and is larger during ramps. We reproduce that character
 * here so the accuracy panels show believable, non-flattering numbers.
 */
function residual(key: string, t: number, stepsAhead: number, magnitude: number): number {
  const rng = createRng(hashString(key) ^ Math.floor(t / MINUTE_MS));
  const base = (rng() - 0.48) * 2;
  const horizonPenalty = 1 + Math.min(stepsAhead, 48) * 0.045;
  return base * magnitude * horizonPenalty;
}

function accuracyFrom(points: ForecastPoint[]): ForecastAccuracy {
  const paired = points.filter(
    (p): p is ForecastPoint & { actualKw: number; predictedKw: number } =>
      p.actualKw !== null && p.predictedKw !== null,
  );
  if (paired.length === 0) {
    return { mae: null, rmse: null, r2: null, mapePct: null, sampleCount: 0, evaluatedAt: null };
  }
  const errors = paired.map((p) => p.predictedKw - p.actualKw);
  const mae = mean(errors.map(Math.abs)) ?? 0;
  const rmse = Math.sqrt(mean(errors.map((e) => e * e)) ?? 0);
  const actualMean = mean(paired.map((p) => p.actualKw)) ?? 0;
  const ssRes = errors.reduce((a, e) => a + e * e, 0);
  const ssTot = paired.reduce((a, p) => a + (p.actualKw - actualMean) ** 2, 0);
  const mape =
    mean(paired.filter((p) => p.actualKw !== 0).map((p) => Math.abs((p.predictedKw - p.actualKw) / p.actualKw) * 100)) ??
    null;

  return {
    mae: roundTo(mae, 2),
    rmse: roundTo(rmse, 2),
    r2: ssTot === 0 ? null : roundTo(1 - ssRes / ssTot, 4),
    mapePct: mape === null ? null : roundTo(mape, 2),
    sampleCount: paired.length,
    evaluatedAt: paired[paired.length - 1].timestamp,
  };
}

/** Site-level load forecast produced by the Random Forest regressor. */
export function buildSiteForecast(nowMs: number, horizon: ForecastHorizon): Forecast {
  const cfg = HORIZONS[horizon];
  const stepMs = cfg.stepMinutes * MINUTE_MS;
  const anchor = quantize(nowMs, stepMs);
  const series: ForecastPoint[] = [];

  for (let i = -cfg.historySteps; i <= cfg.futureSteps; i += 1) {
    const t = anchor + i * stepMs;
    const truth = siteConsumptionKw(t);
    const isFuture = i > 0;
    const magnitude = truth * 0.028;
    const pred = truth + residual("site-load", t, Math.max(i, 0), magnitude);
    // Interval widens with the horizon — narrow in-sample, wider out-of-sample.
    const spread = truth * (isFuture ? 0.035 + i * 0.0022 : 0.02);

    series.push({
      timestamp: new Date(t).toISOString(),
      actualKw: isFuture ? null : truth,
      predictedKw: roundTo(pred, 1),
      lowerKw: roundTo(pred - spread * 1.96, 1),
      upperKw: roundTo(pred + spread * 1.96, 1),
    });
  }

  const future = series.filter((p) => p.actualKw === null && p.predictedKw !== null);
  const peakPoint = future.reduce<ForecastPoint | null>(
    (best, p) => (best === null || (p.predictedKw ?? 0) > (best.predictedKw ?? 0) ? p : best),
    null,
  );

  return {
    modelId: "rf-site-load-v3",
    modelName: "Site Load Forecaster",
    algorithm: "Random Forest Regressor",
    target: "Total site demand",
    horizon,
    resolutionMinutes: cfg.stepMinutes,
    generatedAt: new Date(anchor).toISOString(),
    series,
    accuracy: accuracyFrom(series),
    peak:
      peakPoint && peakPoint.predictedKw !== null
        ? {
            predictedKw: peakPoint.predictedKw,
            expectedAt: peakPoint.timestamp,
            confidence: roundTo(0.86 - cfg.futureSteps * 0.0018, 2),
          }
        : null,
    origin: "simulated",
  };
}

/** Per-asset forecast for the same horizon, used by the asset detail view. */
export function buildAssetForecast(assetId: AssetId, nowMs: number, horizon: ForecastHorizon): Forecast {
  const cfg = HORIZONS[horizon];
  const stepMs = cfg.stepMinutes * MINUTE_MS;
  const anchor = quantize(nowMs, stepMs);
  const isConsumer = CONSUMER_ASSET_IDS.includes(assetId);
  const series: ForecastPoint[] = [];

  for (let i = -cfg.historySteps; i <= cfg.futureSteps; i += 1) {
    const t = anchor + i * stepMs;
    const truth = isConsumer
      ? consumerLoadKw(assetId, t)
      : roundTo(siteConsumptionKw(t) * 0.18, 1);
    const isFuture = i > 0;
    const pred = truth + residual(assetId, t, Math.max(i, 0), truth * 0.045);
    const spread = truth * (isFuture ? 0.05 + i * 0.003 : 0.028);
    series.push({
      timestamp: new Date(t).toISOString(),
      actualKw: isFuture ? null : truth,
      predictedKw: roundTo(pred, 1),
      lowerKw: roundTo(pred - spread * 1.96, 1),
      upperKw: roundTo(pred + spread * 1.96, 1),
    });
  }

  const future = series.filter((p) => p.actualKw === null);
  const peakPoint = future.reduce<ForecastPoint | null>(
    (best, p) => (best === null || (p.predictedKw ?? 0) > (best.predictedKw ?? 0) ? p : best),
    null,
  );

  return {
    modelId: `rf-${assetId}-load-v2`,
    modelName: `${ASSET_REGISTRY[assetId].name} Forecaster`,
    algorithm: "Random Forest Regressor",
    target: `${ASSET_REGISTRY[assetId].name} demand`,
    horizon,
    resolutionMinutes: cfg.stepMinutes,
    generatedAt: new Date(anchor).toISOString(),
    series,
    accuracy: accuracyFrom(series),
    peak:
      peakPoint && peakPoint.predictedKw !== null
        ? { predictedKw: peakPoint.predictedKw, expectedAt: peakPoint.timestamp, confidence: 0.81 }
        : null,
    origin: "simulated",
  };
}

export function buildAssetForecastSummaries(
  nowMs: number,
  horizon: ForecastHorizon,
): AssetForecastSummary[] {
  const cfg = HORIZONS[horizon];
  const stepMs = cfg.stepMinutes * MINUTE_MS;

  return CONSUMER_ASSET_IDS.map((id) => {
    const current = consumerLoadKw(id, nowMs);
    let peak = 0;
    for (let i = 1; i <= cfg.futureSteps; i += 1) {
      peak = Math.max(peak, consumerLoadKw(id, nowMs + i * stepMs));
    }
    const change = current === 0 ? 0 : ((peak - current) / current) * 100;
    return {
      assetId: id,
      assetName: ASSET_REGISTRY[id].name,
      currentKw: roundTo(current, 1),
      predictedPeakKw: roundTo(peak, 1),
      changePct: roundTo(change, 1),
      trend: change > 4 ? "up" : change < -4 ? "down" : "flat",
      mapePct: roundTo(2.4 + (hashString(id) % 180) / 100, 2),
    };
  });
}
