"""Module 2 twin state -> the frontend's ``Asset`` and ``SensorReading`` shapes."""

from __future__ import annotations

from typing import Any, Mapping

from enertwin.api.catalog import (
    ASSET_METRIC_FIELDS,
    BY_ID,
    CATALOG,
    HEADLINE_FIELD,
    METRIC_BOUNDS,
    METRIC_LABELS,
    AssetDescriptor,
)
from enertwin.api.mappers.common import iso, number, rounded
from enertwin.orchestration import Snapshot

SPARKLINE_POINTS = 24


def _metric(
    asset_id: str, field: str, state: Mapping[str, Any]
) -> dict[str, Any]:
    label, unit = METRIC_LABELS.get(field, (field.replace("_", " ").title(), ""))
    metric: dict[str, Any] = {
        "key": field,
        "label": label,
        "value": rounded(number(state, field), 3),
        "unit": unit,
    }
    metric.update(METRIC_BOUNDS.get((asset_id, field), {}))
    return metric


def _breaches(metric: Mapping[str, Any]) -> bool:
    value = metric.get("value")
    if value is None:
        return False
    warn_above = metric.get("warnAbove")
    warn_below = metric.get("warnBelow")
    if warn_above is not None and value > warn_above:
        return True
    if warn_below is not None and value < warn_below:
        return True
    return False


def _power_kw(descriptor: AssetDescriptor, state: Mapping[str, Any]) -> float | None:
    """Signed power in the frontend's convention: positive = consuming."""

    if descriptor.id == "grid":
        imported = number(state, "grid_import_kw")
        exported = number(state, "grid_export_kw")
        if imported is None and exported is None:
            return None
        return (imported or 0.0) - (exported or 0.0)

    if descriptor.power_field is None:
        return 0.0

    value = number(state, descriptor.power_field)
    if value is None:
        return None
    # Solar is metered as generation; the frontend expects generation negative.
    return -value if descriptor.power_is_generation else value


def _efficiency_pct(
    descriptor: AssetDescriptor,
    state: Mapping[str, Any],
    simulation: Mapping[str, Any] | None,
) -> float | None:
    """Measured efficiency, or the twin's own simulated estimate."""

    if descriptor.efficiency_field:
        measured = number(state, descriptor.efficiency_field)
        if measured is not None:
            return round(measured, 2)

    predicted = (simulation or {}).get("predicted_metrics")
    if isinstance(predicted, Mapping):
        for key in (
            "predicted_efficiency_percent",
            "efficiency_percent",
            "inverter_efficiency_percent",
            "round_trip_efficiency_percent",
        ):
            value = number(predicted, key)
            if value is not None:
                return round(value, 2)
    return None


def _sparkline(
    descriptor: AssetDescriptor, history: list[dict[str, Any]]
) -> list[float]:
    field = HEADLINE_FIELD[descriptor.id]
    points: list[float] = []
    for states in history[-SPARKLINE_POINTS:]:
        state = states.get(descriptor.twin_key)
        value = number(state, field) if isinstance(state, Mapping) else None
        if value is not None:
            points.append(round(value, 2))
    return points


def _status(
    state: Mapping[str, Any],
    metrics: list[dict[str, Any]],
    anomaly_count: int,
) -> str:
    if not state:
        return "offline"
    if anomaly_count and any(_breaches(metric) for metric in metrics):
        return "critical"
    if any(_breaches(metric) for metric in metrics):
        return "warning"
    if anomaly_count:
        return "warning"
    return "healthy"


def build_asset(
    descriptor: AssetDescriptor,
    snapshot: Snapshot,
    anomaly_counts: Mapping[str, int],
) -> dict[str, Any]:
    twin = snapshot.twin or {}
    states = twin.get("states", {}) or {}
    history = twin.get("history", []) or []
    simulations = twin.get("simulations", {}) or {}

    state = states.get(descriptor.twin_key) or {}
    metrics = [
        _metric(descriptor.id, field, state)
        for field in ASSET_METRIC_FIELDS[descriptor.id]
    ]
    headline_field = HEADLINE_FIELD[descriptor.id]
    headline = next(
        (m for m in metrics if m["key"] == headline_field),
        _metric(descriptor.id, headline_field, state),
    )

    power_kw = _power_kw(descriptor, state)
    utilisation = None
    if power_kw is not None and descriptor.rated_power_kw > 0:
        utilisation = round(abs(power_kw) / descriptor.rated_power_kw * 100, 1)

    anomaly_count = anomaly_counts.get(descriptor.id, 0)
    breaching = sum(1 for metric in metrics if _breaches(metric))

    return {
        "id": descriptor.id,
        "name": descriptor.name,
        "shortName": descriptor.short_name,
        "category": descriptor.category,
        "role": descriptor.role,
        "description": descriptor.description,
        "location": descriptor.location,
        "ratedPowerKw": descriptor.rated_power_kw,
        "status": _status(state, metrics, anomaly_count),
        "powerKw": rounded(power_kw, 2) if power_kw is not None else 0.0,
        "efficiencyPct": _efficiency_pct(
            descriptor, state, simulations.get(descriptor.twin_key)
        ),
        "utilisationPct": utilisation,
        "lastUpdated": iso(state.get("timestamp")) or snapshot.finished_at,
        "activeAlerts": breaching + anomaly_count,
        "headline": headline,
        "metrics": metrics,
        "sparkline": _sparkline(descriptor, history),
        "origin": "live" if state else "unavailable",
    }


def build_assets(
    snapshot: Snapshot, anomaly_counts: Mapping[str, int]
) -> list[dict[str, Any]]:
    return [build_asset(item, snapshot, anomaly_counts) for item in CATALOG]


def build_sensor_history(
    snapshot: Snapshot, asset_id: str, metric_key: str, hours: float
) -> list[dict[str, Any]]:
    """Every synchronized reading of one metric, newest last."""

    descriptor = BY_ID.get(asset_id)
    if descriptor is None:
        return []

    _label, unit = METRIC_LABELS.get(metric_key, (metric_key, ""))
    bounds = METRIC_BOUNDS.get((asset_id, metric_key), {})
    history = (snapshot.twin or {}).get("history", []) or []

    readings: list[dict[str, Any]] = []
    for states in history:
        state = states.get(descriptor.twin_key)
        if not isinstance(state, Mapping):
            continue
        value = number(state, metric_key)
        timestamp = iso(state.get("timestamp"))
        if value is None or timestamp is None:
            continue

        quality = "good"
        minimum, maximum = bounds.get("min"), bounds.get("max")
        if (minimum is not None and value < minimum) or (
            maximum is not None and value > maximum
        ):
            quality = "bad"
        elif (
            bounds.get("warnAbove") is not None and value > bounds["warnAbove"]
        ) or (bounds.get("warnBelow") is not None and value < bounds["warnBelow"]):
            quality = "uncertain"

        readings.append(
            {
                "assetId": asset_id,
                "metricKey": metric_key,
                "timestamp": timestamp,
                "value": round(value, 4),
                "unit": unit,
                "quality": quality,
            }
        )

    # `hours` selects a window over a 15-minute-resolution dataset.
    wanted = max(1, int(hours * 4))
    return readings[-wanted:]
