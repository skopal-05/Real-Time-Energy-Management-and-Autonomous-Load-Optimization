"""
Production Forecast Integration Module.
"""

from __future__ import annotations

from typing import Any, Dict

from production.production_forecast import ProductionForecast


class ProductionForecastIntegration:
    """
    Integration wrapper for the Production Forecast module.
    """

    def __init__(self) -> None:
        self.forecaster = ProductionForecast()

    def forecast(
        self,
        current_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate production forecast from the current system state.
        """

        return self.forecaster.forecast(current_state)

    def model_info(
        self,
    ) -> Dict[str, Any]:
        """
        Return information about the production forecasting model.
        """

        return self.forecaster.model_info()