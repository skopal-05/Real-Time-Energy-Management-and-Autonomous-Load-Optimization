"""
Future State Generator.
"""

from __future__ import annotations

from typing import Any, Dict

from infrastructure import (
    BatteryForecast,
    BoilerForecast,
    CompressorForecast,
    GridForecast,
    HVACForecast,
)

from production import ProductionForecast
from renewable import SolarForecast


class FutureStateGenerator:
    """
    Generate the future system state using all forecasting models.
    """

    def __init__(self) -> None:

        self.production = ProductionForecast()

        self.boiler = BoilerForecast()

        self.compressor = CompressorForecast()

        self.hvac = HVACForecast()

        self.battery = BatteryForecast()

        self.grid = GridForecast()

        self.solar = SolarForecast()

    # -------------------------------------------------
    # Individual Forecasts
    # -------------------------------------------------

    def production_forecast(
        self,
        current_state: Dict[str, Any],
    ) -> Dict[str, Any]:

        return self.production.forecast(
            current_state,
        )

    def boiler_forecast(
        self,
        current_state: Dict[str, Any],
    ) -> Dict[str, Any]:

        return self.boiler.forecast(
            current_state,
        )

    def compressor_forecast(
        self,
        current_state: Dict[str, Any],
    ) -> Dict[str, Any]:

        return self.compressor.forecast(
            current_state,
        )

    def hvac_forecast(
        self,
        current_state: Dict[str, Any],
    ) -> Dict[str, Any]:

        return self.hvac.forecast(
            current_state,
        )

    def battery_forecast(
        self,
        current_state: Dict[str, Any],
    ) -> Dict[str, Any]:

        return self.battery.forecast(
            current_state,
        )

    def grid_forecast(
        self,
        current_state: Dict[str, Any],
    ) -> Dict[str, Any]:

        return self.grid.forecast(
            current_state,
        )

    def solar_forecast(
        self,
        current_state: Dict[str, Any],
    ) -> Dict[str, Any]:

        return self.solar.forecast(
            current_state,
        )

    # -------------------------------------------------
    # Future State
    # -------------------------------------------------

    def generate(
        self,
        current_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a combined future state.
        """

        future_state: Dict[str, Any] = {}

        future_state.update(
            self.production_forecast(current_state)
        )

        future_state.update(
            self.boiler_forecast(current_state)
        )

        future_state.update(
            self.compressor_forecast(current_state)
        )

        future_state.update(
            self.hvac_forecast(current_state)
        )

        future_state.update(
            self.battery_forecast(current_state)
        )

        future_state.update(
            self.grid_forecast(current_state)
        )

        future_state.update(
            self.solar_forecast(current_state)
        )

        return future_state