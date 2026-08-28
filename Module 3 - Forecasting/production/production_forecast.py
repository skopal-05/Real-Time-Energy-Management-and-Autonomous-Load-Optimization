"""
Production Forecasting Module.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from common.config import MODULE_CONFIG
from common.forecasting_base import ForecastingBase
from common.model_manager import ModelManager


class ProductionForecast(ForecastingBase):
    """
    Forecast production output using the trained Random Forest model.
    """

    def __init__(self) -> None:

        config = MODULE_CONFIG["production"]

        super().__init__(
            model_name=config["model"],
            prediction_horizon=1,
        )

        self.config = config

        self.features = config["features"]

        self.target = config["target"]

        self.encoders = config["encoders"]

        self.manager = ModelManager()

        if not self.manager.load_model(self.model_name):
            raise FileNotFoundError(
                f"Model '{self.model_name}' not found."
            )

        for _, encoder_name in self.encoders.items():

            self.manager.load_encoder(
                encoder_name,
            )

    # -------------------------------------------------
    # Preprocessing
    # -------------------------------------------------

    def preprocess(
        self,
        state: Dict[str, Any],
    ) -> pd.DataFrame:
        """
        Convert the incoming production state into a model-ready DataFrame.
        """

        processed = {}

        for feature in self.features:

            value = state.get(feature, 0)

            if value is None:
                value = 0

            if feature in self.encoders:

                encoder = self.manager.encoders[
                    self.encoders[feature]
                ]

                value = encoder.transform(
                    [value]
                )[0]

            processed[feature] = value

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
        Predict the next production output.
        """

        prediction = self.manager.predict(
            self.model_name,
            processed_state,
        )

        return float(
            prediction[0]
        )

    # -------------------------------------------------
    # Post Processing
    # -------------------------------------------------

    def postprocess(
        self,
        prediction: float,
    ) -> Dict[str, Any]:
        """
        Convert prediction into the standard forecast format.
        """

        return {
            self.target: round(
                prediction,
                2,
            )
        }

    # -------------------------------------------------
    # Forecast
    # -------------------------------------------------

    def forecast(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a production forecast from the current state.
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
            "module": "production",
            "model": self.model_name,
            "target": self.target,
            "features": self.features,
            "prediction_horizon": self.prediction_horizon,
        }