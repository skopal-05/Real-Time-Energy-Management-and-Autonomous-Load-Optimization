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


def generate_compressor(
    system_id: str = "compressor",
    periods: int = 10000,
) -> str:
    """
    Generate realistic compressor data
    for approximately 35 days (5-minute interval).
    """

    start = datetime(2026, 7, 1, 0, 0)

    timestamps = timestamp_series(
        start,
        periods=periods,
        minutes=5,
    )

    air_pressure = 8.0
    efficiency = 95.0
    vibration = 1.2

    def make_row(index: int, _timestamp: datetime) -> dict[str, object]:
        nonlocal air_pressure, efficiency, vibration

        load_factor = 0.35 + daily_curve(index, peak=0.55)

        # Smooth pressure variation
        air_pressure += random.uniform(-0.03, 0.03)
        air_pressure = bounded(air_pressure, 6.8, 9.5)

        air_flow = (
            120 * load_factor
            + random.uniform(-5, 5)
        )

        power = (
            60 * load_factor
            + random.uniform(-2, 2)
        )

        motor_temperature = (
            42
            + power * 0.28
            + random.uniform(-1, 1)
        )

        vibration += random.uniform(-0.03, 0.03)
        vibration = bounded(vibration, 0.8, 3.5)

        efficiency += random.uniform(-0.02, 0.02)
        efficiency = bounded(efficiency, 85, 98)

        # Rare anomaly (maintenance scenario)
        if random.random() < 0.01:
            vibration += random.uniform(0.5, 1.2)
            vibration = bounded(vibration, 0.8, 5.0)

            motor_temperature += random.uniform(8, 15)

            efficiency -= random.uniform(2, 5)
            efficiency = bounded(efficiency, 80, 98)

        return {
            "air_flow_m3_min": round(air_flow, 2),
            "air_pressure_bar": round(air_pressure, 2),
            "power_kw": round(power, 2),
            "motor_temperature_c": round(motor_temperature, 2),
            "vibration_mm_s": round(vibration, 3),
            "efficiency_percent": round(efficiency, 2),
            "status": "running" if air_flow > 35 else "idle",
        }

    return str(
        write_csv(
            "compressor.csv",
            build_rows(
                system_id,
                timestamps,
                make_row,
            ),
        )
    )


if __name__ == "__main__":
    print(generate_compressor())