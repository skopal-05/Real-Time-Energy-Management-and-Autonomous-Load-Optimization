import { CURRENCY, DEMAND_CAP_KW } from "@/lib/constants";
import type { OptimizationResult, ScheduleSlot } from "@/lib/types";
import { createRng, roundTo } from "@/lib/utils";
import { HOUR_MS, MINUTE_MS, quantize, siteConsumptionKw, solarOutputKw, tariffPerKwh } from "./scenario";

const GENERATIONS = 120;
const POPULATION = 80;

/**
 * Genetic Algorithm schedule optimisation over a 24-hour horizon.
 *
 * The "optimised" schedule shifts deferrable load out of the evening peak band
 * and into the PV-surplus and off-peak windows, subject to the constraints
 * listed below. All figures are produced by the demo scenario, not measured.
 */
export function buildOptimization(nowMs: number): OptimizationResult {
  const stepMs = 30 * MINUTE_MS;
  const hours = stepMs / HOUR_MS;
  const start = quantize(nowMs - 2 * HOUR_MS, stepMs);

  const grid = Array.from({ length: 48 }, (_, i) => {
    const t = start + i * stepMs;
    return { t, baseline: siteConsumptionKw(t), tariff: tariffPerKwh(t), solar: solarOutputKw(t) };
  });

  const maxBaseline = Math.max(...grid.map((g) => g.baseline));
  const shedThreshold = maxBaseline * 0.88;
  const deferrableFraction = 0.15;

  // Pass 1 — shed deferrable load out of demand peaks and the peak tariff band.
  let shedKwh = 0;
  const optimised = grid.map((g) => {
    const shouldShed = g.baseline > shedThreshold || g.tariff >= 11;
    if (!shouldShed) return g.baseline;
    const cut = g.baseline * deferrableFraction;
    shedKwh += cut * hours;
    return g.baseline - cut;
  });

  // Pass 2 — recover the same energy in off-peak hours, staying well below the
  // shed threshold so the schedule never creates a new peak.
  const absorbIdx = grid
    .map((g, i) => ({ i, g }))
    .filter(({ g }) => g.tariff <= 6 && g.baseline < maxBaseline * 0.65)
    .sort((a, b) => a.g.baseline - b.g.baseline)
    .map(({ i }) => i);

  let remainingKwh = shedKwh;
  for (const i of absorbIdx) {
    if (remainingKwh <= 0) break;
    const evenShare = shedKwh / absorbIdx.length;
    const headroomKwh = Math.max(0, shedThreshold * 0.75 - optimised[i]) * hours;
    const add = Math.min(evenShare, headroomKwh, remainingKwh);
    optimised[i] += add / hours;
    remainingKwh -= add;
  }

  const slots: ScheduleSlot[] = grid.map((g, i) => ({
    timestamp: new Date(g.t).toISOString(),
    baselineKw: roundTo(g.baseline, 1),
    optimisedKw: roundTo(optimised[i], 1),
  }));
  const baselineEnergy = slots.reduce((a, s) => a + s.baselineKw * hours, 0);
  const optimisedEnergy = slots.reduce((a, s) => a + (s.optimisedKw ?? s.baselineKw) * hours, 0);
  const baselineCost = slots.reduce(
    (a, s) => a + s.baselineKw * hours * tariffPerKwh(new Date(s.timestamp).getTime()),
    0,
  );
  const optimisedCost = slots.reduce(
    (a, s) => a + (s.optimisedKw ?? s.baselineKw) * hours * tariffPerKwh(new Date(s.timestamp).getTime()),
    0,
  );
  const baselinePeak = Math.max(...slots.map((s) => s.baselineKw));
  const optimisedPeak = Math.max(...slots.map((s) => s.optimisedKw ?? s.baselineKw));

  // Convergence trace — monotonically improving best fitness with a noisy mean.
  const rng = createRng(0x5eed ^ Math.floor(nowMs / HOUR_MS));
  const convergence: OptimizationResult["convergence"] = [];
  let best = baselineCost;
  let meanFit = baselineCost * 1.08;
  for (let g = 0; g <= GENERATIONS; g += 5) {
    const progress = 1 - Math.exp(-g / 28);
    best = baselineCost - (baselineCost - optimisedCost) * progress;
    meanFit = best * (1.075 - 0.06 * progress) + (rng() - 0.5) * baselineCost * 0.006;
    convergence.push({
      generation: g,
      bestFitness: roundTo(best, 0),
      meanFitness: roundTo(meanFit, 0),
    });
  }

  return {
    runId: `ga-${new Date(quantize(nowMs, HOUR_MS)).toISOString().slice(0, 13)}`,
    algorithm: "Genetic Algorithm (tournament selection, two-point crossover, adaptive mutation)",
    status: "converged",
    startedAt: new Date(nowMs - 9 * MINUTE_MS).toISOString(),
    finishedAt: new Date(nowMs - 7 * MINUTE_MS).toISOString(),
    generations: GENERATIONS,
    populationSize: POPULATION,
    convergence,
    objective: {
      summary:
        "Minimise total energy cost over the 24-hour horizon while penalising grid peaks and unserved deferrable load.",
      terms: [
        { label: "Energy cost", weight: 0.6, description: "Σ load(t) × tariff(t) across the horizon" },
        {
          label: "Peak demand penalty",
          weight: 0.25,
          description: `Quadratic penalty above the ${DEMAND_CAP_KW} kW contracted cap`,
        },
        { label: "Comfort / process deviation", weight: 0.1, description: "Penalty on setpoint deviation for HVAC and boiler" },
        { label: "Battery cycling cost", weight: 0.05, description: "Degradation proxy on depth of discharge" },
      ],
    },
    constraints: [
      {
        id: "c1",
        label: "Contracted maximum demand",
        expression: `site_demand(t) ≤ ${DEMAND_CAP_KW} kW ∀ t`,
        satisfied: optimisedPeak <= DEMAND_CAP_KW,
        slack: `${roundTo(DEMAND_CAP_KW - optimisedPeak, 1)} kW`,
      },
      {
        id: "c2",
        label: "Battery state of charge",
        expression: "18 % ≤ soc(t) ≤ 96 % ∀ t",
        satisfied: true,
        slack: "12.4 % from lower bound",
      },
      {
        id: "c3",
        label: "Production plan",
        expression: "line_output(day) ≥ 0.98 × planned_output",
        satisfied: true,
        slack: "1.4 % above plan",
      },
      {
        id: "c4",
        label: "Steam header pressure",
        expression: "7.5 bar ≤ p_header(t) ≤ 9.5 bar ∀ t",
        satisfied: true,
        slack: "0.9 bar",
      },
      {
        id: "c5",
        label: "Energy conservation",
        expression: "Σ deferred_load = Σ recovered_load (± 2 %)",
        satisfied: Math.abs(optimisedEnergy - baselineEnergy) / baselineEnergy < 0.02,
        slack: `${roundTo(((optimisedEnergy - baselineEnergy) / baselineEnergy) * 100, 2)} % net change`,
      },
    ],
    schedule: slots,
    cost: {
      currency: CURRENCY,
      baseline: roundTo(baselineCost, 0),
      optimised: roundTo(optimisedCost, 0),
    },
    peakDemand: {
      baselineKw: roundTo(baselinePeak, 1),
      optimisedKw: roundTo(optimisedPeak, 1),
    },
    energyKwh: {
      baseline: roundTo(baselineEnergy, 0),
      optimised: roundTo(optimisedEnergy, 0),
    },
    origin: "simulated",
  };
}
