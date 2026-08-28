"""Robust regression metrics for forecasting model evaluation."""

from __future__ import annotations

from math import isfinite
from typing import Iterable

import numpy as np


class RegressionMetrics:
    """Calculate JSON-safe forecasting metrics without hidden zero handling."""

    def calculate(
        self, actual: Iterable[float], predicted: Iterable[float]
    ) -> dict[str, float]:
        y_true = np.asarray(list(actual), dtype=float).reshape(-1)
        y_pred = np.asarray(list(predicted), dtype=float).reshape(-1)
        self._validate(y_true, y_pred)
        residual = y_pred - y_true
        absolute = np.abs(residual)
        squared = residual**2
        nonzero = np.abs(y_true) > 1e-12
        if np.any(nonzero):
            mape = float(np.mean(absolute[nonzero] / np.abs(y_true[nonzero])) * 100)
        else:
            mape = 0.0 if np.allclose(y_pred, 0.0) else 100.0
        smape_denominator = np.abs(y_true) + np.abs(y_pred)
        smape_terms = np.divide(
            2 * absolute,
            smape_denominator,
            out=np.zeros_like(absolute),
            where=smape_denominator > 1e-12,
        )
        total_variance = float(np.sum((y_true - np.mean(y_true)) ** 2))
        residual_variance = float(np.sum((y_true - y_pred) ** 2))
        r2 = (
            1.0 - residual_variance / total_variance
            if total_variance > 1e-12
            else (1.0 if np.allclose(y_true, y_pred) else 0.0)
        )
        denominator = float(np.sum(np.abs(y_true)))
        wape = float(np.sum(absolute) / denominator * 100) if denominator > 1e-12 else mape
        values = {
            "sample_count": float(y_true.size),
            "mae": float(np.mean(absolute)),
            "mse": float(np.mean(squared)),
            "rmse": float(np.sqrt(np.mean(squared))),
            "mape_percent": mape,
            "smape_percent": float(np.mean(smape_terms) * 100),
            "wape_percent": wape,
            "r2": r2,
            "bias": float(np.mean(residual)),
            "max_error": float(np.max(absolute)),
        }
        return {name: round(value, 8) for name, value in values.items()}

    @staticmethod
    def _validate(y_true: np.ndarray, y_pred: np.ndarray) -> None:
        if y_true.size == 0:
            raise ValueError("actual values cannot be empty")
        if y_true.shape != y_pred.shape:
            raise ValueError("actual and predicted values must have the same shape")
        if not np.all(np.isfinite(y_true)) or not np.all(np.isfinite(y_pred)):
            raise ValueError("actual and predicted values must be finite")

