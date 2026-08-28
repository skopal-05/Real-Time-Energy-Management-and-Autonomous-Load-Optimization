"""
Load Forecast Integration Module.
"""

from __future__ import annotations

from typing import Any, Dict


class LoadForecast:
    """
    Calculate plant energy statistics
    from the generated future state.
    """

    def __init__(self) -> None:
        pass

    # -------------------------------------------------
    # Plant Electrical Load
    # -------------------------------------------------

    def calculate_total_load(
        self,
        future_state: Dict[str, Any],
    ) -> float:
        """
        Calculate total electrical load.
        """

        compressor_power = future_state.get(
            "compressor_power_kw",
            0,
        )

        hvac_power = future_state.get(
            "hvac_power_kw",
            0,
        )

        total_load = (
            compressor_power
            + hvac_power
        )

        return round(
            total_load,
            2,
        )

    # -------------------------------------------------
    # Renewable Generation
    # -------------------------------------------------

    def renewable_generation(
        self,
        future_state: Dict[str, Any],
    ) -> float:

        solar = future_state.get(
            "inverter_power_kw",
            0,
        )

        battery = future_state.get(
            "battery_power_kw",
            0,
        )

        return round(
            solar + battery,
            2,
        )

    # -------------------------------------------------
    # Grid Import
    # -------------------------------------------------

    def grid_import(
        self,
        future_state: Dict[str, Any],
    ) -> float:

        return round(
            future_state.get(
                "grid_import_kw",
                0,
            ),
            2,
        )

    # -------------------------------------------------
    # Boiler Fuel
    # -------------------------------------------------

    def boiler_fuel(
        self,
        future_state: Dict[str, Any],
    ) -> float:

        return round(
            future_state.get(
                "fuel_flow_m3_hr",
                0,
            ),
            2,
        )

    # -------------------------------------------------
    # Forecast
    # -------------------------------------------------

    def forecast(
        self,
        future_state: Dict[str, Any],
    ) -> Dict[str, Any]:

        total_load = self.calculate_total_load(
            future_state,
        )

        renewable = self.renewable_generation(
            future_state,
        )

        grid = self.grid_import(
            future_state,
        )

        boiler = self.boiler_fuel(
            future_state,
        )

        return {

            "total_load_kw": total_load,

            "renewable_generation_kw": renewable,

            "grid_import_kw": grid,

            "boiler_fuel_flow_m3_hr": boiler,
        }