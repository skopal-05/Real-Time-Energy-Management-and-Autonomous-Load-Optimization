"""Tests for carbon evaluation and multi-objective ranking."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parent.parent
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from contracts import Scenario
from ranking import ScenarioEvaluator, ScenarioRanker
from simulation import CarbonSimulator


def scenario(identifier: str, load: float, renewable: float, fuel: float) -> Scenario:
    return Scenario(
        scenario_id=identifier,
        name=identifier,
        description="test",
        horizon_hours=1,
        operating_point={
            "production_load_kw": load,
            "compressor_power_kw": 0,
            "hvac_power_kw": 0,
            "renewable_generation_kw": renewable,
            "battery_charge_kw": 0,
            "battery_discharge_kw": 0,
            "grid_export_limit_kw": 0,
            "boiler_fuel_m3_hr": fuel,
        },
    )


class CarbonSimulatorTests(unittest.TestCase):
    def test_calculates_grid_and_fuel_emissions(self) -> None:
        result = CarbonSimulator(
            grid_factor_kg_kwh=0.5, natural_gas_factor_kg_m3=2
        ).simulate({"grid_import_kwh": 10, "boiler_fuel_m3": 3})
        self.assertEqual(result["grid_emissions_kg_co2e"], 5)
        self.assertEqual(result["fuel_emissions_kg_co2e"], 6)
        self.assertEqual(result["total_emissions_kg_co2e"], 11)


class EvaluationAndRankingTests(unittest.TestCase):
    def test_evaluator_adds_baseline_savings(self) -> None:
        results = ScenarioEvaluator().evaluate(
            [scenario("baseline", 100, 0, 10), scenario("efficient", 80, 0, 8)]
        )
        efficient = results[1]
        self.assertEqual(efficient.energy["energy_saving_kwh"], 20)
        self.assertGreater(efficient.cost["cost_saving_inr"], 0)
        self.assertGreater(efficient.carbon["emissions_avoided_kg_co2e"], 0)

    def test_ranker_selects_lower_impact_scenario(self) -> None:
        evaluated = ScenarioEvaluator().evaluate(
            [scenario("baseline", 100, 0, 10), scenario("efficient", 80, 0, 8)]
        )
        ranked = ScenarioRanker().rank(evaluated)
        self.assertEqual(ranked[0].scenario.scenario_id, "efficient")
        self.assertEqual([item.rank for item in ranked], [1, 2])
        self.assertGreater(ranked[0].score, ranked[1].score)

    def test_custom_weights_are_normalized(self) -> None:
        ranker = ScenarioRanker({"energy": 2, "cost": 1, "carbon": 1})
        self.assertEqual(ranker.weights["energy"], 0.5)


if __name__ == "__main__":
    unittest.main()
