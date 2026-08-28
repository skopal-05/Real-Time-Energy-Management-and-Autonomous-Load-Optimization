"""Detect model performance degradation and numeric feature drift."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

import numpy as np


class ModelMonitor:
    def __init__(
        self,
        *,
        error_degradation_threshold: float = 0.20,
        r2_drop_threshold: float = 0.10,
        minimum_r2: float = 0.50,
        drift_threshold: float = 0.75,
    ) -> None:
        self.error_threshold = error_degradation_threshold
        self.r2_threshold = r2_drop_threshold
        self.minimum_r2 = minimum_r2
        self.drift_threshold = drift_threshold

    def monitor_performance(
        self,
        model_name: str,
        reference_metrics: Mapping[str, float],
        current_metrics: Mapping[str, float],
    ) -> dict[str, Any]:
        reasons: list[str] = []
        changes: dict[str, float] = {}
        for metric in ("mae", "rmse"):
            if metric in reference_metrics and metric in current_metrics:
                reference = float(reference_metrics[metric])
                current = float(current_metrics[metric])
                change = (current - reference) / max(abs(reference), 1e-12)
                changes[f"{metric}_relative_change"] = round(change, 6)
                if change > self.error_threshold:
                    reasons.append(f"{metric} degraded by {change * 100:.2f}%")
        if "r2" in reference_metrics and "r2" in current_metrics:
            drop = float(reference_metrics["r2"]) - float(current_metrics["r2"])
            changes["r2_absolute_drop"] = round(drop, 6)
            if drop > self.r2_threshold:
                reasons.append(f"r2 dropped by {drop:.4f}")
            if float(current_metrics["r2"]) < self.minimum_r2:
                reasons.append(
                    f"r2={float(current_metrics['r2']):.4f} is below the "
                    f"minimum quality threshold {self.minimum_r2:.4f}"
                )
        return {
            "model": model_name,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "status": "degraded" if reasons else "healthy",
            "retraining_required": bool(reasons),
            "reasons": reasons,
            "metric_changes": changes,
            "reference_metrics": dict(reference_metrics),
            "current_metrics": dict(current_metrics),
        }

    def feature_drift(
        self,
        reference: Sequence[Sequence[float]],
        current: Sequence[Sequence[float]],
        feature_names: Sequence[str],
    ) -> dict[str, Any]:
        reference_array = np.asarray(reference, dtype=float)
        current_array = np.asarray(current, dtype=float)
        if reference_array.ndim != 2 or current_array.ndim != 2:
            raise ValueError("reference and current features must be two-dimensional")
        if reference_array.shape[1] != current_array.shape[1]:
            raise ValueError("reference and current feature counts must match")
        if reference_array.shape[1] != len(feature_names):
            raise ValueError("feature_names length must match feature columns")
        if not np.all(np.isfinite(reference_array)) or not np.all(np.isfinite(current_array)):
            raise ValueError("feature values must be finite")
        details = []
        drifted = []
        for index, name in enumerate(feature_names):
            ref = reference_array[:, index]
            cur = current_array[:, index]
            scale = max(float(np.std(ref)), 1e-9)
            mean_shift = abs(float(np.mean(cur) - np.mean(ref))) / scale
            detected = mean_shift > self.drift_threshold
            if detected:
                drifted.append(str(name))
            details.append(
                {
                    "feature": str(name),
                    "reference_mean": round(float(np.mean(ref)), 8),
                    "current_mean": round(float(np.mean(cur)), 8),
                    "standardized_mean_shift": round(mean_shift, 8),
                    "drift_detected": detected,
                }
            )
        return {
            "status": "drift_detected" if drifted else "stable",
            "drift_detected": bool(drifted),
            "drifted_features": drifted,
            "features": details,
        }
