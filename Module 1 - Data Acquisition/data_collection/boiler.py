from __future__ import annotations

import random
from datetime import datetime

from synthetic_utils import bounded, build_rows, timestamp_series, write_csv


def generate_boiler(periods: int = 10000) -> str:
    """
    Generate realistic synthetic boiler data
    for approximately 35 days (5-minute interval).
    """

    start = datetime(2026, 7, 1, 0, 0)

    timestamps = timestamp_series(
        start,
        periods=periods,
        minutes=5,
    )

    pressure = 8.2
    efficiency = 84.5

    def make_row(index: int, _timestamp: datetime) -> dict[str, object]:
        nonlocal pressure, efficiency

        # Smooth pressure variation
        pressure += random.uniform(-0.05, 0.05)
        pressure = bounded(pressure, 7.2, 9.4)

        # Rare pressure spike
        if random.random() < 0.01:
            pressure = bounded(
                pressure + random.uniform(0.4, 0.8),
                7.2,
                9.4,
            )

        steam_flow = (
            1200
            + (pressure - 8.2) * 120
            + random.uniform(-25, 25)
        )

        fuel_flow = (
            82
            + steam_flow * 0.035
            + random.uniform(-1.5, 1.5)
        )

        feedwater_temperature = (
            86
            + random.uniform(-2, 2)
        )

        flue_gas_temperature = (
            185
            + (pressure - 8.2) * 8
            + random.uniform(-5, 5)
        )

        # Efficiency changes slowly
        efficiency += random.uniform(-0.05, 0.05)
        efficiency = bounded(efficiency, 79, 87)

        # Occasional efficiency drop (maintenance indicator)
        if random.random() < 0.01:
            efficiency -= random.uniform(2, 4)
            efficiency = bounded(efficiency, 75, 87)

        return {
            "steam_pressure_bar": round(pressure, 2),
            "steam_flow_kg_hr": round(steam_flow, 2),
            "fuel_flow_m3_hr": round(fuel_flow, 2),
            "feedwater_temperature_c": round(feedwater_temperature, 2),
            "flue_gas_temperature_c": round(flue_gas_temperature, 2),
            "efficiency_percent": round(efficiency, 2),
        }

    return str(
        write_csv(
            "boiler.csv",
            build_rows(
                "boiler_1",
                timestamps,
                make_row,
            ),
        )
    )


if __name__ == "__main__":
    print(generate_boiler())