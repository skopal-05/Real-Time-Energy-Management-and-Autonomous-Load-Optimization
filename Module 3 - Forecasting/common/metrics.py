"""
Evaluation metrics for AI Forecasting models.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
from numpy.typing import ArrayLike
from sklearn.metrics import (
    explained_variance_score,
    max_error,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)


class ForecastMetrics:
    """
    Computes regression metrics for forecasting models.
    """

    def __init__(
        self,
        y_true: ArrayLike,
        y_pred: ArrayLike,
    ) -> None:

        self.y_true = np.asarray(y_true)
        self.y_pred = np.asarray(y_pred)

        self._summary_cache: Dict[str, float] | None = None

        self._validate()

    # =====================================================
    # Validation
    # =====================================================

    def _validate(self) -> None:

        if self.y_true.size == 0:
            raise ValueError("y_true cannot be empty.")

        if self.y_pred.size == 0:
            raise ValueError("y_pred cannot be empty.")

        if self.y_true.shape != self.y_pred.shape:
            raise ValueError(
                "y_true and y_pred must have the same shape."
            )

    # =====================================================
    # Individual Metrics
    # =====================================================

    def mae(self) -> float:

        return float(
            mean_absolute_error(
                self.y_true,
                self.y_pred,
            )
        )

    def mse(self) -> float:

        return float(
            mean_squared_error(
                self.y_true,
                self.y_pred,
            )
        )

    def rmse(self) -> float:

        return float(np.sqrt(self.mse()))

    def mape(self) -> float:

        return float(
            mean_absolute_percentage_error(
                self.y_true,
                self.y_pred,
            )
            * 100
        )

    def r2(self) -> float:

        return float(
            r2_score(
                self.y_true,
                self.y_pred,
            )
        )

    def explained_variance(self) -> float:

        return float(
            explained_variance_score(
                self.y_true,
                self.y_pred,
            )
        )

    def maximum_error(self) -> float:

        return float(
            max_error(
                self.y_true,
                self.y_pred,
            )
        )

    # =====================================================
    # Summary
    # =====================================================

    def summary(self) -> Dict[str, float]:

        if self._summary_cache is None:

            self._summary_cache = {

                "MAE": self.mae(),

                "MSE": self.mse(),

                "RMSE": self.rmse(),

                "MAPE": self.mape(),

                "R2": self.r2(),

                "Explained Variance":
                    self.explained_variance(),

                "Max Error":
                    self.maximum_error(),
            }

        return self._summary_cache

    # =====================================================
    # Pretty Print
    # =====================================================

    def print_summary(self) -> None:

        print("\nForecast Evaluation")
        print("-" * 35)

        for metric, value in self.summary().items():

            print(
                f"{metric:<22}: {value:.4f}"
            )

    # =====================================================
    # Magic Methods
    # =====================================================

    def __str__(
        self,
    ) -> str:

        return str(
            self.summary()
        )

    def __repr__(
        self,
    ) -> str:

        return (
            f"ForecastMetrics("
            f"{self.summary()})"
        )