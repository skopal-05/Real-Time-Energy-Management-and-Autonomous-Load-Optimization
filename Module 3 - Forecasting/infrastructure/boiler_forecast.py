"""
Boiler Forecasting Module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from common.config import MODULE_CONFIG
from common.forecasting_base import ForecastingBase
from common.model_manager import ModelManager


class BoilerForecast(ForecastingBase):
    """
    Forecast boiler steam flow using the trained Random Forest model.
    """

    def __init__(self) -> None:

        config = MODULE_CONFIG["boiler"]

        super().__init__(
            model_name=config["model"],
            prediction_horizon=1,
        )

        self.config = config

        self.features = config["features"]

        self.target = config["target"]

        self.manager = ModelManager()

        self.manager.load_model(
            self.model_name
        )

    # -------------------------------------------------
    # Preprocessing
    # -------------------------------------------------

    def preprocess(
        self,
        state: Dict[str, Any],
    ) -> pd.DataFrame:
        """
        Convert the incoming boiler state into a model-ready DataFrame.
        """

        processed = {}

        for feature in self.features:

            processed[feature] = state.get(
                feature,
                0,
            )

        return pd.DataFrame(
            [processed],
            columns=self.features,
        )

    # -------------------------------------------------
    # Prediction
    # -------------------------------------------------

    def predict(
        self,
        processed_state: pd.DataFrame,
    ) -> float:
        """
        Predict the next boiler target value.
        """

        prediction = self.manager.predict(
            self.model_name,
            processed_state,
        )

        return float(prediction[0])

    # -------------------------------------------------
    # Post Processing
    # -------------------------------------------------

    def postprocess(
        self,
        prediction: float,
    ) -> Dict[str, float]:
        """
        Convert prediction into the standard forecast format.
        """

        return {
            self.target: round(prediction, 2),
        }

    # -------------------------------------------------
    # Forecast
    # -------------------------------------------------

    def forecast(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Generate a boiler forecast from the current state.
        """

        processed_state = self.preprocess(
            state,
        )

        prediction = self.predict(
            processed_state,
        )

        return self.postprocess(
            prediction,
        )

    # -------------------------------------------------
    # Model Information
    # -------------------------------------------------

    def model_info(
        self,
    ) -> Dict[str, Any]:
        """
        Return metadata about the forecasting model.
        """

        return {
            "module": "boiler",
            "model": self.model_name,
            "target": self.target,
            "features": self.features,
            "prediction_horizon": self.prediction_horizon,
        }