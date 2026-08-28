"""Validated wrapper around scikit-learn Isolation Forest."""

from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.ensemble import IsolationForest


class IsolationForestModel:
    def __init__(
        self,
        *,
        contamination: float = 0.05,
        n_estimators: int = 200,
        random_state: int = 42,
    ) -> None:
        if not 0 < contamination <= 0.5:
            raise ValueError("contamination must be in (0, 0.5]")
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
        )
        self.feature_count: int | None = None

    def fit(self, features: Sequence[Sequence[float]]) -> "IsolationForestModel":
        X = self._array(features)
        if X.shape[0] < 10:
            raise ValueError("Isolation Forest requires at least 10 training rows")
        self.model.fit(X)
        self.feature_count = X.shape[1]
        return self

    def score(self, features: Sequence[Sequence[float]]) -> list[dict[str, float | int | str]]:
        if self.feature_count is None:
            raise RuntimeError("Isolation Forest must be fitted before scoring")
        X = self._array(features)
        if X.shape[1] != self.feature_count:
            raise ValueError("scoring feature count does not match fitted model")
        predictions = self.model.predict(X)
        decision = self.model.decision_function(X)
        raw_anomaly = -decision
        minimum = float(np.min(raw_anomaly))
        maximum = float(np.max(raw_anomaly))
        if maximum - minimum > 1e-12:
            normalized = (raw_anomaly - minimum) / (maximum - minimum)
        else:
            normalized = 1 / (1 + np.exp(-raw_anomaly))
        return [
            {
                "row_index": int(index),
                "raw_score": round(float(raw_anomaly[index]), 8),
                "anomaly_score": round(float(normalized[index]), 8),
                "label": "anomaly" if predictions[index] == -1 else "normal",
                "is_anomaly": bool(predictions[index] == -1),
            }
            for index in range(X.shape[0])
        ]

    @staticmethod
    def _array(features: Sequence[Sequence[float]]) -> np.ndarray:
        X = np.asarray(features, dtype=float)
        if X.ndim != 2 or X.shape[0] == 0 or X.shape[1] == 0:
            raise ValueError("features must be a non-empty two-dimensional array")
        if not np.all(np.isfinite(X)):
            raise ValueError("features must be finite")
        return X

