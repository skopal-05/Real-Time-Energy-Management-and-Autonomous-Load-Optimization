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


def generate_hvac(
    system_id: str = "hvac",
    periods: int = 10000,
) -> str:
    """
    Generate realistic HVAC data
    for approximately 35 days (5-minute interval).
    """

    start = datetime(2026, 7, 1, 0, 0)

    timestamps = timestamp_series(
        start,
        periods=periods,
        minutes=5,
    )

    room_temperature = 23.5
    humidity = 52.0
    efficiency = 95.0
    setpoint = 23

    def make_row(index: int, timestamp: datetime) -> dict[str, object]:
        nonlocal room_temperature, humidity, efficiency, setpoint

        hour = timestamp.hour

        # Occupancy/load profile
        load_factor = 0.40 + daily_curve(index, peak=0.60)

        # Office timing -> slightly higher HVAC demand
        if 9 <= hour < 18:
            load_factor += 0.15

        power = (
            20 * load_factor
            + random.uniform(-0.8, 0.8)
        )

        airflow = (
            1600 * load_factor
            + random.uniform(-40, 40)
        )

        # Operator changes setpoint occasionally
        if index % 288 == 0:
            setpoint = random.choice([22, 23, 24])

        # Temperature slowly follows setpoint
        room_temperature += (
            (setpoint - room_temperature) * 0.05
            + random.uniform(-0.15, 0.15)
        )

        room_temperature = bounded(
            room_temperature,
            19,
            29,
        )

        # Humidity changes gradually
        humidity += random.uniform(-0.3, 0.3)
        humidity = bounded(humidity, 40, 65)

        # Efficiency changes slowly
        efficiency += random.uniform(-0.02, 0.02)
        efficiency = bounded(efficiency, 85, 98)

        # Rare maintenance scenario
        if random.random() < 0.01:
            room_temperature += random.uniform(2, 4)
            power += random.uniform(3, 6)
            efficiency -= random.uniform(2, 5)

            room_temperature = bounded(room_temperature, 19, 35)
            efficiency = bounded(efficiency, 80, 98)

        return {
            "power_kw": round(power, 2),
            "temperature_c": round(room_temperature, 2),
            "airflow_m3_min": round(airflow, 2),
            "humidity_percent": round(humidity, 2),
            "setpoint_temperature_c": setpoint,
            "efficiency_percent": round(efficiency, 2),
            "status": "running" if power > 5 else "idle",
        }

    return str(
        write_csv(
            "hvac.csv",
            build_rows(
                system_id,
                timestamps,
                make_row,
            ),
        )
    )


if __name__ == "__main__":
    print(generate_hvac())