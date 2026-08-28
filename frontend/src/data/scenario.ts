import { ASSET_REGISTRY, CONSUMER_ASSET_IDS } from "@/lib/constants";
import type { AssetId, EnergyReading } from "@/lib/types";
import { clamp, createRng, hashString, roundTo } from "@/lib/utils";

/**
 * Physical scenario model behind the demo data set.
 *
 * This is a deterministic simulation of a two-line manufacturing site with
 * rooftop PV, a battery and a grid connection. It exists so the UI can be
 * exercised end-to-end before the Python backend is connected. It is NOT a
 * measurement source — everything it produces is tagged `origin: "simulated"`.
 */

export const STEP_MS = 5 * 60 * 1000;
export const MINUTE_MS = 60 * 1000;
export const HOUR_MS = 60 * MINUTE_MS;
export const DAY_MS = 24 * HOUR_MS;

/** Snaps a timestamp onto the 5-minute simulation grid. */
export function quantize(ms: number, stepMs: number = STEP_MS): number {
  return Math.floor(ms / stepMs) * stepMs;
}

/** Fractional hour-of-day (local time) for a timestamp. */
export function hourOfDay(ms: number): number {
  const d = new Date(ms);
  return d.getHours() + d.getMinutes() / 60;
}

function dayIndex(ms: number): number {
  return Math.floor(ms / DAY_MS);
}

/** Repeatable bounded noise, stable for a given asset + timestamp. */
function noise(key: string, ms: number, amplitude: number): number {
  const rng = createRng(hashString(key) ^ Math.floor(ms / MINUTE_MS));
  return (rng() - 0.5) * 2 * amplitude;
}

/** Smooth 0→1 ramp used for shift start/stop transitions. */
function ramp(x: number, start: number, end: number): number {
  if (x <= start) return 0;
  if (x >= end) return 1;
  const t = (x - start) / (end - start);
  return t * t * (3 - 2 * t);
}

function window(h: number, start: number, end: number, edge = 0.6): number {
  return ramp(h, start, start + edge) * (1 - ramp(h, end - edge, end));
}

/** Ambient temperature in °C — drives the HVAC and PV derating models. */
export function ambientTempC(ms: number): number {
  const h = hourOfDay(ms);
  const seasonal = 2.5 * Math.sin((dayIndex(ms) / 60) * Math.PI * 2);
  return roundTo(27.5 + seasonal + 6.2 * Math.sin(((h - 9.5) / 24) * Math.PI * 2), 1);
}

/** Plane-of-array irradiance in W/m² — clear-sky curve with cloud noise. */
export function irradianceWm2(ms: number): number {
  const h = hourOfDay(ms);
  if (h < 6 || h > 18.6) return 0;
  const clear = Math.sin(((h - 6) / 12.6) * Math.PI) ** 1.15;
  const cloud = 1 - clamp(0.32 * (0.5 + noise(`cloud-${dayIndex(ms)}`, ms, 0.5)), 0, 0.55);
  return roundTo(Math.max(0, 1000 * clear * cloud), 0);
}

/* ------------------------------------------------------------------ */
/* Per-asset load models                                               */
/* ------------------------------------------------------------------ */

/** Instantaneous electrical power for a consuming asset, in kW. */
export function consumerLoadKw(assetId: AssetId, ms: number): number {
  const rated = ASSET_REGISTRY[assetId].ratedPowerKw;
  const h = hourOfDay(ms);
  const weekend = new Date(ms).getDay() === 0;

  switch (assetId) {
    case "line-a": {
      const shift = window(h, 6, 22, 1.2);
      const lunchDip = 1 - 0.28 * window(h, 12.5, 13.5, 0.3);
      const base = 0.14 + 0.74 * shift * lunchDip * (weekend ? 0.25 : 1);
      return roundTo(rated * clamp(base + noise(assetId, ms, 0.035), 0.05, 1), 1);
    }
    case "line-b": {
      const shiftA = window(h, 7, 15.5, 1);
      const shiftB = window(h, 16.5, 23, 1);
      const base = 0.12 + 0.7 * Math.max(shiftA, shiftB * 0.85) * (weekend ? 0.2 : 1);
      return roundTo(rated * clamp(base + noise(assetId, ms, 0.04), 0.05, 1), 1);
    }
    case "boiler": {
      // Load/unload cycling on roughly a 40-minute period.
      const duty = 0.5 + 0.5 * Math.sin((ms / (40 * MINUTE_MS)) * Math.PI * 2);
      const demand = 0.28 + 0.5 * window(h, 5.5, 21, 1.5) * (weekend ? 0.4 : 1);
      return roundTo(rated * clamp(demand * (0.72 + 0.35 * duty) + noise(assetId, ms, 0.03), 0.06, 1), 1);
    }
    case "compressor": {
      const duty = 0.5 + 0.5 * Math.sin((ms / (11 * MINUTE_MS)) * Math.PI * 2 + 1.1);
      const demand = 0.22 + 0.62 * window(h, 6.2, 22.2, 1.2) * (weekend ? 0.3 : 1);
      return roundTo(rated * clamp(demand * (0.68 + 0.42 * duty) + noise(assetId, ms, 0.045), 0.05, 1), 1);
    }
    case "hvac": {
      const t = ambientTempC(ms);
      const occupancy = 0.35 + 0.65 * window(h, 6, 23, 1.5);
      const thermal = clamp(0.3 + 0.062 * (t - 24), 0.18, 1);
      return roundTo(rated * clamp(occupancy * thermal + noise(assetId, ms, 0.03), 0.06, 1), 1);
    }
    default:
      return 0;
  }
}

