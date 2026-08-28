import { ASSET_IDS, ASSET_REGISTRY, CONSUMER_ASSET_IDS } from "@/lib/constants";
import type { Asset, AssetId, AssetMetric, HealthState, SensorReading } from "@/lib/types";
import { clamp, createRng, hashString, roundTo } from "@/lib/utils";
import {
  MINUTE_MS,
  HOUR_MS,
  ambientTempC,
  consumerLoadKw,
  currentEnergyState,
  irradianceWm2,
  quantize,
  solarOutputKw,
} from "./scenario";

/** Assets whose twin is deliberately degraded in the demo scenario. */
const SCRIPTED_STATES: Partial<Record<AssetId, HealthState>> = {
  compressor: "warning",
  boiler: "warning",
};

function statusFor(assetId: AssetId, utilisation: number | null): HealthState {
  const scripted = SCRIPTED_STATES[assetId];
  if (scripted) return scripted;
  if (utilisation !== null && utilisation > 96) return "warning";
  return "healthy";
}

function sparkline(assetId: AssetId, nowMs: number, snapshotAt: number): number[] {
  const points: number[] = [];
  for (let i = 23; i >= 0; i -= 1) {
    const t = nowMs - i * 15 * MINUTE_MS;
    if (CONSUMER_ASSET_IDS.includes(assetId)) {
      points.push(consumerLoadKw(assetId, t));
    } else if (assetId === "solar") {
      points.push(solarOutputKw(t));
    } else {
      // Battery and grid share the site balance; approximate with net demand.
      const net = CONSUMER_ASSET_IDS.reduce((acc, id) => acc + consumerLoadKw(id, t), 0) - solarOutputKw(t);
      points.push(roundTo(assetId === "grid" ? Math.max(net, 0) : Math.abs(net) * 0.28, 1));
    }
  }
  void snapshotAt;
  return points;
}

