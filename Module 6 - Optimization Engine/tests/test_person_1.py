"""Person 1 tests: genetic algorithm, objective, constraints, and optimizer."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parent.parent
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from algorithms import GeneticAlgorithm
from contracts import OptimizationProblem, VariableBound
from optimization import ConstraintChecker, ObjectiveFunction, OptimizationValidator, Optimizer


BEST_SCENARIO = {
    "best_scenario": {
        "scenario_id": "cost_saver",
        "horizon_hours": 1.0,
        "operating_point": {
            "production_load_kw": 0.0,
            "compressor_power_kw": 43.953,
            "hvac_power_kw": 6.681,
            "renewable_generation_kw": 260.88,
            "battery_charge_kw": 40.0,
            "battery_discharge_kw": 0.0,
            "grid_export_limit_kw": 100.0,
            "boiler_fuel_m3_hr": 122.58,
        },
    }
}

RECOMMENDATIONS = {
    "recommendations": [
        {
            "agent": "compressor_agent",
            "setpoints": {"compressor_power_target_kw": 51.71},
        },
        {"agent": "hvac_agent", "setpoints": {"hvac_power_target_kw": 7.86}},
        {
            "agent": "boiler_agent",
            "setpoints": {"boiler_fuel_target_m3_hr": 122.58},
        },
        {
            "agent": "cost_optimization_agent",
            "setpoints": {"production_load_target_kw": 68.7},
        },
    ]
}

SYSTEM_STATE = {
    "state_of_charge_percent": 50,
    "capacity_kwh": 100,
    "minimum_soc_percent": 20,
    "maximum_soc_percent": 90,
    "maximum_charge_kw": 50,
    "maximum_discharge_kw": 50,
    "grid_import_limit_kw": 500,
    "maximum_compressor_power_kw": 100,
    "maximum_hvac_power_kw": 100,
    "maximum_fuel_flow_m3_hr": 200,
}


class GeneticAlgorithmTests(unittest.TestCase):
    def test_minimizes_simple_quadratic(self) -> None:
        algorithm = GeneticAlgorithm(population_size=30, generations=45, seed=7)
        result = algorithm.minimize(
            lambda values: (values["x"] - 2.0) ** 2,
            {"x": (-10.0, 10.0)},
        )
        self.assertAlmostEqual(result.values["x"], 2.0, delta=0.15)
        self.assertEqual(result.evaluations, 30 * 45)

    def test_seed_makes_results_reproducible(self) -> None:
        kwargs = {"population_size": 15, "generations": 10, "seed": 10}
        first = GeneticAlgorithm(**kwargs).minimize(lambda value: value["x"] ** 2, {"x": (-1, 1)})
        second = GeneticAlgorithm(**kwargs).minimize(lambda value: value["x"] ** 2, {"x": (-1, 1)})
        self.assertEqual(first.values, second.values)
        self.assertEqual(first.history, second.history)


class ConstraintAndObjectiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = Optimizer().build_problem(BEST_SCENARIO, RECOMMENDATIONS, system_state=SYSTEM_STATE)

    def test_recovers_nonzero_production_requirement(self) -> None:
        self.assertEqual(self.problem.baseline_state["production_load_kw"], 68.7)
        self.assertEqual(self.problem.bounds["production_load_kw"].minimum, 68.7)

    def test_rejects_simultaneous_battery_actions(self) -> None:
        state = dict(self.problem.baseline_state)
        state["battery_charge_kw"] = 10
        state["battery_discharge_kw"] = 5
        violations = ConstraintChecker().violations(state, self.problem)
        self.assertIn("battery cannot charge and discharge simultaneously", violations)

    def test_repair_respects_maximum_soc(self) -> None:
        problem = OptimizationProblem(
            baseline_state=self.problem.baseline_state,
            bounds=self.problem.bounds,
            state_of_charge_percent=89,
            maximum_soc_percent=90,
        )
        repaired = ConstraintChecker().repair(problem.baseline_state, problem)
        self.assertLessEqual(ConstraintChecker().projected_soc(repaired, problem), 90)

    def test_balancing_battery_charge_and_export_improves_objective(self) -> None:
        objective = ObjectiveFunction()
        baseline = ConstraintChecker().repair(self.problem.baseline_state, self.problem)
        baseline_metrics = objective.metrics(baseline, self.problem)
        candidate = dict(baseline)
        candidate["battery_charge_kw"] = 32.61
        candidate_score, _ = objective.score(candidate, self.problem, baseline_metrics)
        baseline_score, _ = objective.score(baseline, self.problem, baseline_metrics)
        self.assertLess(candidate_score, baseline_score)


class OptimizerTests(unittest.TestCase):
    def test_optimizer_returns_feasible_improved_state(self) -> None:
        optimizer = Optimizer(
            algorithm=GeneticAlgorithm(population_size=30, generations=35, seed=42)
        )
        problem = optimizer.build_problem(BEST_SCENARIO, RECOMMENDATIONS, system_state=SYSTEM_STATE)
        result = optimizer.optimize(problem)
        self.assertTrue(result.feasible)
        self.assertEqual(result.optimized_state["production_load_kw"], 68.7)
        self.assertGreaterEqual(result.optimized_state["compressor_power_kw"], 51.71)
        self.assertLess(
            result.optimized_metrics["cost"]["net_operating_cost_inr"],
            result.baseline_metrics["cost"]["net_operating_cost_inr"],
        )
        self.assertFalse(OptimizationValidator().validate_result(result, problem))

    def test_zero_production_without_module_4_target_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "production load is zero"):
            Optimizer().build_problem(BEST_SCENARIO, [], system_state=SYSTEM_STATE)


if __name__ == "__main__":
    unittest.main()
