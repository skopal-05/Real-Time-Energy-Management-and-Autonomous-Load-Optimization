"""Person 2 tests: recommendation generation, validation, and JSON outputs."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parent.parent
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from contracts import OptimizationResult
from recommendation import RecommendationEngine, RecommendationValidator


def result_fixture() -> OptimizationResult:
    baseline_metrics = {
        "energy": {"energy_objective_kwh": 1500.0, "primary_energy_kwh": 1450.0},
        "cost": {"net_operating_cost_inr": 6000.0},
        "carbon": {"total_emissions_kg_co2e": 260.0},
    }
    optimized_metrics = {
        "energy": {"energy_objective_kwh": 1450.0, "primary_energy_kwh": 1450.0},
        "cost": {"net_operating_cost_inr": 5600.0},
        "carbon": {"total_emissions_kg_co2e": 240.0},
    }
    return OptimizationResult(
        baseline_state={
            "production_load_kw": 68.7,
            "compressor_power_kw": 60.0,
            "hvac_power_kw": 10.0,
            "battery_charge_kw": 40.0,
            "battery_discharge_kw": 0.0,
            "grid_export_limit_kw": 80.0,
            "boiler_fuel_m3_hr": 130.0,
        },
        optimized_state={
            "production_load_kw": 68.7,
            "compressor_power_kw": 52.0,
            "hvac_power_kw": 8.0,
            "battery_charge_kw": 20.0,
            "battery_discharge_kw": 0.0,
            "grid_export_limit_kw": 100.0,
            "boiler_fuel_m3_hr": 122.0,
        },
        baseline_metrics=baseline_metrics,
        optimized_metrics=optimized_metrics,
        objective={"total": 0.9},
        feasible=True,
        violations=(),
        algorithm={"name": "test_algorithm"},
    )


class RecommendationEngineTests(unittest.TestCase):
    def test_converts_changed_setpoints_to_actions(self) -> None:
        recommendations = RecommendationEngine().generate(result_fixture())
        variables = {item["recommendation_id"] for item in recommendations}
        self.assertIn("optimize_compressor_power_kw", variables)
        self.assertIn("optimize_grid_export_limit_kw", variables)
        self.assertTrue(all(item["constraints_respected"] for item in recommendations))

    def test_expected_impact_matches_result_metrics(self) -> None:
        recommendations = RecommendationEngine().generate(result_fixture())
        impact = recommendations[0]["expected_impact"]
        self.assertEqual(impact["energy_saving_kwh"], 50.0)
        self.assertEqual(impact["cost_saving_inr"], 400.0)
        self.assertEqual(impact["emissions_avoided_kg_co2e"], 20.0)

    def test_writes_all_required_json_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = RecommendationEngine().write_outputs(result_fixture(), directory)
            self.assertEqual(set(paths), {"optimized_state", "recommendations", "report"})
            for path in paths.values():
                self.assertTrue(path.exists())
                self.assertIsInstance(json.loads(path.read_text(encoding="utf-8")), dict)
            report = json.loads(paths["report"].read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["cost_saving_inr"], 400.0)


class RecommendationValidatorTests(unittest.TestCase):
    def test_rejects_duplicate_ids_and_invalid_priority(self) -> None:
        item = RecommendationEngine().generate(result_fixture())[0]
        duplicate = dict(item)
        duplicate["priority"] = "urgent"
        errors = RecommendationValidator().validate([item, duplicate])
        self.assertTrue(any("duplicate" in error for error in errors))
        self.assertTrue(any("invalid priority" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