function metricsFor(assetId: AssetId, nowMs: number): AssetMetric[] {
  const rng = createRng(hashString(assetId) ^ Math.floor(nowMs / (10 * MINUTE_MS)));
  const jitter = (amp: number) => (rng() - 0.5) * 2 * amp;
  const rated = ASSET_REGISTRY[assetId].ratedPowerKw;
  const energy = currentEnergyState(nowMs);
  const temp = ambientTempC(nowMs);

  switch (assetId) {
    case "line-a":
    case "line-b": {
      const load = consumerLoadKw(assetId, nowMs);
      const throughput = roundTo((load / rated) * (assetId === "line-a" ? 148 : 96) + jitter(3), 0);
      return [
        { key: "power", label: "Line Power", value: load, unit: "kW", min: 0, max: rated },
        { key: "throughput", label: "Throughput", value: throughput, unit: "units/h", min: 0, max: 160 },
        {
          key: "sec",
          label: "Specific Energy",
          value: throughput > 0 ? roundTo(load / throughput, 2) : null,
          unit: "kWh/unit",
        },
        { key: "motorTemp", label: "Main Motor Temp", value: roundTo(58 + (load / rated) * 22 + jitter(2), 1), unit: "°C", warnAbove: 85 },
        { key: "vibration", label: "Vibration RMS", value: roundTo(1.8 + (load / rated) * 1.4 + jitter(0.25), 2), unit: "mm/s", warnAbove: 4.5 },
        { key: "powerFactor", label: "Power Factor", value: roundTo(0.9 + jitter(0.03), 3), unit: "", warnBelow: 0.85 },
      ];
    }
    case "boiler": {
      const load = consumerLoadKw(assetId, nowMs);
      return [
        { key: "power", label: "Electrical Load", value: load, unit: "kW", min: 0, max: rated },
        { key: "steamPressure", label: "Steam Pressure", value: roundTo(8.4 + jitter(0.35), 2), unit: "bar", min: 0, max: 12, warnAbove: 10.5 },
        { key: "outletTemp", label: "Outlet Temp", value: roundTo(172 + (load / rated) * 18 + jitter(3), 1), unit: "°C", warnAbove: 205 },
        { key: "feedwaterTemp", label: "Feedwater Temp", value: roundTo(78 + jitter(3), 1), unit: "°C" },
        { key: "stackLoss", label: "Stack Loss", value: roundTo(11.4 + jitter(1.1), 1), unit: "%", warnAbove: 15 },
        { key: "efficiency", label: "Thermal Efficiency", value: roundTo(84 - jitter(2.5), 1), unit: "%", warnBelow: 78 },
      ];
    }
    case "compressor": {
      const load = consumerLoadKw(assetId, nowMs);
      return [
        { key: "power", label: "Motor Power", value: load, unit: "kW", min: 0, max: rated },
        { key: "dischargePressure", label: "Discharge Pressure", value: roundTo(6.6 + jitter(0.22), 2), unit: "bar", min: 0, max: 9, warnAbove: 8 },
        { key: "flow", label: "Air Flow", value: roundTo(24 + (load / rated) * 14 + jitter(1.5), 1), unit: "m³/min" },
        { key: "loadFraction", label: "Loaded Fraction", value: roundTo(clamp(52 + jitter(9), 0, 100), 0), unit: "%", warnBelow: 55 },
        { key: "oilTemp", label: "Oil Temp", value: roundTo(74 + jitter(4), 1), unit: "°C", warnAbove: 92 },
        { key: "specificPower", label: "Specific Power", value: roundTo(6.9 + jitter(0.3), 2), unit: "kW/m³/min", warnAbove: 7.6 },
      ];
    }
    case "hvac": {
      const load = consumerLoadKw(assetId, nowMs);
      return [
        { key: "power", label: "Chiller Power", value: load, unit: "kW", min: 0, max: rated },
        { key: "ambient", label: "Ambient Temp", value: temp, unit: "°C" },
        { key: "supplyTemp", label: "Supply Air Temp", value: roundTo(15.5 + jitter(0.8), 1), unit: "°C", warnAbove: 19 },
        { key: "zoneTemp", label: "Zone Temp", value: roundTo(24.2 + jitter(0.7), 1), unit: "°C", warnAbove: 27 },
        { key: "cop", label: "Coefficient of Performance", value: roundTo(3.4 - (temp - 27) * 0.05 + jitter(0.12), 2), unit: "", warnBelow: 2.8 },
        { key: "humidity", label: "Relative Humidity", value: roundTo(56 + jitter(5), 0), unit: "%" },
      ];
    }
    case "solar": {
      const output = solarOutputKw(nowMs);
      const g = irradianceWm2(nowMs);
      return [
        { key: "power", label: "AC Output", value: output, unit: "kW", min: 0, max: rated },
        { key: "irradiance", label: "Irradiance", value: g, unit: "W/m²", min: 0, max: 1000 },
        { key: "panelTemp", label: "Panel Temp", value: roundTo(temp + 0.028 * g, 1), unit: "°C", warnAbove: 68 },
        { key: "inverterEff", label: "Inverter Efficiency", value: g > 50 ? roundTo(96.3 + jitter(0.4), 1) : null, unit: "%" },
        { key: "performanceRatio", label: "Performance Ratio", value: g > 100 ? roundTo(clamp(output / ((g / 1000) * rated), 0, 1) * 100, 1) : null, unit: "%" },
        { key: "stringFaults", label: "String Faults", value: 0, unit: "" },
      ];
    }
    case "battery": {
      return [
        { key: "power", label: "Battery Power", value: energy.batteryKw, unit: "kW", min: -rated, max: rated },
        { key: "soc", label: "State of Charge", value: energy.batterySocPct, unit: "%", min: 0, max: 100, warnBelow: 20 },
        { key: "soh", label: "State of Health", value: 97.4, unit: "%", warnBelow: 85 },
        { key: "cellTemp", label: "Cell Temp", value: roundTo(31 + Math.abs(energy.batteryKw) / rated * 6 + jitter(1), 1), unit: "°C", warnAbove: 45 },
        { key: "cycles", label: "Equivalent Cycles", value: 412, unit: "" },
        { key: "dcVoltage", label: "DC Bus Voltage", value: roundTo(742 + jitter(6), 0), unit: "V" },
      ];
    }
    case "grid":
    default: {
      return [
        { key: "power", label: "Net Import", value: energy.gridKw, unit: "kW", min: -rated, max: rated },
        { key: "voltage", label: "Line Voltage", value: roundTo(415 + jitter(4), 0), unit: "V", warnBelow: 395, warnAbove: 435 },
        { key: "frequency", label: "Frequency", value: roundTo(50 + jitter(0.06), 2), unit: "Hz", warnBelow: 49.5, warnAbove: 50.5 },
        { key: "powerFactor", label: "Power Factor", value: roundTo(0.96 + jitter(0.015), 3), unit: "", warnBelow: 0.9 },
        { key: "thd", label: "Voltage THD", value: roundTo(2.6 + jitter(0.5), 2), unit: "%", warnAbove: 5 },
        { key: "maxDemand", label: "Recorded Max Demand", value: roundTo(886 + jitter(12), 0), unit: "kW" },
      ];
    }
  }
}

