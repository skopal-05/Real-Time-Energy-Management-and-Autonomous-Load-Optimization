"""Validation for structured Module 7 performance reports."""

from __future__ import annotations

from math import isfinite
from typing import Any, Mapping


class EvaluationValidator:
    REQUIRED_FORECAST_METRICS = {
        "sample_count",
        "mae",
        "mse",
        "rmse",
        "mape_percent",
        "smape_percent",
        "wape_percent",
        "r2",
        "bias",
        "max_error",
    }

    def validate_forecast_metrics(self, metrics: Mapping[str, Any]) -> list[str]:
        errors: list[str] = []
        missing = self.REQUIRED_FORECAST_METRICS - set(metrics)
        if missing:
            errors.append(f"missing forecast metrics: {sorted(missing)}")
        for name in self.REQUIRED_FORECAST_METRICS & set(metrics):
            value = metrics[name]
            if isinstance(value, bool):
                errors.append(f"{name} must be numeric")
            else:
                try:
                    valid = isfinite(float(value))
                except (TypeError, ValueError):
                    valid = False
                if not valid:
                    errors.append(f"{name} must be finite")
        if float(metrics.get("sample_count", 0)) <= 0:
            errors.append("sample_count must be positive")
        return errors

    def validate_report(self, report: Mapping[str, Any]) -> list[str]:
        errors: list[str] = []
        models = report.get("forecasting_models")
        if not isinstance(models, Mapping) or not models:
            errors.append("forecasting_models must be a non-empty object")
        else:
            for model_name, item in models.items():
                if not isinstance(item, Mapping) or "metrics" not in item:
                    errors.append(f"{model_name} missing metrics")
                else:
                    errors.extend(
                        f"{model_name}: {error}"
                        for error in self.validate_forecast_metrics(item["metrics"])
                    )
        for section in ("decision_pipeline", "scenario_evaluation", "optimization_benchmark"):
            if section not in report:
                errors.append(f"missing report section: {section}")
        return errors

    @staticmethod
    def require_valid(errors: list[str], label: str = "evaluation output") -> None:
        if errors:
            raise ValueError(f"invalid {label}: " + "; ".join(errors))

