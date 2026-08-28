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


def generate_production_line(
    line_id: str,
    periods: int = 10000,
) -> str:
    """
    Generate realistic production line data
    for approximately 35 days (5-minute interval).
    """

    start = datetime(2026, 7, 1, 0, 0)

    timestamps = timestamp_series(
        start,
        periods=periods,
        minutes=5,
    )

    machine_load = 110.0
    motor_temperature = 52.0
    vibration = 1.5

    def make_row(index: int, timestamp: datetime) -> dict[str, object]:
        nonlocal machine_load, motor_temperature, vibration

        hour = timestamp.hour

        # Daily production profile
        load_factor = 0.45 + daily_curve(index, peak=0.55)

        # Working hours
        if 8 <= hour < 18:
            load_factor += 0.15

        # Machine load changes smoothly
        machine_load += random.uniform(-2, 2)
        machine_load = bounded(machine_load, 90, 140)

        effective_load = machine_load * load_factor

        units_per_hour = (
            effective_load * 0.82
            + random.uniform(-3, 3)
        )

        # Temperature depends on machine load
        motor_temperature += (
            (effective_load / 100) * 0.08
            + random.uniform(-0.25, 0.25)
        )

        motor_temperature = bounded(
            motor_temperature,
            40,
            85,
        )

        # Vibration changes gradually
        vibration += random.uniform(-0.03, 0.03)
        vibration = bounded(
            vibration,
            1.0,
            3.8,
        )

        # Rare overload / maintenance event
        if random.random() < 0.01:
            effective_load += random.uniform(10, 20)
            motor_temperature += random.uniform(5, 10)
            vibration += random.uniform(0.5, 1.2)

            vibration = bounded(vibration, 1.0, 5.0)

        return {
            "units_per_hour": round(units_per_hour, 2),
            "machine_load_kw": round(effective_load, 2),
            "motor_temperature_c": round(motor_temperature, 2),
            "vibration_mm_s": round(vibration, 3),
            "status": "running" if units_per_hour > 40 else "idle",
        }

    filename = f"{line_id.lower()}_production.csv"

    return str(
        write_csv(
            filename,
            build_rows(
                line_id,
                timestamps,
                make_row,
            ),
        )
    )


if __name__ == "__main__":
    for system in (
        "production_line_a",
        "production_line_b",
    ):
        print(generate_production_line(system))