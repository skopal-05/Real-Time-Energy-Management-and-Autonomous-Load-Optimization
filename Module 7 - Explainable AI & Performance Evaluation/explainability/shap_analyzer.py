"""Exact Shapley-value explanations for small industrial forecasting models."""

from __future__ import annotations

from math import factorial
from typing import Any, Sequence

import numpy as np
import pandas as pd


class ShapAnalyzer:
    """Compute exact single-reference SHAP values by enumerating coalitions.

    Module 3 models use at most six input features, so exact enumeration needs
    at most 64 coalition predictions per explained row and avoids an additional
    runtime dependency.
    """

    def __init__(self, *, maximum_exact_features: int = 10) -> None:
        self.maximum_exact_features = maximum_exact_features

    def explain(
        self,
        model: Any,
        background: Sequence[Sequence[float]],
        samples: Sequence[Sequence[float]],
        feature_names: Sequence[str],
    ) -> dict[str, Any]:
        background_array = np.asarray(background, dtype=float)
        sample_array = np.asarray(samples, dtype=float)
        if background_array.ndim != 2 or sample_array.ndim != 2:
            raise ValueError("background and samples must be two-dimensional")
        if background_array.shape[1] != sample_array.shape[1]:
            raise ValueError("background and sample feature counts must match")
        feature_count = background_array.shape[1]
        if feature_count != len(feature_names):
            raise ValueError("feature_names length must match feature columns")
        if feature_count > self.maximum_exact_features:
            raise ValueError(
                f"exact SHAP supports at most {self.maximum_exact_features} features"
            )
        if not np.all(np.isfinite(background_array)) or not np.all(np.isfinite(sample_array)):
            raise ValueError("SHAP inputs must be finite")

        reference = np.mean(background_array, axis=0)
        base_value = self._predict(model, reference, feature_names)
        explanations = []
        for row_index, sample in enumerate(sample_array):
            coalition_predictions: dict[int, float] = {}
            for mask in range(1 << feature_count):
                point = reference.copy()
                for index in range(feature_count):
                    if mask & (1 << index):
                        point[index] = sample[index]
                coalition_predictions[mask] = self._predict(model, point, feature_names)
            contributions = []
            for feature_index, feature_name in enumerate(feature_names):
                shap_value = 0.0
                feature_bit = 1 << feature_index
                for mask in range(1 << feature_count):
                    if mask & feature_bit:
                        continue
                    coalition_size = mask.bit_count()
                    weight = (
                        factorial(coalition_size)
                        * factorial(feature_count - coalition_size - 1)
                        / factorial(feature_count)
                    )
                    shap_value += weight * (
                        coalition_predictions[mask | feature_bit]
                        - coalition_predictions[mask]
                    )
                contributions.append(
                    {
                        "feature": str(feature_name),
                        "feature_value": round(float(sample[feature_index]), 8),
                        "shap_value": round(float(shap_value), 8),
                        "effect": "increases" if shap_value > 0 else (
                            "decreases" if shap_value < 0 else "neutral"
                        ),
                    }
                )
            prediction = coalition_predictions[(1 << feature_count) - 1]
            contribution_sum = sum(item["shap_value"] for item in contributions)
            explanations.append(
                {
                    "sample_index": row_index,
                    "base_value": round(base_value, 8),
                    "prediction": round(prediction, 8),
                    "contribution_sum": round(contribution_sum, 8),
                    "additivity_error": round(
                        abs(prediction - (base_value + contribution_sum)), 10
                    ),
                    "features": sorted(
                        contributions, key=lambda item: abs(item["shap_value"]), reverse=True
                    ),
                }
            )
        return {
            "method": "exact_single_reference_shapley",
            "feature_count": feature_count,
            "background_sample_count": int(background_array.shape[0]),
            "reference_values": {
                str(name): round(float(value), 8)
                for name, value in zip(feature_names, reference)
            },
            "explanations": explanations,
        }

    @staticmethod
    def _predict(model: Any, row: np.ndarray, feature_names: Sequence[str]) -> float:
        data = pd.DataFrame([row], columns=list(feature_names))
        prediction = np.asarray(model.predict(data), dtype=float).reshape(-1)
        if prediction.size != 1 or not np.isfinite(prediction[0]):
            raise ValueError("model must produce one finite prediction per SHAP sample")
        return float(prediction[0])

