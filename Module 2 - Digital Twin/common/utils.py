import json
import logging
from pathlib import Path
from datetime import datetime


def current_timestamp() -> str:
    """
    Returns the current timestamp in ISO format.
    """
    return datetime.now().isoformat()


def setup_logger(name: str) -> logging.Logger:
    """
    Creates and returns a logger.
    """

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


def save_json(data: dict, filepath):
    """
    Save dictionary as JSON.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def load_json(filepath: str) -> dict:
    """
    Load JSON file.
    """
    with open(filepath, "r") as f:
        return json.load(f)