"""
Common utility functions for AI Forecasting Module.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd


# ==========================================================
# Directories
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = ROOT_DIR / "models"
OUTPUT_DIR = ROOT_DIR / "outputs"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ==========================================================
# Time Utilities
# ==========================================================

def current_timestamp() -> str:
    """Return current timestamp."""

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def timestamp() -> str:
    """
    Alias for current_timestamp().
    """

    return current_timestamp()


def future_timestamp(
    minutes: int,
) -> str:
    """Return future timestamp."""

    return (

        datetime.now()

        + timedelta(minutes=minutes)

    ).strftime("%Y-%m-%d %H:%M:%S")


# ==========================================================
# Directory Utilities
# ==========================================================

def ensure_directory(
    path: Path | str,
) -> Path:

    path = Path(path)

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


# ==========================================================
# JSON Utilities
# ==========================================================

def save_json(
    data: Dict[str, Any],
    filepath: Path | str,
) -> None:

    filepath = Path(filepath)

    ensure_directory(
        filepath.parent,
    )

    with open(
        filepath,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )


def load_json(
    filepath: Path | str,
) -> Dict[str, Any]:

    filepath = Path(filepath)

    if not filepath.exists():

        raise FileNotFoundError(
            f"{filepath} not found."
        )

    with open(
        filepath,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ==========================================================
# CSV Utilities
# ==========================================================

def load_csv(
    filepath: Path | str,
) -> pd.DataFrame:

    filepath = Path(filepath)

    if not filepath.exists():

        raise FileNotFoundError(
            f"{filepath} not found."
        )

    return pd.read_csv(
        filepath,
    )


def save_csv(
    dataframe: pd.DataFrame,
    filepath: Path | str,
) -> None:

    filepath = Path(filepath)

    ensure_directory(
        filepath.parent,
    )

    dataframe.to_csv(
        filepath,
        index=False,
    )


# ==========================================================
# Model Utilities
# ==========================================================

def save_model(
    obj: Any,
    filename: str,
) -> Path:

    ensure_directory(
        MODEL_DIR,
    )

    filepath = MODEL_DIR / filename

    joblib.dump(
        obj,
        filepath,
    )

    return filepath


def load_model(
    filename: str,
) -> Any:

    filepath = MODEL_DIR / filename

    if not filepath.exists():

        raise FileNotFoundError(
            f"{filepath} not found."
        )

    return joblib.load(
        filepath,
    )


# ==========================================================
# Numeric Utilities
# ==========================================================

def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def normalize(
    value: float,
    minimum: float,
    maximum: float,
) -> float:

    if maximum == minimum:
        return 0.0

    return (

        value - minimum

    ) / (

        maximum - minimum

    )


def percentage_change(
    old: float,
    new: float,
) -> float:

    if old == 0:
        return 0.0

    return (

        (new - old)

        / old

    ) * 100


# ==========================================================
# Formatting
# ==========================================================

def round_values(
    data: Dict[str, Any],
    digits: int = 2,
) -> Dict[str, Any]:

    rounded: Dict[str, Any] = {}

    for key, value in data.items():

        if isinstance(
            value,
            (int, float, np.number),
        ):

            rounded[key] = round(
                float(value),
                digits,
            )

        else:

            rounded[key] = value

    return rounded


# ==========================================================
# Random Seed
# ==========================================================

def set_random_seed(
    seed: int = 42,
) -> int:

    random.seed(seed)

    np.random.seed(seed)

    return seed


# ==========================================================
# File Information
# ==========================================================

def file_exists(
    filepath: Path | str,
) -> bool:

    return Path(
        filepath,
    ).exists()


# ==========================================================
# Module Information
# ==========================================================

def info() -> Dict[str, Any]:

    return {

        "root_directory":
            str(ROOT_DIR),

        "model_directory":
            str(MODEL_DIR),

        "output_directory":
            str(OUTPUT_DIR),

        "generated_at":
            current_timestamp(),
    }