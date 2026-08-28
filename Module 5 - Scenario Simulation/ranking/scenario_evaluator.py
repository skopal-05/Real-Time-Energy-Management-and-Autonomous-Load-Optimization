"""Evaluate scenarios with common energy, cost, and carbon models."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from contracts import Scenario, ScenarioResult
from simulation import CarbonSimulator, CostSimulator, EnergySimulator


class ScenarioEvaluator:
    """Run comparable simulations and add savings relative to baseline."""

    def __init__(
        self,
        energy_simulator: EnergySimulator | None = None,
        cost_simulator: CostSimulator | None = None,
        carbon_simulator: CarbonSimulator | None = None,
    ) -> None:
        self.energy_simulator = energy_simulator or EnergySimulator()
        self.cost_simulator = cost_simulator or CostSimulator()
        self.carbon_simulator = carbon_simulator or CarbonSimulator()

    def evaluate(self, scenarios: Iterable[Scenario]) -> list[ScenarioResult]:
        items = list(scenarios)
        if not items:
            raise ValueError("at least one scenario is required")
        evaluated: list[ScenarioResult] = []
        for scenario in items:
            energy = self.energy_simulator.simulate(scenario)
            cost = self.cost_simulator.simulate(energy)
            carbon = self.carbon_simulator.simulate(energy)
            evaluated.append(ScenarioResult(scenario, energy, cost, carbon))

        baseline = next(
            (item for item in evaluated if item.scenario.scenario_id == "baseline"),
            evaluated[0],
        )
        enriched: list[ScenarioResult] = []
        for item in evaluated:
            energy = dict(item.energy)
            cost = dict(item.cost)
            carbon = dict(item.carbon)
            energy["energy_saving_kwh"] = round(
                baseline.energy["useful_electrical_load_kwh"]
                - energy["useful_electrical_load_kwh"],
                3,
            )
            cost["cost_saving_inr"] = round(
                baseline.cost["net_operating_cost_inr"] - cost["net_operating_cost_inr"], 2
            )
            carbon["emissions_avoided_kg_co2e"] = round(
                baseline.carbon["total_emissions_kg_co2e"]
                - carbon["total_emissions_kg_co2e"],
                3,
            )
            enriched.append(replace(item, energy=energy, cost=cost, carbon=carbon))
        return enriched
