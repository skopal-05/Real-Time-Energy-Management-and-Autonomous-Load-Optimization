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


def generate_grid(periods: int = 10000) -> str:
    """
    Generate realistic grid connection data
    for approximately 35 days (5-minute interval).
    """

    start = datetime(2026, 7, 1, 0, 0)

    timestamps = timestamp_series(
        start,
        periods=periods,
        minutes=5,
    )

    frequency = 50.00
    voltage = 415.0
    power_factor = 0.96

    def make_row(index: int, timestamp: datetime) -> dict[str, object]:
        nonlocal frequency, voltage, power_factor

        demand_shape = 0.65 + daily_curve(index, peak=0.35)

        grid_import = (
            500 * demand_shape
            + random.uniform(-15, 15)
        )

        grid_export = max(
            0,
            40 * daily_curve(index, periods)
            + random.uniform(-3, 3),
        )

        # Stable frequency
        frequency += random.uniform(-0.005, 0.005)
        frequency = bounded(frequency, 49.90, 50.10)

        # Stable voltage
        voltage += random.uniform(-0.4, 0.4)
        voltage = bounded(voltage, 410, 424)

        # Slowly changing PF
        power_factor += random.uniform(-0.002, 0.002)
        power_factor = bounded(power_factor, 0.88, 0.99)

        # Time-of-day tariff
        hour = timestamp.hour

        if 18 <= hour < 22:
            tariff = 9.4          # Peak
        elif 10 <= hour < 18:
            tariff = 8.1
        elif 6 <= hour < 10:
            tariff = 7.2
        else:
            tariff = 6.5

        # Rare disturbance
        if random.random() < 0.005:
            frequency -= random.uniform(0.03, 0.08)
            voltage -= random.uniform(4, 8)

        return {
            "grid_import_kw": round(grid_import, 2),
            "grid_export_kw": round(grid_export, 2),
            "frequency_hz": round(frequency, 3),
            "voltage_v": round(voltage, 2),
            "power_factor": round(power_factor, 3),
            "tariff_inr_kwh": round(tariff, 2),
        }

    return str(
        write_csv(
            "grid.csv",
            build_rows(
                "grid_connection_1",
                timestamps,
                make_row,
            ),
        )
    )


if __name__ == "__main__":
    print(generate_grid())