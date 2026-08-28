"""
Generic Machine Learning Model Manager
for AI Forecasting Module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.preprocessing import LabelEncoder

from common.utils import MODEL_DIR


class ModelManager:
    """
    Generic manager responsible for:

    - Model training
    - Prediction
    - Evaluation
    - Saving / Loading models
    - Saving / Loading encoders
    - Encoding / Decoding values
    """

    def __init__(self) -> None:

        self.models: Dict[str, Any] = {}

        self.encoders: Dict[str, LabelEncoder] = {}

    # =====================================================
    # Utility
    # =====================================================

    def is_model_loaded(
        self,
        model_name: str,
    ) -> bool:

        return model_name in self.models

    def is_encoder_loaded(
        self,
        encoder_name: str,
    ) -> bool:

        return encoder_name in self.encoders

    # =====================================================
    # Training
    # =====================================================

    def train(
        self,
        model_name: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        **kwargs,
    ) -> RandomForestRegressor:

        model = RandomForestRegressor(

            n_estimators=kwargs.get(
                "n_estimators",
                200,
            ),

            random_state=kwargs.get(
                "random_state",
                42,
            ),

            max_depth=kwargs.get(
                "max_depth",
                None,
            ),

            min_samples_split=kwargs.get(
                "min_samples_split",
                2,
            ),

            min_samples_leaf=kwargs.get(
                "min_samples_leaf",
                1,
            ),

            n_jobs=-1,
        )

        model.fit(
            X_train,
            y_train,
        )

        self.models[model_name] = model

        return model

    # =====================================================
    # Prediction
    # =====================================================

    def predict(
        self,
        model_name: str,
        X: pd.DataFrame,
    ):

        if not self.is_model_loaded(model_name):

            raise ValueError(
                f"Model '{model_name}' is not loaded."
            )

        return self.models[
            model_name
        ].predict(X)

    # =====================================================
    # Evaluation
    # =====================================================

    def evaluate(
        self,
        model_name: str,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> Dict[str, float]:

        prediction = self.predict(
            model_name,
            X_test,
        )

        mse = mean_squared_error(
            y_test,
            prediction,
        )

        return {

            "MAE": float(

                mean_absolute_error(
                    y_test,
                    prediction,
                )

            ),

            "MSE": float(
                mse,
            ),

            "RMSE": float(
                mse ** 0.5,
            ),

            "R2": float(

                r2_score(
                    y_test,
                    prediction,
                )

            ),
        }

    # =====================================================
    # Save Model
    # =====================================================

    def save_model(
        self,
        model_name: str,
    ) -> Path:

        if not self.is_model_loaded(
            model_name,
        ):

            raise ValueError(
                f"Model '{model_name}' not found."
            )

        filepath = (
            MODEL_DIR /
            f"{model_name}.joblib"
        )

        joblib.dump(

            self.models[
                model_name
            ],

            filepath,

        )

        return filepath

    # =====================================================
    # Load Model
    # =====================================================

    def load_model(
        self,
        model_name: str,
    ) -> bool:

        if self.is_model_loaded(
            model_name,
        ):
            return True

        filepath = (
            MODEL_DIR /
            f"{model_name}.joblib"
        )

        if not filepath.exists():
            return False

        self.models[
            model_name
        ] = joblib.load(
            filepath,
        )

        return True

        # =====================================================
    # Save Encoder
    # =====================================================

    def save_encoder(
        self,
        encoder_name: str,
        encoder: LabelEncoder,
    ) -> Path:

        filepath = (
            MODEL_DIR /
            f"{encoder_name}.joblib"
        )

        joblib.dump(
            encoder,
            filepath,
        )

        self.encoders[
            encoder_name
        ] = encoder

        return filepath

    # =====================================================
    # Load Encoder
    # =====================================================

    def load_encoder(
        self,
        encoder_name: str,
    ) -> bool:

        if self.is_encoder_loaded(
            encoder_name,
        ):
            return True

        filepath = (
            MODEL_DIR /
            f"{encoder_name}.joblib"
        )

        if not filepath.exists():
            return False

        self.encoders[
            encoder_name
        ] = joblib.load(
            filepath,
        )

        return True

    # =====================================================
    # Encode
    # =====================================================

    def transform(
        self,
        encoder_name: str,
        values: Iterable[Any],
    ):

        if not self.is_encoder_loaded(
            encoder_name,
        ):

            raise ValueError(
                f"Encoder '{encoder_name}' is not loaded."
            )

        return self.encoders[
            encoder_name
        ].transform(
            values,
        )

    # =====================================================
    # Decode
    # =====================================================

    def inverse_transform(
        self,
        encoder_name: str,
        values: Iterable[Any],
    ):

        if not self.is_encoder_loaded(
            encoder_name,
        ):

            raise ValueError(
                f"Encoder '{encoder_name}' is not loaded."
            )

        return self.encoders[
            encoder_name
        ].inverse_transform(
            values,
        )

    # =====================================================
    # Feature Importance
    # =====================================================

    def feature_importance(
        self,
        model_name: str,
        feature_names: Iterable[str],
    ) -> Dict[str, float]:

        if not self.is_model_loaded(
            model_name,
        ):

            raise ValueError(
                f"Model '{model_name}' is not loaded."
            )

        model = self.models[
            model_name
        ]

        if not hasattr(
            model,
            "feature_importances_",
        ):

            raise AttributeError(
                "Model does not support feature importance."
            )

        return {

            feature: float(score)

            for feature, score in zip(

                feature_names,

                model.feature_importances_,

            )

        }

    # =====================================================
    # Information
    # =====================================================

    def info(
        self,
    ) -> Dict[str, Any]:

        return {

            "loaded_models":
                list(
                    self.models.keys()
                ),

            "loaded_encoders":
                list(
                    self.encoders.keys()
                ),
        }

    # =====================================================
    # Magic Methods
    # =====================================================

    def __contains__(
        self,
        item: str,
    ) -> bool:

        return (
            item in self.models
        )

    def __len__(
        self,
    ) -> int:

        return len(
            self.models
        )

    def __str__(
        self,
    ) -> str:

        return (

            "ModelManager("
            f"{len(self.models)} models, "
            f"{len(self.encoders)} encoders)"

        )