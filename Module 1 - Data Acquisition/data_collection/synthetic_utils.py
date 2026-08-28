from __future__ import annotations

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

# ==========================================================
# Project Paths
# ==========================================================

# Current directory (data_collection/)
CURRENT_DIR = Path(__file__).resolve().parent

# Project root (Module 1 - Data Acquisition/)
PROJECT_DIR = CURRENT_DIR.parent

# Output directories
OUTPUT_DIR = PROJECT_DIR / "outputs"
CLEANED_DIR = OUTPUT_DIR / "cleaned_data"
LOG_DIR = OUTPUT_DIR / "logs"

# Create output directories if they do not exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CLEANED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================================
# Global Configuration
# ==========================================================

# Sampling interval used across the project
SAMPLING_INTERVAL_MINUTES = 15

# Number of readings generated in one day
PERIODS_PER_DAY = (24 * 60) // SAMPLING_INTERVAL_MINUTES


# ==========================================================
# Time Utilities
# ==========================================================

def timestamp_series(
    start: datetime,
    periods: int,
    minutes: int = SAMPLING_INTERVAL_MINUTES,
) -> list[datetime]:
    """
    Generate sequential timestamps.

    Parameters
    ----------
    start : datetime
        Starting timestamp.

    periods : int
        Number of timestamps.

    minutes : int
        Time interval between consecutive timestamps.
    """

    return [
        start + timedelta(minutes=i * minutes)
        for i in range(periods)
    ]


def daily_curve(
    index: int,
    peak: float = 0.5,
) -> float:
    """
    Generate a smooth sinusoidal daily load profile.

    The curve repeats every day irrespective of
    the total dataset length.
    """

    angle = (
        2
        * math.pi
        * (index % PERIODS_PER_DAY)
        / PERIODS_PER_DAY
    )

    return peak * (math.sin(angle - math.pi / 2) + 1) / 2


# ==========================================================
# Dataset Builder
# ==========================================================

def build_rows(
    system_id: str,
    timestamps: list[datetime],
    make_row: Callable[[int, datetime], dict[str, object]],
) -> list[dict[str, object]]:
    """
    Build complete dataset rows by combining
    timestamps with generated sensor values.
    """

    rows = []

    for index, timestamp in enumerate(timestamps):

        row = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "system_id": system_id,
        }

        row.update(make_row(index, timestamp))
        rows.append(row)

    return rows


# ==========================================================
# CSV Writer
# ==========================================================

def write_csv(
    filename: str,
    rows: list[dict[str, object]],
) -> Path:
    """
    Save generated sensor data as a CSV file.
    """

    if not rows:
        raise ValueError("No rows available to write.")

    filepath = OUTPUT_DIR / filename

    with open(
        filepath,
        "w",
        newline="",
        encoding="utf-8",
    ) as csvfile:

        writer = csv.DictWriter(
            csvfile,
            fieldnames=rows[0].keys(),
        )

        writer.writeheader()
        writer.writerows(rows)

    return filepath


# ==========================================================
# Numeric Utilities
# ==========================================================

def bounded(
    value: float,
    low: float,
    high: float,
) -> float:
    """
    Restrict a value within a specified range.
    """

    return max(low, min(value, high))


def random_walk(
    start: float,
    periods: int,
    step: float = 1.0,
    low: float | None = None,
    high: float | None = None,
) -> list[float]:
    """
    Generate a bounded random walk.

    Useful for slowly varying sensor values like:
        - Temperature
        - Pressure
        - Voltage
        - State of Charge
    """

    values = [round(start, 2)]

    for _ in range(periods - 1):

        next_value = values[-1] + random.uniform(-step, step)

        if low is not None:
            next_value = max(low, next_value)

        if high is not None:
            next_value = min(high, next_value)

        values.append(round(next_value, 2))

    return values