function headlineFor(assetId: AssetId, metrics: AssetMetric[]): AssetMetric {
  const key: Record<AssetId, string> = {
    "line-a": "throughput",
    "line-b": "throughput",
    boiler: "steamPressure",
    compressor: "dischargePressure",
    hvac: "zoneTemp",
    solar: "irradiance",
    battery: "soc",
    grid: "voltage",
  };
  return metrics.find((m) => m.key === key[assetId]) ?? metrics[0];
}

function efficiencyFor(assetId: AssetId, metrics: AssetMetric[], nowMs: number): number | null {
  const pick = (k: string) => metrics.find((m) => m.key === k)?.value ?? null;
  switch (assetId) {
    case "boiler":
      return pick("efficiency");
    case "solar":
      return pick("performanceRatio");
    case "hvac": {
      const cop = pick("cop");
      return cop === null ? null : roundTo(clamp((cop / 4.2) * 100, 0, 100), 1);
    }
    case "compressor":
      return pick("loadFraction");
    case "battery":
      return 94;
    case "grid":
      return null; // Efficiency is undefined for a supply point.
    default: {
      const sec = pick("sec");
      if (sec === null) return null;
      const baseline = assetId === "line-a" ? 2.6 : 2.9;
      void nowMs;
      return roundTo(clamp((baseline / sec) * 100, 0, 100), 1);
    }
  }
}

/** Builds the full asset list for a given wall-clock time. */
export function buildAssets(nowMs: number): Asset[] {
  const snapshotAt = quantize(nowMs);
  const energy = currentEnergyState(nowMs);

  return ASSET_IDS.map((id) => {
    const d = ASSET_REGISTRY[id];
    const metrics = metricsFor(id, nowMs);
    const power = metrics.find((m) => m.key === "power")?.value ?? 0;
    const utilisation =
      d.ratedPowerKw > 0 ? roundTo(clamp((Math.abs(power) / d.ratedPowerKw) * 100, 0, 130), 1) : null;
    const status = statusFor(id, utilisation);

    return {
      id,
      name: d.name,
      shortName: d.shortName,
      category: d.category,
      role: d.role,
      description: d.description,
      location: d.location,
      ratedPowerKw: d.ratedPowerKw,
      status,
      powerKw: roundTo(power ?? 0, 1),
      efficiencyPct: efficiencyFor(id, metrics, nowMs),
      utilisationPct: utilisation,
      lastUpdated: new Date(snapshotAt + (hashString(id) % 90) * 1000).toISOString(),
      activeAlerts: status === "warning" ? 1 : status === "critical" ? 2 : 0,
      headline: headlineFor(id, metrics),
      metrics,
      sparkline: sparkline(id, nowMs, snapshotAt),
      origin: "simulated" as const,
    };
  }).map((asset) =>
    asset.id === "grid" ? { ...asset, powerKw: energy.gridKw } : asset,
  );
}

/** Historical sensor trace for one metric of one asset. */
export function buildSensorHistory(
  assetId: AssetId,
  metricKey: string,
  nowMs: number,
  hours = 12,
  stepMinutes = 10,
): SensorReading[] {
  const out: SensorReading[] = [];
  const stepMs = stepMinutes * MINUTE_MS;
  const start = quantize(nowMs - hours * HOUR_MS, stepMs);
  for (let t = start; t <= nowMs; t += stepMs) {
    const metrics = metricsFor(assetId, t);
    const metric = metrics.find((m) => m.key === metricKey);
    if (!metric || metric.value === null) continue;
    out.push({
      assetId,
      metricKey,
      timestamp: new Date(t).toISOString(),
      value: metric.value,
      unit: metric.unit,
      quality: "good",
    });
  }
  return out;
}
