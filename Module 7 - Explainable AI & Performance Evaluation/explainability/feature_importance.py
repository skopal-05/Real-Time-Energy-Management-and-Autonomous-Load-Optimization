"""Global native and permutation feature-importance analysis."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd


class FeatureImportance:
    def native(self, model: Any, feature_names: Sequence[str]) -> dict[str, Any]:
        values = getattr(model, "feature_importances_", None)
        if values is None:
            raise ValueError("model does not expose feature_importances_")
        scores = np.asarray(values, dtype=float).reshape(-1)
        if scores.size != len(feature_names):
            raise ValueError("feature name count does not match model importances")
        if not np.all(np.isfinite(scores)):
            raise ValueError("feature importances must be finite")
        scores = np.abs(scores)
        total = float(np.sum(scores))
        normalized = scores / total if total > 0 else np.zeros_like(scores)
        ranked = sorted(
            (
                {
                    "feature": str(name),
                    "importance": round(float(score), 8),
                    "rank": 0,
                }
                for name, score in zip(feature_names, normalized)
            ),
            key=lambda item: item["importance"],
            reverse=True,
        )
        for rank, item in enumerate(ranked, start=1):
            item["rank"] = rank
        return {"method": "model_native", "feature_count": len(ranked), "features": ranked}

    def permutation(
        self,
        model: Any,
        features: Sequence[Sequence[float]],
        targets: Sequence[float],
        feature_names: Sequence[str],
        *,
        repeats: int = 5,
        seed: int = 42,
    ) -> dict[str, Any]:
        X = np.asarray(features, dtype=float)
        y = np.asarray(targets, dtype=float).reshape(-1)
        if X.ndim != 2 or X.shape[0] != y.size or X.shape[1] != len(feature_names):
            raise ValueError("features, targets, and feature_names are not aligned")
        if repeats < 1:
            raise ValueError("repeats must be positive")
        baseline_rmse = float(
            np.sqrt(np.mean((np.asarray(model.predict(self._prediction_input(X, feature_names))) - y) ** 2))
        )
        rng = np.random.default_rng(seed)
        raw_scores = []
        for column in range(X.shape[1]):
            changes = []
            for _ in range(repeats):
                permuted = X.copy()
                permuted[:, column] = rng.permutation(permuted[:, column])
                rmse = float(
                    np.sqrt(
                        np.mean(
                            (
                                np.asarray(
                                    model.predict(
                                        self._prediction_input(permuted, feature_names)
                                    )
                                )
                                - y
                            )
                            ** 2
                        )
                    )
                )
                changes.append(max(0.0, rmse - baseline_rmse))
            raw_scores.append(float(np.mean(changes)))
        total = sum(raw_scores)
        normalized = [value / total if total > 0 else 0.0 for value in raw_scores]
        ranked = sorted(
            (
                {"feature": str(name), "importance": round(score, 8), "rank": 0}
                for name, score in zip(feature_names, normalized)
            ),
            key=lambda item: item["importance"],
            reverse=True,
        )
        for rank, item in enumerate(ranked, start=1):
            item["rank"] = rank
        return {
            "method": "permutation_rmse",
            "baseline_rmse": round(baseline_rmse, 8),
            "feature_count": len(ranked),
            "features": ranked,
        }

    @staticmethod
    def _prediction_input(X: np.ndarray, feature_names: Sequence[str]) -> Any:
        return pd.DataFrame(X, columns=list(feature_names))
