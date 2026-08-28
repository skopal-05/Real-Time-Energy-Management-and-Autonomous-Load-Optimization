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


def generate_weather(periods: int = 10000) -> str:
    """
    Generate realistic weather data for approximately
    100 days at a 15-minute sampling interval.
    """

    start = datetime(2026, 7, 1, 0, 0)

    timestamps = timestamp_series(
        start,
        periods=periods,
    )

    # Initial weather conditions
    ambient_temperature = 28.0
    humidity = 65.0
    wind_speed = 3.5
    cloud_cover = 25.0

    def make_row(index: int, timestamp: datetime) -> dict[str, object]:
        nonlocal ambient_temperature, humidity, wind_speed, cloud_cover

        # Daily sunlight profile
        sun = daily_curve(index, peak=1.0)

        # Temperature gradually follows sunlight
        target_temperature = 25 + sun * 10
        ambient_temperature += (
            (target_temperature - ambient_temperature) * 0.08
            + random.uniform(-0.15, 0.15)
        )
        ambient_temperature = bounded(
            ambient_temperature,
            22,
            38,
        )

        # Humidity decreases as sunlight increases
        target_humidity = 72 - sun * 25
        humidity += (
            (target_humidity - humidity) * 0.08
            + random.uniform(-0.4, 0.4)
        )
        humidity = bounded(
            humidity,
            35,
            90,
        )

        # Wind speed changes gradually
        wind_speed += random.uniform(-0.15, 0.15)
        wind_speed = bounded(
            wind_speed,
            1,
            8,
        )

        # Cloud cover changes gradually
        cloud_cover += random.uniform(-2, 2)
        cloud_cover = bounded(
            cloud_cover,
            0,
            100,
        )

        # Rare cloudy weather event
        if random.random() < 0.02:
            cloud_cover = bounded(
                cloud_cover + random.uniform(20, 45),
                0,
                100,
            )

        # Solar irradiance depends on sunlight and cloud cover
        irradiance = (
            920
            * sun
            * (1 - cloud_cover / 120)
            + random.uniform(-15, 15)
        )

        irradiance = max(0, irradiance)

        return {
            "ambient_temperature_c": round(ambient_temperature, 2),
            "humidity_percent": round(humidity, 2),
            "wind_speed_m_s": round(wind_speed, 2),
            "cloud_cover_percent": round(cloud_cover, 2),
            "global_irradiance_w_m2": round(irradiance, 2),
        }

    return str(
        write_csv(
            "weather.csv",
            build_rows(
                "weather_station_1",
                timestamps,
                make_row,
            ),
        )
    )


if __name__ == "__main__":
    print(generate_weather())