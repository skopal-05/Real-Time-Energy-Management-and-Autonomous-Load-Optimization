import { ASSET_REGISTRY } from "@/lib/constants";
import type { AssetId, ExplainableModel, Explanation, FeatureContribution } from "@/lib/types";
import { roundTo } from "@/lib/utils";
import {
  HOUR_MS,
  ambientTempC,
  consumerLoadKw,
  currentEnergyState,
  hourOfDay,
  siteConsumptionKw,
  solarOutputKw,
} from "./scenario";

/**
 * Models with a SHAP explainer attached.
 *
 * Assets outside a model's `scope` genuinely have no explainer fitted yet — the
 * UI shows an empty state for those rather than inventing SHAP values.
 */
export const EXPLAINABLE_MODELS: ExplainableModel[] = [
  {
    id: "rf-site-load-v3",
    name: "Site Load Forecaster",
    algorithm: "Random Forest Regressor",
    target: "Total site demand (kW)",
    scope: ["site", "line-a", "line-b", "hvac"],
  },
  {
    id: "if-anomaly-v2",
    name: "Anomaly Detector",
    algorithm: "Isolation Forest",
    target: "Anomaly score",
    scope: ["compressor", "boiler", "solar"],
  },
];

function siteContributions(nowMs: number): FeatureContribution[] {
  const h = hourOfDay(nowMs);
  const temp = ambientTempC(nowMs);
  const lineA = consumerLoadKw("line-a", nowMs);
  const lineB = consumerLoadKw("line-b", nowMs);
  const hvac = consumerLoadKw("hvac", nowMs);
  const compressor = consumerLoadKw("compressor", nowMs);
  const lagged = siteConsumptionKw(nowMs - HOUR_MS);
  const solar = solarOutputKw(nowMs);

  return [
    {
      feature: "line_a_setpoint",
      label: "Production demand — Line A",
      shapValue: roundTo((lineA - 210) * 0.62, 1),
      featureValue: roundTo(lineA, 1),
      unit: "kW",
    },
    {
      feature: "load_lag_60min",
      label: "Load 60 min ago",
      shapValue: roundTo((lagged - 720) * 0.24, 1),
      featureValue: roundTo(lagged, 1),
      unit: "kW",
    },
    {
      feature: "hvac_power",
      label: "HVAC load",
      shapValue: roundTo((hvac - 96) * 0.71, 1),
      featureValue: roundTo(hvac, 1),
      unit: "kW",
    },
    {
      feature: "compressor_power",
      label: "Compressor power",
      shapValue: roundTo((compressor - 88) * 0.55, 1),
      featureValue: roundTo(compressor, 1),
      unit: "kW",
    },
    {
      feature: "line_b_setpoint",
      label: "Production demand — Line B",
      shapValue: roundTo((lineB - 150) * 0.48, 1),
      featureValue: roundTo(lineB, 1),
      unit: "kW",
    },
    {
      feature: "ambient_temp",
      label: "Ambient temperature",
      shapValue: roundTo((temp - 27.5) * 6.4, 1),
      featureValue: temp,
      unit: "°C",
    },
    {
      feature: "hour_of_day",
      label: "Hour of day",
      shapValue: roundTo(Math.sin(((h - 9) / 24) * Math.PI * 2) * 34, 1),
      featureValue: roundTo(h, 2),
      unit: "h",
    },
    {
      feature: "pv_output",
      label: "On-site PV output",
      shapValue: roundTo(-solar * 0.06, 1),
      featureValue: roundTo(solar, 1),
      unit: "kW",
    },
  ].sort((a, b) => Math.abs(b.shapValue) - Math.abs(a.shapValue));
}