/** Rooftop PV output in kW, including temperature derating. */
export function solarOutputKw(ms: number): number {
  const rated = ASSET_REGISTRY.solar.ratedPowerKw;
  const g = irradianceWm2(ms);
  if (g <= 0) return 0;
  const cellTemp = ambientTempC(ms) + 0.028 * g;
  const derate = clamp(1 - 0.0037 * (cellTemp - 25), 0.72, 1);
  const inverter = 0.965;
  return roundTo(clamp((g / 1000) * rated * derate * inverter, 0, rated), 1);
}

export function siteConsumptionKw(ms: number): number {
  return roundTo(
    CONSUMER_ASSET_IDS.reduce((acc, id) => acc + consumerLoadKw(id, ms), 0),
    1,
  );
}

/* ------------------------------------------------------------------ */
/* Battery dispatch + site balance                                     */
/* ------------------------------------------------------------------ */

const BATTERY_CAPACITY_KWH = 600;
const BATTERY_MAX_KW = ASSET_REGISTRY.battery.ratedPowerKw;
const BATTERY_MIN_SOC = 18;
const BATTERY_MAX_SOC = 96;

/** Evening peak-tariff window in which the battery is allowed to discharge. */
export function isPeakTariff(ms: number): boolean {
  const h = hourOfDay(ms);
  return h >= 17.5 && h < 22;
}

/**
 * Integrates the site energy balance over a time range.
 * Battery state of charge is path-dependent, so the series is produced by
 * stepping forward rather than sampling pointwise.
 */
export function generateEnergySeries(
  startMs: number,
  endMs: number,
  stepMinutes = 5,
  initialSocPct = 62,
): EnergyReading[] {
  const stepMs = stepMinutes * MINUTE_MS;
  const hours = stepMinutes / 60;
  let soc = initialSocPct;
  const out: EnergyReading[] = [];

  for (let t = quantize(startMs, stepMs); t <= endMs; t += stepMs) {
    const consumption = siteConsumptionKw(t);
    const solar = solarOutputKw(t);
    const surplus = solar - consumption;

    let battery = 0; // + discharging to site, − charging
    if (surplus > 5 && soc < BATTERY_MAX_SOC) {
      battery = -Math.min(surplus, BATTERY_MAX_KW);
    } else if (isPeakTariff(t) && soc > BATTERY_MIN_SOC) {
      battery = Math.min(BATTERY_MAX_KW * 0.8, Math.max(0, consumption - solar) * 0.45);
    }

    // Charge/discharge with 94 % round-trip efficiency.
    const deltaKwh = -battery * hours * (battery < 0 ? 0.97 : 1 / 0.97);
    soc = clamp(soc + (deltaKwh / BATTERY_CAPACITY_KWH) * 100, BATTERY_MIN_SOC - 2, BATTERY_MAX_SOC + 1);

    const grid = roundTo(consumption - solar - battery, 1);

    out.push({
      timestamp: new Date(t).toISOString(),
      consumptionKw: consumption,
      generationKw: solar,
      solarKw: solar,
      batteryKw: roundTo(battery, 1),
      gridKw: grid,
      batterySocPct: roundTo(soc, 1),
    });
  }
  return out;
}

/** The current instantaneous site snapshot, integrated over the last 12 h. */
export function currentEnergyState(nowMs: number): EnergyReading {
  const series = generateEnergySeries(nowMs - 12 * HOUR_MS, nowMs, 5);
  return series[series.length - 1];
}

/** Battery power/SOC alone, for the battery twin. */
export function batteryState(nowMs: number): { powerKw: number; socPct: number } {
  const s = currentEnergyState(nowMs);
  return { powerKw: s.batteryKw, socPct: s.batterySocPct };
}

/** Power for any asset, consumers and non-consumers alike (kW, signed). */
export function assetPowerKw(assetId: AssetId, ms: number): number {
  if (CONSUMER_ASSET_IDS.includes(assetId)) return consumerLoadKw(assetId, ms);
  const state = currentEnergyState(ms);
  if (assetId === "solar") return -state.solarKw;
  if (assetId === "battery") return -state.batteryKw;
  return -state.gridKw;
}

/** Tariff in ₹/kWh — a simple three-band industrial schedule. */
export function tariffPerKwh(ms: number): number {
  const h = hourOfDay(ms);
  if (h >= 17.5 && h < 22) return 11.4; // peak
  if (h >= 6 && h < 17.5) return 7.9; // normal
  return 5.6; // off-peak
}
