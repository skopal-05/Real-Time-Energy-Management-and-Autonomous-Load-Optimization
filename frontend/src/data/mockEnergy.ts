import { ASSET_REGISTRY, CHART_COLORS, CONSUMER_ASSET_IDS } from "@/lib/constants";
import type {
  EnergyFlowLink,
  EnergyFlowNode,
  EnergyFlowSnapshot,
  EnergyReading,
  EnergySourceShare,
} from "@/lib/types";
import { roundTo } from "@/lib/utils";
import { HOUR_MS, consumerLoadKw, currentEnergyState, generateEnergySeries } from "./scenario";
import { buildAssets } from "./mockAssets";

/** Rolling window of the site energy balance ending at `nowMs`. */
export function buildEnergyWindow(nowMs: number, hours = 12, stepMinutes = 5): EnergyReading[] {
  return generateEnergySeries(nowMs - hours * HOUR_MS, nowMs, stepMinutes);
}

/** Energy delivered by each source over the trailing window, in kWh. */
export function buildSourceShares(nowMs: number, hours = 24): EnergySourceShare[] {
  const series = generateEnergySeries(nowMs - hours * HOUR_MS, nowMs, 15);
  const h = 0.25;
  let solar = 0;
  let battery = 0;
  let grid = 0;

  for (const p of series) {
    const solarToLoad = Math.min(p.solarKw, p.consumptionKw);
    solar += solarToLoad * h;
    if (p.batteryKw > 0) battery += p.batteryKw * h;
    if (p.gridKw > 0) grid += p.gridKw * h;
  }

  const total = solar + battery + grid || 1;
  return [
    { source: "Solar", energyKwh: roundTo(solar, 0), sharePct: roundTo((solar / total) * 100, 1), colorToken: CHART_COLORS.solar },
    { source: "Battery", energyKwh: roundTo(battery, 0), sharePct: roundTo((battery / total) * 100, 1), colorToken: CHART_COLORS.battery },
    { source: "Grid", energyKwh: roundTo(grid, 0), sharePct: roundTo((grid / total) * 100, 1), colorToken: CHART_COLORS.grid },
  ];
}

/** Share of demand met by on-site renewables right now, 0–100. */
export function renewableSharePct(reading: EnergyReading): number {
  if (reading.consumptionKw <= 0) return 0;
  const renewable = Math.min(reading.solarKw, reading.consumptionKw);
  return roundTo((renewable / reading.consumptionKw) * 100, 1);
}

/**
 * Node/link graph for the energy-flow map.
 * Powers are signed at the source: every link carries a positive magnitude and
 * the direction is expressed by the from → to pair.
 */
export function buildEnergyFlow(nowMs: number): EnergyFlowSnapshot {
  const state = currentEnergyState(nowMs);
  const assets = buildAssets(nowMs);
  const statusOf = (id: string) => assets.find((a) => a.id === id)?.status ?? "healthy";

  const solarToLoad = roundTo(Math.min(state.solarKw, state.consumptionKw), 1);
  const solarToBattery = roundTo(state.batteryKw < 0 ? Math.min(-state.batteryKw, Math.max(state.solarKw - solarToLoad, 0)) : 0, 1);
  const solarToGrid = roundTo(Math.max(state.solarKw - solarToLoad - solarToBattery, 0), 1);
  const batteryToBus = roundTo(Math.max(state.batteryKw, 0), 1);
  const gridToBus = roundTo(Math.max(state.gridKw, 0), 1);
  const busToGrid = roundTo(Math.max(-state.gridKw, 0), 1);

  const nodes: EnergyFlowNode[] = [
    {
      id: "solar",
      label: "Solar PV",
      kind: "source",
      powerKw: state.solarKw,
      status: statusOf("solar"),
      assetId: "solar",
      detail: `${roundTo(state.solarKw, 0)} kW generating`,
    },
    {
      id: "grid",
      label: "Grid",
      kind: "source",
      powerKw: state.gridKw,
      status: statusOf("grid"),
      assetId: "grid",
      detail: state.gridKw >= 0 ? "Importing" : "Exporting",
    },
    {
      id: "battery",
      label: "Battery",
      kind: "storage",
      powerKw: state.batteryKw,
      status: statusOf("battery"),
      assetId: "battery",
      detail:
        state.batteryKw > 1
          ? `Discharging · ${state.batterySocPct}% SoC`
          : state.batteryKw < -1
            ? `Charging · ${state.batterySocPct}% SoC`
            : `Idle · ${state.batterySocPct}% SoC`,
    },
    {
      id: "bus",
      label: "Main Distribution Bus",
      kind: "hub",
      powerKw: state.consumptionKw,
      status: "healthy",
      detail: "415 V · 50 Hz",
    },
    ...CONSUMER_ASSET_IDS.map<EnergyFlowNode>((id) => ({
      id,
      label: ASSET_REGISTRY[id].shortName,
      kind: "sink",
      powerKw: consumerLoadKw(id, nowMs),
      status: statusOf(id),
      assetId: id,
      detail: ASSET_REGISTRY[id].category,
    })),
  ];

  const links: EnergyFlowLink[] = [
    { from: "solar", to: "bus", powerKw: solarToLoad, colorToken: CHART_COLORS.solar, active: solarToLoad > 1 },
    { from: "solar", to: "battery", powerKw: solarToBattery, colorToken: CHART_COLORS.solar, active: solarToBattery > 1 },
    { from: "solar", to: "grid", powerKw: solarToGrid, colorToken: CHART_COLORS.solar, active: solarToGrid > 1 },
    { from: "battery", to: "bus", powerKw: batteryToBus, colorToken: CHART_COLORS.battery, active: batteryToBus > 1 },
    { from: "grid", to: "bus", powerKw: gridToBus, colorToken: CHART_COLORS.grid, active: gridToBus > 1 },
    { from: "bus", to: "grid", powerKw: busToGrid, colorToken: CHART_COLORS.generation, active: busToGrid > 1 },
    ...CONSUMER_ASSET_IDS.map<EnergyFlowLink>((id) => ({
      from: "bus",
      to: id,
      powerKw: consumerLoadKw(id, nowMs),
      colorToken: CHART_COLORS.load,
      active: consumerLoadKw(id, nowMs) > 1,
    })),
  ];

  return {
    timestamp: new Date(nowMs).toISOString(),
    nodes,
    links,
    origin: "simulated",
  };
}
