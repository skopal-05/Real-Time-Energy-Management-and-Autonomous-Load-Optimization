"""
Run Forecasting Pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from integration.future_state_generator import FutureStateGenerator
from integration.load_forecast import LoadForecast


OUTPUT_DIRECTORY = Path("outputs")
OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIRECTORY / "forecast_output.json"


def save_forecast(
    forecast: Dict[str, Any],
) -> None:
    """
    Save forecast results to a JSON file.
    """

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            forecast,
            file,
            indent=4,
        )


def main() -> None:
    """
    Execute the complete forecasting pipeline.
    """

    # -------------------------------------------------
    # Example Current State
    # Replace this with Digital Twin state in integration.
    # -------------------------------------------------

    current_state = {

    # ---------------- Production ----------------

    "machine_load_kw": 85,
    "motor_temperature_c": 68,
    "vibration_mm_s": 1.9,
    "status": "running",

    # ---------------- Boiler ----------------

    "steam_pressure_bar": 12,
    "feedwater_temperature_c": 88,
    "flue_gas_temperature_c": 180,
    "efficiency_percent": 92,

    # ---------------- Compressor ----------------

    "air_pressure_bar": 7,

    # ---------------- HVAC ----------------

    "temperature_c": 24,
    "airflow_m3_min": 350,
    "humidity_percent": 55,
    "setpoint_temperature_c": 22,

    # ---------------- Battery ----------------

    "voltage_v": 410,
    "current_a": 36,
    "mode": "charging",
    "state_of_charge_percent": 72,

    # ---------------- Grid ----------------

    "grid_export_kw": 5,
    "frequency_hz": 50,
    "power_factor": 0.98,
    "tariff_inr_kwh": 8.5,

    # ---------------- Solar ----------------

    "irradiance_w_m2": 900,
    "panel_temperature_c": 38,
    "inverter_status": "online",
}

    # -------------------------------------------------
    # Generate Future State
    # -------------------------------------------------

    generator = FutureStateGenerator()

    future_state = generator.generate(
        current_state,
    )

    # -------------------------------------------------
    # Calculate Load Forecast
    # -------------------------------------------------

    load_forecast = LoadForecast()

    energy_forecast = load_forecast.forecast(
        future_state,
    )

    # -------------------------------------------------
    # Merge Results
    # -------------------------------------------------

    forecast = {
        "future_state": future_state,
        "energy_forecast": energy_forecast,
    }

    # -------------------------------------------------
    # Save Output
    # -------------------------------------------------

    save_forecast(
        forecast,
    )

    print(
        json.dumps(
            forecast,
            indent=4,
        )
    )


if __name__ == "__main__":
    main()