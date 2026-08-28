from __future__ import annotations

import random
from datetime import datetime

from synthetic_utils import (
    bounded,
    build_rows,
    daily_curve,
    timestamp_series,
    write_csv,
)


def generate_solar(periods: int = 10000) -> str:
    """
    Generate realistic solar plant data
    for approximately 35 days (5-minute interval).
    """

    start = datetime(2026, 7, 1, 0, 0)

    timestamps = timestamp_series(
        start,
        periods=periods,
        minutes=5,
    )

    inverter_efficiency = 0.965

    def make_row(index: int, timestamp: datetime) -> dict[str, object]:
        nonlocal inverter_efficiency

        hour = timestamp.hour

        # Sunlight profile
        if 6 <= hour <= 18:
            sun = daily_curve(index, peak=1.0)
        else:
            sun = 0

        irradiance = max(
            0,
            950 * sun + random.uniform(-20, 20)
        )

        # Occasional cloud event
        if random.random() < 0.02:
            irradiance *= random.uniform(0.4, 0.8)

        panel_temperature = (
            28
            + sun * 24
            + random.uniform(-1, 1)
        )

        # Efficiency decreases slightly at high temperature
        temperature_factor = max(
            0.88,
            1 - (panel_temperature - 25) * 0.003,
        )

        dc_power = (
            irradiance
            * 0.42
            * temperature_factor
        )

        inverter_efficiency += random.uniform(-0.001, 0.001)
        inverter_efficiency = bounded(
            inverter_efficiency,
            0.94,
            0.98,
        )

        inverter_power = (
            dc_power
            * inverter_efficiency
        )

        return {
            "irradiance_w_m2": round(irradiance, 2),
            "dc_power_kw": round(dc_power, 2),
            "inverter_power_kw": round(inverter_power, 2),
            "panel_temperature_c": round(panel_temperature, 2),
            "inverter_status": (
                "online"
                if irradiance > 25
                else "standby"
            ),
        }

    return str(
        write_csv(
            "solar_plant.csv",
            build_rows(
                "solar_plant_1",
                timestamps,
                make_row,
            ),
        )
    )


if __name__ == "__main__":
    print(generate_solar())