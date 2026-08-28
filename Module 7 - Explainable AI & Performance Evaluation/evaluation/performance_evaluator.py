"""Evaluate forecasting models and the Modules 4–6 decision pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from evaluation.benchmark import Benchmark
from evaluation.evaluation_validator import EvaluationValidator
from evaluation.metrics import RegressionMetrics


class PerformanceEvaluator:
    def __init__(self) -> None:
        self.metrics = RegressionMetrics()
        self.benchmark = Benchmark()
        self.validator = EvaluationValidator()

    def evaluate_forecast(
        self,
        model_name: str,
        actual: Iterable[float],
        predicted: Iterable[float],
        *,
        target: str,
    ) -> dict[str, Any]:
        metrics = self.metrics.calculate(actual, predicted)
        self.validator.require_valid(
            self.validator.validate_forecast_metrics(metrics), f"{model_name} metrics"
        )
        return {"model": model_name, "target": target, "metrics": metrics}

    def build_report(
        self,
        forecast_evaluations: Mapping[str, Mapping[str, Any]],
        agent_output: Mapping[str, Any],
        scenario_output: Mapping[str, Any],
        optimization_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        recommendations = agent_output.get("recommendations", [])
        ranked = scenario_output.get("ranked_scenarios", [])
        priorities = [item.get("priority") for item in recommendations if isinstance(item, Mapping)]
        setpoint_count = sum(
            bool(item.get("setpoints")) for item in recommendations if isinstance(item, Mapping)
        )
        constrained_count = sum(
            bool(item.get("constraints")) for item in recommendations if isinstance(item, Mapping)
        )
        scores = [
            float(item.get("ranking", {}).get("score", 0.0))
            for item in ranked
            if isinstance(item, Mapping)
        ]
        decision = {
            "recommendation_count": len(recommendations),
            "high_or_critical_priority_count": sum(
                priority in {"high", "critical"} for priority in priorities
            ),
            "setpoint_coverage_percent": round(setpoint_count / max(len(recommendations), 1) * 100, 2),
            "constraint_coverage_percent": round(
                constrained_count / max(len(recommendations), 1) * 100, 2
            ),
        }
        scenario = {
            "scenario_count": len(ranked),
            "best_scenario_id": ranked[0].get("scenario_id") if ranked else None,
            "best_score": max(scores) if scores else None,
            "score_spread": round(max(scores) - min(scores), 4) if scores else None,
            "all_scenarios_ranked": bool(ranked)
            and sorted(item.get("ranking", {}).get("rank") for item in ranked)
            == list(range(1, len(ranked) + 1)),
        }
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "forecasting_models": dict(forecast_evaluations),
            "forecasting_summary": self._forecast_summary(forecast_evaluations),
            "decision_pipeline": decision,
            "scenario_evaluation": scenario,
            "optimization_benchmark": self.benchmark.compare_optimization_report(
                optimization_report
            ),
        }
        self.validator.require_valid(self.validator.validate_report(report))
        return report

    @staticmethod
    def _forecast_summary(
        evaluations: Mapping[str, Mapping[str, Any]]
    ) -> dict[str, float]:
        wapes = [float(item["metrics"]["wape_percent"]) for item in evaluations.values()]
        smapes = [float(item["metrics"]["smape_percent"]) for item in evaluations.values()]
        r2_values = [float(item["metrics"]["r2"]) for item in evaluations.values()]
        return {
            "model_count": len(evaluations),
            "mean_wape_percent": round(sum(wapes) / max(len(wapes), 1), 8),
            "mean_smape_percent": round(sum(smapes) / max(len(smapes), 1), 8),
            "mean_r2": round(sum(r2_values) / max(len(r2_values), 1), 8),
        }
