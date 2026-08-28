"""Person 1 tests: evaluation, monitoring, and retraining."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor

MODULE_ROOT = Path(__file__).resolve().parent.parent
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from evaluation import Benchmark, EvaluationValidator, PerformanceEvaluator, RegressionMetrics
from retraining import ModelMonitor, RetrainingPipeline, RetrainingValidator


class RegressionMetricTests(unittest.TestCase):
    def test_perfect_prediction_metrics(self) -> None:
        metrics = RegressionMetrics().calculate([1, 2, 3], [1, 2, 3])
        self.assertEqual(metrics["rmse"], 0)
        self.assertEqual(metrics["mape_percent"], 0)
        self.assertEqual(metrics["r2"], 1)

    def test_zero_targets_are_json_safe(self) -> None:
        metrics = RegressionMetrics().calculate([0, 0, 2], [0, 1, 2])
        self.assertTrue(np.isfinite(list(metrics.values())).all())

    def test_rejects_misaligned_or_nonfinite_values(self) -> None:
        with self.assertRaises(ValueError):
            RegressionMetrics().calculate([1, 2], [1])
        with self.assertRaises(ValueError):
            RegressionMetrics().calculate([1, float("nan")], [1, 2])


class BenchmarkAndEvaluatorTests(unittest.TestCase):
    def test_benchmark_obeys_metric_direction(self) -> None:
        result = Benchmark().compare(
            {"cost": 100, "export": 10},
            {"cost": 80, "export": 15},
            higher_is_better={"export"},
        )
        self.assertEqual(result["summary"]["improved"], 2)

    def test_performance_evaluator_builds_complete_report(self) -> None:
        evaluator = PerformanceEvaluator()
        forecast = {
            "demo": evaluator.evaluate_forecast(
                "demo", [10, 20, 30], [11, 19, 30], target="load_kw"
            )
        }
        report = evaluator.build_report(
            forecast,
            {
                "recommendations": [
                    {"priority": "high", "setpoints": {"x": 1}, "constraints": ["x <= 2"]}
                ]
            },
            {
                "ranked_scenarios": [
                    {"scenario_id": "a", "ranking": {"score": 90, "rank": 1}},
                    {"scenario_id": "b", "ranking": {"score": 70, "rank": 2}},
                ]
            },
            {
                "baseline_metrics": {"cost": {"net_operating_cost_inr": 100}},
                "optimized_metrics": {"cost": {"net_operating_cost_inr": 80}},
            },
        )
        self.assertFalse(EvaluationValidator().validate_report(report))
        self.assertEqual(report["scenario_evaluation"]["best_scenario_id"], "a")
        self.assertEqual(report["optimization_benchmark"]["summary"]["improved"], 1)

    def test_evaluation_validator_rejects_incomplete_report(self) -> None:
        errors = EvaluationValidator().validate_report({})
        self.assertTrue(errors)


class MonitoringTests(unittest.TestCase):
    def test_detects_metric_degradation(self) -> None:
        result = ModelMonitor().monitor_performance(
            "model", {"mae": 2, "rmse": 3, "r2": 0.9}, {"mae": 3, "rmse": 4, "r2": 0.7}
        )
        self.assertEqual(result["status"], "degraded")
        self.assertTrue(result["retraining_required"])

    def test_healthy_metrics_do_not_trigger_retraining(self) -> None:
        result = ModelMonitor().monitor_performance(
            "model", {"mae": 2, "rmse": 3, "r2": 0.9}, {"mae": 2.1, "rmse": 3.1, "r2": 0.88}
        )
        self.assertEqual(result["status"], "healthy")

    def test_absolute_r2_quality_floor_triggers_review(self) -> None:
        result = ModelMonitor(minimum_r2=0.5).monitor_performance(
            "model", {"mae": 2, "rmse": 3, "r2": 0.4}, {"mae": 2, "rmse": 3, "r2": 0.4}
        )
        self.assertTrue(result["retraining_required"])
        self.assertTrue(any("minimum quality threshold" in reason for reason in result["reasons"]))

    def test_detects_feature_drift(self) -> None:
        reference = np.column_stack([np.arange(20), np.arange(20)])
        current = reference.copy().astype(float)
        current[:, 1] += 20
        report = ModelMonitor(drift_threshold=1).feature_drift(
            reference, current, ["stable", "shifted"]
        )
        self.assertEqual(report["status"], "drift_detected")
        self.assertEqual(report["drifted_features"], ["shifted"])


class RetrainingTests(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(4)
        self.X = rng.normal(size=(80, 3))
        self.y = 4 * self.X[:, 0] - 2 * self.X[:, 1] + rng.normal(scale=0.1, size=80)
        self.model = RandomForestRegressor(n_estimators=20, random_state=1).fit(self.X, self.y)

    def test_no_trigger_does_not_train_candidate(self) -> None:
        report, candidate = RetrainingPipeline().run(
            self.model, self.X, self.y, model_name="demo", trigger=False
        )
        self.assertEqual(report["status"], "not_required")
        self.assertIsNone(candidate)

    def test_forced_retraining_evaluates_candidate_without_promotion(self) -> None:
        report, candidate = RetrainingPipeline().run(
            self.model, self.X, self.y, model_name="demo", trigger=False, force=True
        )
        self.assertEqual(report["status"], "candidate_accepted")
        self.assertFalse(report["promoted"])
        self.assertIsNotNone(candidate)
        self.assertFalse(RetrainingValidator().validate_retraining(report))

    def test_retraining_validator_rejects_invalid_promotion(self) -> None:
        errors = RetrainingValidator().validate_retraining(
            {
                "model": "demo",
                "triggered": False,
                "status": "not_required",
                "promoted": True,
                "current_metrics": {},
                "candidate_metrics": None,
            }
        )
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
