import { DEMAND_CAP_KW } from "@/lib/constants";
import type { Agent, AIRecommendation, OperatingObjective } from "@/lib/types";
import { roundTo } from "@/lib/utils";
import { MINUTE_MS, currentEnergyState, isPeakTariff, siteConsumptionKw, solarOutputKw } from "./scenario";

export function buildObjective(nowMs: number): OperatingObjective {
  const peak = isPeakTariff(nowMs);
  return peak
    ? {
        mode: "peak-shaving",
        label: "Peak Shaving",
        description:
          "During the evening peak tariff window the agents prioritise keeping grid demand below the contracted maximum, using battery discharge and deferrable load first.",
        constraints: [
          `Site demand ≤ ${DEMAND_CAP_KW} kW (contracted maximum demand)`,
          "Battery state of charge ≥ 18 %",
          "Production Line A output not reduced below 85 % of plan",
        ],
        since: new Date(nowMs - 42 * MINUTE_MS).toISOString(),
      }
    : {
        mode: "cost-optimal",
        label: "Cost Optimal",
        description:
          "Outside the peak window the agents minimise energy cost across the tariff schedule, charging storage from surplus PV and shifting flexible thermal load into low-price bands.",
        constraints: [
          `Site demand ≤ ${DEMAND_CAP_KW} kW (contracted maximum demand)`,
          "Battery state of charge between 18 % and 96 %",
          "Steam header pressure held between 7.5 and 9.5 bar",
        ],
        since: new Date(nowMs - 3 * 60 * MINUTE_MS).toISOString(),
      };
}

export function buildAgents(nowMs: number): Agent[] {
  return [
    {
      id: "demand-agent",
      name: "Demand Agent",
      scope: "Watches site demand against the contracted maximum and the forecast peak.",
      state: "active",
      ruleCount: 9,
      decisionsToday: 14,
      lastActionAt: new Date(nowMs - 6 * MINUTE_MS).toISOString(),
      watches: ["line-a", "line-b", "grid"],
    },
    {
      id: "generation-agent",
      name: "Generation Agent",
      scope: "Tracks PV output against irradiance and flags under-performance or curtailment.",
      state: "active",
      ruleCount: 6,
      decisionsToday: 5,
      lastActionAt: new Date(nowMs - 31 * MINUTE_MS).toISOString(),
      watches: ["solar", "grid"],
    },
    {
      id: "storage-agent",
      name: "Storage Agent",
      scope: "Schedules battery charge and discharge against tariff bands and PV surplus.",
      state: "active",
      ruleCount: 11,
      decisionsToday: 22,
      lastActionAt: new Date(nowMs - 2 * MINUTE_MS).toISOString(),
      watches: ["battery", "solar", "grid"],
    },
    {
      id: "thermal-agent",
      name: "Thermal Agent",
      scope: "Coordinates boiler and HVAC setpoints within comfort and process limits.",
      state: "active",
      ruleCount: 8,
      decisionsToday: 9,
      lastActionAt: new Date(nowMs - 18 * MINUTE_MS).toISOString(),
      watches: ["boiler", "hvac"],
    },
    {
      id: "cost-agent",
      name: "Cost Agent",
      scope: "Prices every candidate action against the tariff schedule before it is proposed.",
      state: "active",
      ruleCount: 5,
      decisionsToday: 31,
      lastActionAt: new Date(nowMs - 9 * MINUTE_MS).toISOString(),
      watches: ["grid", "battery"],
    },
    {
      id: "safety-agent",
      name: "Safety & Constraint Agent",
      scope: "Holds veto rights — rejects any proposal that violates a hard operating constraint.",
      state: "active",
      ruleCount: 13,
      decisionsToday: 3,
      lastActionAt: new Date(nowMs - 77 * MINUTE_MS).toISOString(),
      watches: ["boiler", "compressor", "battery", "grid"],
    },
  ];
}

/**
 * Recommendations are derived from the same scenario state the rest of the UI
 * shows, so a viewer can trace a decision back to the numbers that triggered it.
 */