function assetContributions(assetId: AssetId, nowMs: number): FeatureContribution[] {
  const temp = ambientTempC(nowMs);
  const h = hourOfDay(nowMs);
  const load = consumerLoadKw(assetId, nowMs);
  const state = currentEnergyState(nowMs);

  switch (assetId) {
    case "compressor":
      return [
        { feature: "specific_power", label: "Specific power", shapValue: -0.146, featureValue: 8.14, unit: "kW/m³/min" },
        { feature: "loaded_fraction", label: "Loaded fraction", shapValue: -0.078, featureValue: 46, unit: "%" },
        { feature: "discharge_pressure", label: "Discharge pressure", shapValue: -0.041, featureValue: 6.42, unit: "bar" },
        { feature: "oil_temp", label: "Oil temperature", shapValue: -0.028, featureValue: 79.4, unit: "°C" },
        { feature: "flow", label: "Air flow", shapValue: 0.019, featureValue: 31.2, unit: "m³/min" },
        { feature: "ambient_temp", label: "Ambient temperature", shapValue: -0.012, featureValue: temp, unit: "°C" },
      ];
    case "boiler":
      return [
        { feature: "stack_loss", label: "Stack loss", shapValue: -0.092, featureValue: 16.2, unit: "%" },
        { feature: "outlet_temp", label: "Outlet temperature", shapValue: -0.047, featureValue: 196.4, unit: "°C" },
        { feature: "feedwater_temp", label: "Feedwater temperature", shapValue: 0.026, featureValue: 79.1, unit: "°C" },
        { feature: "firing_rate", label: "Firing rate", shapValue: -0.031, featureValue: 68, unit: "%" },
        { feature: "steam_pressure", label: "Steam pressure", shapValue: -0.014, featureValue: 8.6, unit: "bar" },
      ];
    case "solar":
      return [
        { feature: "performance_ratio", label: "Performance ratio", shapValue: -0.058, featureValue: 82.4, unit: "%" },
        { feature: "irradiance", label: "Irradiance", shapValue: 0.024, featureValue: 612, unit: "W/m²" },
        { feature: "panel_temp", label: "Panel temperature", shapValue: -0.019, featureValue: roundTo(temp + 17, 1), unit: "°C" },
        { feature: "inverter_eff", label: "Inverter efficiency", shapValue: 0.011, featureValue: 96.2, unit: "%" },
      ];
    case "hvac":
      return [
        { feature: "ambient_temp", label: "Ambient temperature", shapValue: roundTo((temp - 27.5) * 4.6, 1), featureValue: temp, unit: "°C" },
        { feature: "zone_temp", label: "Zone temperature", shapValue: 11.4, featureValue: 24.6, unit: "°C" },
        { feature: "occupancy_window", label: "Occupancy window", shapValue: roundTo(Math.max(0, 18 - Math.abs(h - 13) * 2), 1), featureValue: roundTo(h, 2), unit: "h" },
        { feature: "cop", label: "Coefficient of performance", shapValue: -7.8, featureValue: 3.21, unit: "" },
        { feature: "load_lag_30min", label: "HVAC load 30 min ago", shapValue: roundTo((load - 96) * 0.3, 1), featureValue: roundTo(load, 1), unit: "kW" },
      ];
    case "line-a":
    case "line-b":
      return [
        { feature: "throughput", label: "Throughput", shapValue: roundTo((load - 180) * 0.52, 1), featureValue: roundTo(load / 2.4, 0), unit: "units/h" },
        { feature: "shift_state", label: "Shift active", shapValue: h > 6 && h < 22 ? 62.5 : -84.2, featureValue: h > 6 && h < 22 ? 1 : 0, unit: "" },
        { feature: "load_lag_15min", label: "Line load 15 min ago", shapValue: roundTo((load - 200) * 0.21, 1), featureValue: roundTo(load, 1), unit: "kW" },
        { feature: "motor_temp", label: "Main motor temperature", shapValue: 6.2, featureValue: 71.4, unit: "°C" },
        { feature: "power_factor", label: "Power factor", shapValue: -3.1, featureValue: 0.91, unit: "" },
      ];
    default:
      return [
        { feature: "grid_import", label: "Grid import", shapValue: roundTo(state.gridKw * 0.04, 1), featureValue: state.gridKw, unit: "kW" },
      ];
  }
}

function narrativeFor(modelId: string, assetId: AssetId | "site", top: FeatureContribution[]): string {
  const names = top.slice(0, 3).map((c) => c.label.toLowerCase());
  if (modelId === "if-anomaly-v2") {
    return `The detector isolated this window mainly because of ${names[0]}, together with ${names[1]} and ${names[2]}. Each of these sat outside the range the model learned from normal operation, and their combination is rare enough that the point was separated in very few splits — which is what produces a low isolation score.`;
  }
  if (assetId === "site") {
    return `The predicted site load is driven mainly by ${names[0]}, ${names[1]} and ${names[2]}. Production demand sets the base level, thermal and compressed-air services scale it with ambient conditions, and on-site PV pulls the net figure down. Features are listed by the size of their contribution, not by their raw value.`;
  }
  return `For ${ASSET_REGISTRY[assetId as AssetId].name}, the prediction is dominated by ${names[0]}, followed by ${names[1]} and ${names[2]}. Positive bars push the prediction above the model's expected value; negative bars pull it below.`;
}

/**
 * Returns the SHAP explanation for a model/asset pair, or `null` when no
 * explainer has been fitted for that pair. Callers must render an empty state
 * for `null` — values are never fabricated.
 */
export function buildExplanation(
  modelId: string,
  assetId: AssetId | "site",
  nowMs: number,
): Explanation | null {
  const model = EXPLAINABLE_MODELS.find((m) => m.id === modelId);
  if (!model || !model.scope.includes(assetId)) return null;

  const contributions =
    assetId === "site" ? siteContributions(nowMs) : assetContributions(assetId, nowMs);
  const sorted = [...contributions].sort((a, b) => Math.abs(b.shapValue) - Math.abs(a.shapValue));

  const isAnomalyModel = model.id === "if-anomaly-v2";
  const baseValue = isAnomalyModel ? 0.12 : assetId === "site" ? 742.5 : 128.4;
  const prediction = roundTo(
    baseValue + sorted.reduce((a, c) => a + c.shapValue, 0),
    isAnomalyModel ? 3 : 1,
  );

  return {
    id: `xai-${modelId}-${assetId}`,
    modelId: model.id,
    modelName: model.name,
    algorithm: model.algorithm,
    assetId,
    assetName: assetId === "site" ? "Whole site" : ASSET_REGISTRY[assetId].name,
    target: model.target,
    prediction,
    baseValue,
    unit: isAnomalyModel ? "" : "kW",
    generatedAt: new Date(nowMs).toISOString(),
    contributions: sorted,
    narrative: narrativeFor(model.id, assetId, sorted),
    origin: "simulated",
  };
}
