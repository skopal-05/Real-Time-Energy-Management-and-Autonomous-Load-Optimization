"""Tests for scenario generation and energy/cost simulation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parent.parent
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from scenario_generator import ScenarioGenerator, ScenarioValidator
from simulation import CostSimulator, EnergySimulator


FORECAST = {
    "future_state": {"compressor_power_kw": 20, "hvac_power_kw": 10},
    "energy_forecast": {
        "total_load_kw": 70,
        "renewable_generation_kw": 80,
        "boiler_fuel_flow_m3_hr": 50,
    },
}
RECOMMENDATIONS = [
    {
        "agent": "compressor_agent",
        "action": "optimize",
        "priority": "medium",
        "setpoints": {"compressor_power_target_kw": 15},
    },
    {
        "agent": "boiler_agent",
        "action": "optimize",
        "priority": "high",
        "setpoints": {"boiler_fuel_target_m3_hr": 40},
    },
]


class ScenarioGeneratorTests(unittest.TestCase):
    def test_generates_all_templates_with_unique_ids(self) -> None:
        scenarios = ScenarioGenerator().generate(FORECAST, RECOMMENDATIONS)
        self.assertGreaterEqual(len(scenarios), 4)
        self.assertEqual(len(scenarios), len({item.scenario_id for item in scenarios}))
        self.assertEqual(scenarios[0].scenario_id, "baseline")

    def test_applies_agent_equipment_targets(self) -> None:
        scenarios = ScenarioGenerator().generate(FORECAST, RECOMMENDATIONS)
        optimized = next(item for item in scenarios if item.scenario_id == "agent_optimized")
        self.assertEqual(optimized.operating_point["compressor_power_kw"], 15)
        self.assertEqual(optimized.operating_point["boiler_fuel_m3_hr"], 40)

    def test_rejects_invalid_forecast(self) -> None:
        with self.assertRaises(ValueError):
            ScenarioGenerator().generate({}, RECOMMENDATIONS)

    def test_validator_rejects_simultaneous_charge_and_discharge(self) -> None:
        scenario = ScenarioGenerator().generate(FORECAST, RECOMMENDATIONS)[0]
        scenario.operating_point["battery_charge_kw"] = 1
        scenario.operating_point["battery_discharge_kw"] = 1
        self.assertTrue(ScenarioValidator().validate(scenario))


class SimulationTests(unittest.TestCase):
    def test_energy_balance_uses_grid_for_deficit(self) -> None:
        scenario = ScenarioGenerator().generate(FORECAST, RECOMMENDATIONS)[0]
        metrics = EnergySimulator().simulate(scenario)
        self.assertEqual(metrics["site_consumption_kwh"], 100)
        self.assertEqual(metrics["grid_import_kwh"], 20)
        self.assertEqual(metrics["grid_export_kwh"], 0)

    def test_cost_includes_grid_fuel_and_export(self) -> None:
        cost = CostSimulator(
            import_tariff_inr_kwh=8,
            export_price_inr_kwh=4,
            fuel_price_inr_m3=10,
            battery_degradation_inr_kwh=0,
        ).simulate(
            {
                "grid_import_kwh": 2,
                "grid_export_kwh": 3,
                "boiler_fuel_m3": 4,
                "battery_charge_kwh": 0,
                "battery_discharge_kwh": 0,
            }
        )
        self.assertEqual(cost["net_operating_cost_inr"], 44)


if __name__ == "__main__":
    unittest.main()
