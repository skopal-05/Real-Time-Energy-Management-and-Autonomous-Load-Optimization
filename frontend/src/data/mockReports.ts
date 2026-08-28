import { ASSET_REGISTRY, ASSET_IDS, CURRENCY, CONSUMER_ASSET_IDS } from "@/lib/constants";
import type { PerformanceReport, ReportPeriod } from "@/lib/types";
import { roundTo } from "@/lib/utils";
import { DAY_MS, HOUR_MS, consumerLoadKw, generateEnergySeries, solarOutputKw, tariffPerKwh } from "./scenario";
import { buildAnomalies, buildAnomalyStats } from "./mockAnomalies";
import { buildSiteForecast } from "./mockForecast";

const PERIOD_CONFIG: Record<ReportPeriod, { days: number; buckets: number; bucketLabel: (i: number, end: number) => string }> = {
  day: {
    days: 1,
    buckets: 12,
    bucketLabel: (i) => `${String(i * 2).padStart(2, "0")}:00`,
  },
  week: {
    days: 7,
    buckets: 7,
    bucketLabel: (i, end) =>
      new Date(end - (6 - i) * DAY_MS).toLocaleDateString("en-GB", { weekday: "short" }),
  },
  month: {
    days: 30,
    buckets: 10,
    bucketLabel: (i, end) =>
      new Date(end - (9 - i) * 3 * DAY_MS).toLocaleDateString("en-GB", { day: "2-digit", month: "short" }),
  },
};

export function buildReport(nowMs: number, period: ReportPeriod): PerformanceReport {
  const cfg = PERIOD_CONFIG[period];
  const rangeEnd = nowMs;
  const rangeStart = nowMs - cfg.days * DAY_MS;
  const stepMinutes = period === "day" ? 15 : 60;
  const series = generateEnergySeries(rangeStart, rangeEnd, stepMinutes);
  const hoursPerSample = stepMinutes / 60;

  let consumptionKwh = 0;
  let generationKwh = 0;
  let gridImportKwh = 0;
  let gridExportKwh = 0;
  let peakDemandKw = 0;

  for (const p of series) {
    consumptionKwh += p.consumptionKw * hoursPerSample;
    generationKwh += p.generationKw * hoursPerSample;
    if (p.gridKw > 0) gridImportKwh += p.gridKw * hoursPerSample;
    else gridExportKwh += -p.gridKw * hoursPerSample;
    peakDemandKw = Math.max(peakDemandKw, p.consumptionKw);
  }

  const averageLoadKw = consumptionKwh / (cfg.days * 24);

  // Bucketed series for the report chart.
  const bucketMs = (rangeEnd - rangeStart) / cfg.buckets;
  const buckets = Array.from({ length: cfg.buckets }, (_, i) => {
    const bStart = rangeStart + i * bucketMs;
    const bEnd = bStart + bucketMs;
    const inBucket = series.filter((p) => {
      const t = new Date(p.timestamp).getTime();
      return t >= bStart && t < bEnd;
    });
    return {
      label: cfg.bucketLabel(i, rangeEnd),
      consumptionKwh: roundTo(inBucket.reduce((a, p) => a + p.consumptionKw * hoursPerSample, 0), 0),
      generationKwh: roundTo(inBucket.reduce((a, p) => a + p.generationKw * hoursPerSample, 0), 0),
      peakKw: roundTo(inBucket.reduce((a, p) => Math.max(a, p.consumptionKw), 0), 0),
    };
  });

  // Asset-level energy split over the same window.
  const assetEnergy = ASSET_IDS.map((id) => {
    let kwh = 0;
    if (CONSUMER_ASSET_IDS.includes(id)) {
      for (let t = rangeStart; t < rangeEnd; t += HOUR_MS) kwh += consumerLoadKw(id, t);
    } else if (id === "solar") {
      for (let t = rangeStart; t < rangeEnd; t += HOUR_MS) kwh += solarOutputKw(t);
    } else if (id === "battery") {
      kwh = series.reduce((a, p) => a + Math.max(p.batteryKw, 0) * hoursPerSample, 0);
    } else {
      kwh = gridImportKwh;
    }
    return { id, kwh };
  });

  const consumerTotal = assetEnergy
    .filter((a) => CONSUMER_ASSET_IDS.includes(a.id))
    .reduce((acc, a) => acc + a.kwh, 0);

  const forecast = buildSiteForecast(nowMs, "24h");
  const anomalies = buildAnomalies(nowMs);

  return {
    period,
    rangeStart: new Date(rangeStart).toISOString(),
    rangeEnd: new Date(rangeEnd).toISOString(),
    totals: {
      consumptionKwh: roundTo(consumptionKwh, 0),
      generationKwh: roundTo(generationKwh, 0),
      gridImportKwh: roundTo(gridImportKwh, 0),
      gridExportKwh: roundTo(gridExportKwh, 0),
      renewableSharePct: roundTo((generationKwh / Math.max(consumptionKwh, 1)) * 100, 1),
      peakDemandKw: roundTo(peakDemandKw, 1),
      averageLoadKw: roundTo(averageLoadKw, 1),
      loadFactorPct: roundTo((averageLoadKw / Math.max(peakDemandKw, 1)) * 100, 1),
    },
    series: buckets,
    assetBreakdown: assetEnergy
      .filter((a) => CONSUMER_ASSET_IDS.includes(a.id))
      .map((a) => ({
        assetId: a.id,
        assetName: ASSET_REGISTRY[a.id].name,
        energyKwh: roundTo(a.kwh, 0),
        sharePct: roundTo((a.kwh / Math.max(consumerTotal, 1)) * 100, 1),
        efficiencyPct:
          a.id === "line-a" ? 91.2 : a.id === "line-b" ? 88.4 : a.id === "boiler" ? 83.6 : a.id === "hvac" ? 78.9 : 71.5,
        availabilityPct: a.id === "compressor" ? 96.1 : 99.2,
      })),
    forecastPerformance: forecast.accuracy,
    anomalyStats: buildAnomalyStats(anomalies),
    optimizationImpact: {
      runsCompleted: period === "day" ? 24 : period === "week" ? 168 : 720,
      peakReductionKw: roundTo(peakDemandKw * 0.086, 1),
      energyShiftedKwh: roundTo(consumptionKwh * 0.041, 0),
      costDelta: roundTo(
        -series.reduce((a, p) => a + p.consumptionKw * hoursPerSample * tariffPerKwh(new Date(p.timestamp).getTime()) * 0.037, 0),
        0,
      ),
      currency: CURRENCY,
    },
    origin: "simulated",
  };
}
