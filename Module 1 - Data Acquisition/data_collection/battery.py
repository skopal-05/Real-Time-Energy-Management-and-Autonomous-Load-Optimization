from __future__ import annotations

import random
from datetime import datetime

from synthetic_utils import bounded, build_rows, timestamp_series, write_csv


def generate_battery(periods: int = 10000) -> str:
    """
    Generate realistic synthetic battery storage data
    for approximately 35 days (5-minute interval).
    """

    start = datetime(2026, 7, 1, 0, 0)

    # 5-minute sampling interval
    timestamps = timestamp_series(
        start,
        periods=periods,
        minutes=5,
    )

    state_of_charge = 62.0
    power_kw = 25.0

    def make_row(index: int, _timestamp: datetime) -> dict[str, object]:
        nonlocal state_of_charge, power_kw

        # Smooth variation instead of completely random values
        power_kw += random.uniform(-5, 5)
        power_kw = bounded(power_kw, -75, 90)

        # Occasionally simulate heavy charging/discharging
        if random.random() < 0.01:
            power_kw = random.choice([
                random.uniform(60, 90),
                random.uniform(-75, -50),
            ])

        # Update battery charge
        state_of_charge = bounded(
            state_of_charge + power_kw * 0.004,
            15,
            95,
        )

        voltage = 690 + random.uniform(-5, 5)

        current = power_kw * 1000 / voltage

        temperature = (
            30
            + abs(power_kw) * 0.03
            + random.uniform(-0.7, 0.7)
        )

        return {
            "state_of_charge_percent": round(state_of_charge, 2),
            "battery_power_kw": round(power_kw, 2),
            "voltage_v": round(voltage, 2),
            "current_a": round(current, 2),
            "temperature_c": round(temperature, 2),
            "mode": "charging" if power_kw >= 0 else "discharging",
        }

    return str(
        write_csv(
            "battery_storage.csv",
            build_rows(
                "battery_storage_1",
                timestamps,
                make_row,
            ),
        )
    )


if __name__ == "__main__":
    print(generate_battery())