export function buildRecommendations(nowMs: number): AIRecommendation[] {
  const state = currentEnergyState(nowMs);
  const peak = isPeakTariff(nowMs);
  const solar = solarOutputKw(nowMs);
  const demand = siteConsumptionKw(nowMs);
  const headroom = roundTo(DEMAND_CAP_KW - demand, 1);

  // The storage agent's live proposal follows the actual battery state, so the
  // decision layer visibly reacts as the scenario advances.
  const reserveReached = state.batterySocPct <= 22;
  const storageDecision: AIRecommendation = (() => {
    const base = {
      id: "dec-1041",
      agentId: "storage-agent" as const,
      agentName: "Storage Agent",
      targetAssets: ["battery", "grid"] as AIRecommendation["targetAssets"],
      status: "applied" as const,
      createdAt: new Date(nowMs - 4 * MINUTE_MS).toISOString(),
      sourceModule: "rules" as const,
      origin: "simulated" as const,
    };

    if (peak && reserveReached) {
      return {
        ...base,
        title: "Hold battery at its reserve floor — cover the remaining peak from the grid",
        ruleTriggered: "IF tariff_band = 'peak' AND soc ≤ 22 % THEN block(discharge) AND serve_from(grid)",
        rationale: `State of charge is down to ${state.batterySocPct} % after supporting the earlier part of the peak window. Discharging further would take the pack below its reserve floor, so the agent stops dispatch and lets the remaining ${roundTo(demand, 0)} kW of demand come from the grid. Recharging resumes once the tariff drops.`,
        priority: "medium" as const,
        expectedImpact: [
          { label: "Reserve protected", value: 18, unit: "% SoC" },
          { label: "Cycle depth avoided", value: null, unit: "%" },
        ],
      };
    }

    if (peak) {
      return {
        ...base,
        title: "Discharge battery to hold site demand under the contracted cap",
        ruleTriggered:
          "IF tariff_band = 'peak' AND site_demand > 0.85 × demand_cap AND soc > 22 % THEN discharge(battery)",
        rationale: `Site demand is ${roundTo(demand, 0)} kW against a ${DEMAND_CAP_KW} kW contracted cap, leaving ${headroom} kW of headroom inside the peak tariff band. Discharging storage covers the gap without touching production.`,
        priority: "high" as const,
        expectedImpact: [
          { label: "Peak import avoided", value: roundTo(Math.max(state.batteryKw, 40), 0), unit: "kW" },
          { label: "Tariff differential", value: 5.8, unit: "₹/kWh" },
        ],
      };
    }

    return {
      ...base,
      title: "Charge battery from surplus PV before the evening peak",
      ruleTriggered: "IF pv_surplus > 20 kW AND soc < 90 % AND tariff_band ≠ 'peak' THEN charge(battery)",
      rationale: `PV output is ${roundTo(solar, 0)} kW against ${roundTo(demand, 0)} kW of demand and the battery is at ${state.batterySocPct} %. Storing surplus now avoids importing at the 17:30 peak rate later.`,
      priority: "medium" as const,
      expectedImpact: [
        { label: "Energy stored", value: roundTo(Math.max(-state.batteryKw, 0), 0), unit: "kW" },
        { label: "Tariff differential", value: 5.8, unit: "₹/kWh" },
      ],
    };
  })();

  const items: AIRecommendation[] = [
    storageDecision,
    {
      id: "dec-1040",
      agentId: "thermal-agent",
      agentName: "Thermal Agent",
      title: "Raise HVAC supply-air setpoint by 1.0 °C for 45 minutes",
      ruleTriggered:
        "IF forecast_peak_within(60 min) AND zone_temp < setpoint + 1.5 °C THEN relax(hvac_setpoint, 1.0 °C)",
      rationale:
        "The Random Forest forecast places the site peak inside the next hour. Zone temperature is currently below its comfort ceiling, so a short setpoint relaxation trims chiller load during the peak without breaching the comfort band.",
      targetAssets: ["hvac"],
      priority: "medium",
      status: "pending",
      createdAt: new Date(nowMs - 11 * MINUTE_MS).toISOString(),
      expectedImpact: [
        { label: "Load reduction", value: 26, unit: "kW" },
        { label: "Duration", value: 45, unit: "min" },
      ],
      sourceModule: "forecast",
      origin: "simulated",
    },
    {
      id: "dec-1039",
      agentId: "demand-agent",
      agentName: "Demand Agent",
      title: "Defer Line B changeover batch by 20 minutes",
      ruleTriggered:
        "IF forecast_demand > demand_cap × 0.95 AND batch_is_deferrable THEN propose_defer(batch, ≤ 30 min)",
      rationale:
        "Starting the changeover batch on schedule would coincide with the forecast site peak. Deferring it by 20 minutes moves the start into a lower-demand window; the shift plan has enough slack to absorb the delay.",
      targetAssets: ["line-b"],
      priority: "medium",
      status: "pending",
      createdAt: new Date(nowMs - 23 * MINUTE_MS).toISOString(),
      expectedImpact: [
        { label: "Peak contribution avoided", value: 48, unit: "kW" },
        { label: "Schedule slack used", value: 20, unit: "min" },
      ],
      sourceModule: "optimizer",
      origin: "simulated",
    },
    {
      id: "dec-1038",
      agentId: "safety-agent",
      agentName: "Safety & Constraint Agent",
      title: "Reject compressor unload proposal — discharge pressure margin too low",
      ruleTriggered: "IF proposed_action reduces header_pressure below 6.2 bar THEN veto(action)",
      rationale:
        "The Cost Agent proposed unloading the compressor during the peak window. Header pressure is already close to its lower process limit, so the Safety Agent vetoed the action. Hard constraints always override cost objectives.",
      targetAssets: ["compressor"],
      priority: "high",
      status: "rejected",
      createdAt: new Date(nowMs - 38 * MINUTE_MS).toISOString(),
      expectedImpact: [{ label: "Constraint protected", value: 6.2, unit: "bar min" }],
      sourceModule: "rules",
      origin: "simulated",
    },
    {
      id: "dec-1037",
      agentId: "generation-agent",
      agentName: "Generation Agent",
      title: "Flag south-array performance ratio below expectation",
      ruleTriggered: "IF performance_ratio < 0.86 FOR 30 min AND irradiance > 400 W/m² THEN raise(inspection)",
      rationale:
        "Measured AC output is tracking below the irradiance-derived expectation for the south string. Soiling is the most common cause at this time of year; an inspection request has been queued rather than an automatic control action.",
      targetAssets: ["solar"],
      priority: "low",
      status: "accepted",
      createdAt: new Date(nowMs - 64 * MINUTE_MS).toISOString(),
      expectedImpact: [{ label: "Recoverable yield", value: null, unit: "kWh/day" }],
      sourceModule: "anomaly",
      origin: "simulated",
    },
    {
      id: "dec-1036",
      agentId: "cost-agent",
      agentName: "Cost Agent",
      title: "Shift boiler pre-heat into the off-peak band",
      ruleTriggered: "IF tariff_band(t+Δ) < tariff_band(t) AND thermal_storage_available THEN shift(preheat, Δ)",
      rationale:
        "Pre-heat can be brought forward into the 05:00–06:00 off-peak band without affecting the steam schedule, because the header holds enough thermal mass to bridge the gap.",
      targetAssets: ["boiler"],
      priority: "low",
      status: "applied",
      createdAt: new Date(nowMs - 3 * 60 * MINUTE_MS).toISOString(),
      expectedImpact: [
        { label: "Energy shifted", value: 140, unit: "kWh" },
        { label: "Tariff differential", value: 2.3, unit: "₹/kWh" },
      ],
      sourceModule: "optimizer",
      origin: "simulated",
    },
  ];

  return items;
}
