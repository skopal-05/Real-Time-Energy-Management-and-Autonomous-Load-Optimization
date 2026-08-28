"""
Feature preprocessing for AI Forecasting Module.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from common.model_manager import ModelManager


class FeatureBuilder:
    """
    Prepares sensor data for machine learning models.

    Responsibilities
    ----------------
    - Remove unnecessary columns
    - Handle missing values
    - Encode categorical features
    - Return ordered DataFrame
    """

    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
    ) -> None:

        self.model_manager = model_manager

    # =====================================================
    # Internal Helpers
    # =====================================================

    def _encode_value(
        self,
        column: str,
        value: Any,
        encoder_mapping: Dict[str, str],
    ) -> Any:

        if (
            self.model_manager is None
            or column not in encoder_mapping
        ):
            return value

        encoder_name = encoder_mapping[column]

        return self.model_manager.transform(
            encoder_name,
            [value],
        )[0]

    # =====================================================
    # Build Features
    # =====================================================

    def build(
        self,
        sensor_data: Dict[str, Any],
        feature_columns: List[str],
        encoder_mapping: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:

        encoder_mapping = encoder_mapping or {}

        processed: Dict[str, Any] = {}

        for column in feature_columns:

            value = sensor_data.get(column, 0)

            if value is None:
                value = 0

            value = self._encode_value(
                column,
                value,
                encoder_mapping,
            )

            processed[column] = value

        return pd.DataFrame(
            [processed],
            columns=feature_columns,
        )

    # =====================================================
    # Select Features
    # =====================================================

    @staticmethod
    def select(
        dataframe: pd.DataFrame,
        feature_columns: List[str],
    ) -> pd.DataFrame:

        return dataframe[
            feature_columns
        ].copy()

    # =====================================================
    # Drop Columns
    # =====================================================

    @staticmethod
    def drop(
        dataframe: pd.DataFrame,
        columns: List[str],
    ) -> pd.DataFrame:

        return dataframe.drop(
            columns=columns,
            errors="ignore",
        )

    # =====================================================
    # Fill Missing Values
    # =====================================================

    @staticmethod
    def fill_missing(
        dataframe: pd.DataFrame,
        value: Any = 0,
    ) -> pd.DataFrame:

        return dataframe.fillna(value)

    # =====================================================
    # Feature Names
    # =====================================================

    @staticmethod
    def feature_names(
        dataframe: pd.DataFrame,
    ) -> List[str]:

        return list(dataframe.columns)

    # =====================================================
    # Shape
    # =====================================================

    @staticmethod
    def shape(
        dataframe: pd.DataFrame,
    ) -> tuple[int, int]:

        return dataframe.shape

    # =====================================================
    # Information
    # =====================================================

    def info(
        self,
    ) -> Dict[str, Any]:

        return {

            "builder": "FeatureBuilder",

            "handles_missing_values": True,

            "handles_encoding": (
                self.model_manager is not None
            ),

            "returns": "pandas.DataFrame",
        }

    # =====================================================
    # Magic Methods
    # =====================================================

    def __str__(
        self,
    ) -> str:

        return (
            "FeatureBuilder("
            "Data Cleaning + Encoding)"
        )