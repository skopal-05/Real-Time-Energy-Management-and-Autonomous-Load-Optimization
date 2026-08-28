"""Safe candidate-model retraining and optional promotion pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import train_test_split

from evaluation.metrics import RegressionMetrics
from retraining.retraining_validator import RetrainingValidator


class RetrainingPipeline:
    """Train and compare a candidate without overwriting the current model by default."""

    def __init__(self, *, minimum_rmse_improvement: float = 0.01, random_state: int = 42) -> None:
        self.minimum_improvement = minimum_rmse_improvement
        self.random_state = random_state
        self.metrics = RegressionMetrics()
        self.validator = RetrainingValidator()

    def run(
        self,
        model: Any,
        features: Sequence[Sequence[float]],
        targets: Sequence[float],
        *,
        model_name: str,
        trigger: bool,
        force: bool = False,
        promotion_path: str | Path | None = None,
    ) -> tuple[dict[str, Any], Any | None]:
        X = np.asarray(features)
        y = np.asarray(targets, dtype=float).reshape(-1)
        if X.ndim != 2 or X.shape[0] != y.size or y.size < 10:
            raise ValueError("retraining requires at least 10 aligned feature/target rows")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state, shuffle=True
        )
        current_input: Any = X_test
        model_feature_names = getattr(model, "feature_names_in_", None)
        if model_feature_names is not None:
            current_input = pd.DataFrame(X_test, columns=list(model_feature_names))
        current_metrics = self.metrics.calculate(y_test, model.predict(current_input))
        should_train = bool(trigger or force)
        if not should_train:
            report = {
                "model": model_name,
                "triggered": False,
                "status": "not_required",
                "promoted": False,
                "current_metrics": current_metrics,
                "candidate_metrics": None,
                "rmse_improvement_percent": 0.0,
                "promotion_path": None,
            }
            self.validator.require_valid(
                self.validator.validate_retraining(report), "retraining report"
            )
            return report, None

        candidate = clone(model)
        candidate.fit(X_train, y_train)
        candidate_metrics = self.metrics.calculate(y_test, candidate.predict(X_test))
        current_rmse = current_metrics["rmse"]
        candidate_rmse = candidate_metrics["rmse"]
        improvement = (current_rmse - candidate_rmse) / max(abs(current_rmse), 1e-12)
        accepted = improvement >= self.minimum_improvement or force
        promoted = False
        written_path = None
        if accepted and promotion_path is not None:
            path = Path(promotion_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(candidate, path)
            promoted = True
            written_path = str(path)
        report = {
            "model": model_name,
            "triggered": True,
            "status": "candidate_accepted" if accepted else "candidate_rejected",
            "promoted": promoted,
            "current_metrics": current_metrics,
            "candidate_metrics": candidate_metrics,
            "rmse_improvement_percent": round(improvement * 100, 4),
            "promotion_path": written_path,
        }
        self.validator.require_valid(
            self.validator.validate_retraining(report), "retraining report"
        )
        return report, candidate
