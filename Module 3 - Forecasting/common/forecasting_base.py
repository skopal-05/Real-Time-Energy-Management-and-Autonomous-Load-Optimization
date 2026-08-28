"""
Base class for AI Forecasting models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from common.utils import (
    current_timestamp,
    round_values,
)


class ForecastingBase(ABC):
    """
    Base class for all AI forecasting modules.

    Pipeline
    --------
    preprocess()
        ↓
    predict()
        ↓
    postprocess()
    """

    def __init__(
        self,
        model_name: str,
        prediction_horizon: int = 60,
    ) -> None:

        self.model_name = model_name
        self.prediction_horizon = prediction_horizon

    # =====================================================
    # Abstract Methods
    # =====================================================

    @abstractmethod
    def preprocess(
        self,
        sensor_data: Dict[str, Any],
    ) -> Any:
        """
        Convert raw sensor data into
        model-ready input.
        """
        pass

    @abstractmethod
    def predict(
        self,
        processed_data: Any,
    ) -> Dict[str, Any]:
        """
        Run AI prediction.
        """
        pass

    # =====================================================
    # Post Processing
    # =====================================================

    def postprocess(
        self,
        prediction: Dict[str, Any],
    ) -> Dict[str, Any]:

        result = round_values(
            prediction,
        )

        result["model"] = self.model_name

        result["prediction_horizon"] = (
            self.prediction_horizon
        )

        result["timestamp"] = (
            current_timestamp()
        )

        return result

    # =====================================================
    # Forecast Pipeline
    # =====================================================

    def forecast(
        self,
        sensor_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Complete forecasting pipeline.
        """

        processed_data = self.preprocess(
            sensor_data,
        )

        prediction = self.predict(
            processed_data,
        )

        return self.postprocess(
            prediction,
        )

    # =====================================================
    # Configuration
    # =====================================================

    def set_prediction_horizon(
        self,
        minutes: int,
    ) -> None:

        self.prediction_horizon = minutes

    def get_prediction_horizon(
        self,
    ) -> int:

        return self.prediction_horizon

    # =====================================================
    # Information
    # =====================================================

    def info(
        self,
    ) -> Dict[str, Any]:

        return {

            "model_name":
                self.model_name,

            "prediction_horizon":
                self.prediction_horizon,
        }

    # =====================================================
    # Magic Methods
    # =====================================================

    def __str__(
        self,
    ) -> str:

        return (
            f"{self.__class__.__name__}"
            f"({self.model_name})"
        )

    def __repr__(
        self,
    ) -> str:

        return (

            f"{self.__class__.__name__}("

            f"model_name='{self.model_name}', "

            f"prediction_horizon="
            f"{self.prediction_horizon})"

        )