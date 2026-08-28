"""Shared helpers for turning module artifacts into frontend payloads.

Rule for every mapper in this package: never invent a number. When a module did
not produce a value, emit ``null`` and let the UI render its "unavailable"
state - which it already has for every field typed as nullable.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping, Sequence


def iso(value: Any) -> str | None:
    """Normalise a timestamp from Module 1's CSV format to ISO-8601 UTC."""

    if value in (None, ""):
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def shift_iso(base: str | None, minutes: float) -> str | None:
    if base is None:
        return None
    try:
        parsed = datetime.fromisoformat(base.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (
        (parsed + timedelta(minutes=minutes))
        .astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def number(source: Mapping[str, Any] | None, key: str) -> float | None:
    """Read a finite float, or ``None`` when the value is missing or unusable."""

    if not isinstance(source, Mapping) or key not in source:
        return None
    raw = source[key]
    if isinstance(raw, bool) or raw is None or raw == "":
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def rounded(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits)


def total(values: Iterable[float | None]) -> float:
    return sum(value for value in values if value is not None)


def mean(values: Sequence[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return sum(present) / len(present) if present else None


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def percent(part: float | None, whole: float | None) -> float | None:
    """Part as a percentage of whole, or ``None`` when it cannot be computed."""

    if part is None or whole is None or whole == 0:
        return None
    return round(part / whole * 100, 1)


def accuracy(pairs: Sequence[tuple[float, float]]) -> dict[str, Any]:
    """Regression metrics over (actual, predicted) pairs.

    Returns the frontend's ``ForecastAccuracy`` shape. With no usable pairs
    every metric is ``null`` rather than zero.
    """

    usable = [
        (a, p)
        for a, p in pairs
        if a is not None and p is not None and math.isfinite(a) and math.isfinite(p)
    ]
    if not usable:
        return {
            "mae": None,
            "rmse": None,
            "r2": None,
            "mapePct": None,
            "sampleCount": 0,
            "evaluatedAt": None,
        }

    count = len(usable)
    errors = [a - p for a, p in usable]
    mae = sum(abs(e) for e in errors) / count
    rmse = math.sqrt(sum(e * e for e in errors) / count)

    actual_mean = sum(a for a, _ in usable) / count
    ss_tot = sum((a - actual_mean) ** 2 for a, _ in usable)
    ss_res = sum(e * e for e in errors)
    r2 = (1 - ss_res / ss_tot) if ss_tot > 0 else None

    absolute = [(abs(a - p) / abs(a)) for a, p in usable if a != 0]
    mape = (sum(absolute) / len(absolute) * 100) if absolute else None

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4) if r2 is not None else None,
        "mapePct": round(mape, 3) if mape is not None else None,
        "sampleCount": count,
        "evaluatedAt": now_iso(),
    }


def trend_of(change_pct: float | None, threshold: float = 1.0) -> str:
    if change_pct is None:
        return "flat"
    if change_pct > threshold:
        return "up"
    if change_pct < -threshold:
        return "down"
    return "flat"


def severity_from_score(score: float, threshold: float) -> str:
    """Map an anomaly score above a threshold onto a severity band."""

    if threshold <= 0:
        return "medium"
    excess = (score - threshold) / threshold
    if excess >= 0.35:
        return "critical"
    if excess >= 0.18:
        return "high"
    if excess >= 0.05:
        return "medium"
    return "low"


def title_case(identifier: str) -> str:
    """``battery_management_agent`` -> ``Battery Management Agent``."""

    return " ".join(part.capitalize() for part in identifier.replace("-", "_").split("_"))
