"""Module 3 forecasts -> the frontend's ``Forecast`` shapes.

The driver replays Module 3's seven Random Forest models across every
synchronized interval, recording each model's prediction alongside the measured
value of its training target. That gives a real actual-vs-predicted series and
real accuracy metrics, computed here rather than assumed.

Two honesty notes carried through to the UI:

* Module 3's models map an interval's features to that same interval's target,
  so the historical series is a replay over data the models were trained on -
  the accuracy figures are replay accuracy, not held-out generalisation.
* The models expose no predictive distribution, so ``lowerKw``/``upperKw`` and
  peak ``confidence`` are ``null`` rather than invented bands.
"""

from __future__ import annotations

from typing import Any

from enertwin.api.catalog import BY_ID
from enertwin.api.mappers.common import (
    accuracy,
    iso,
    now_iso,
    percent,
    shift_iso,
    trend_of,
)
from enertwin.orchestration import Snapshot

RESOLUTION_MINUTES = 15
ALGORITHM = "Random Forest Regressor"

HORIZON_POINTS: dict[str, int] = {"1h": 4, "6h": 24, "24h": 96, "7d": 672}

#: Frontend asset id -> (twin key used in the forecast series, model id, label,
#: target description, unit is kW unless stated).
SITE_MODEL = "site-load-rf"

ASSET_MODELS: dict[str, tuple[str, str, str]] = {
    "line-a": ("production_line_a", "production-rf", "Line A throughput (units/h)"),
    "line-b": ("production_line_b", "production-rf", "Line B throughput (units/h)"),
    "boiler": ("boiler", "boiler-rf", "Boiler fuel flow (m³/h)"),
    "compressor": ("compressor", "compressor-rf", "Compressor power (kW)"),
    "hvac": ("hvac", "hvac-rf", "HVAC power (kW)"),
    "solar": ("solar", "solar-rf", "Inverter AC output (kW)"),
    "battery": ("battery", "battery-rf", "Battery power (kW)"),
    "grid": ("grid", "grid-rf", "Grid import (kW)"),
}


#: Frontend asset id -> the key Module 7 evaluates that asset's model under.
MODULE7_MODEL_KEY: dict[str, str] = {
    "line-a": "production",
    "line-b": "production",
    "boiler": "boiler",
    "compressor": "compressor",
    "hvac": "hvac",
    "solar": "solar",
    "battery": "battery",
    "grid": "grid",
}


def module7_accuracy(snapshot: Snapshot, asset_id: str) -> dict[str, Any] | None:
    """Module 7's held-out evaluation of a model, when it produced one.

    Module 7 is the project's evaluation module: it scores each Random Forest on
    a held-out split, which is a stronger measurement than replaying the models
    over the window they were trained on. Its figures are preferred wherever it
    reported them.
    """

    key = MODULE7_MODEL_KEY.get(asset_id)
    models = (snapshot.performance or {}).get("forecasting_models")
    if key is None or not isinstance(models, dict):
        return None

    entry = models.get(key)
    if not isinstance(entry, dict):
        return None
    metrics = entry.get("metrics")
    if not isinstance(metrics, dict):
        return None

    sample_count = metrics.get("sample_count")
    return {
        "mae": metrics.get("mae"),
        "rmse": metrics.get("rmse"),
        "r2": metrics.get("r2"),
        "mapePct": metrics.get("mape_percent"),
        "sampleCount": int(sample_count) if sample_count is not None else 0,
        "evaluatedAt": iso((snapshot.performance or {}).get("generated_at")),
    }


def _steps(snapshot: Snapshot) -> list[dict[str, Any]]:
    series = snapshot.forecast_series or {}
    steps = series.get("steps")
    return steps if isinstance(steps, list) else []


def _site_pair(step: dict[str, Any]) -> tuple[float | None, float | None]:
    """Module 3's total load: compressor + HVAC, measured and predicted."""

    measured = step.get("measured", {})
    predicted = step.get("predicted", {})

    def add(source: dict[str, Any]) -> float | None:
        parts = [source.get("compressor"), source.get("hvac")]
        if any(part is None for part in parts):
            return None
        return round(sum(parts), 3)

    return add(measured), add(predicted)


def _series_from_pairs(
    pairs: list[tuple[str | None, float | None, float | None]],
    forward: float | None,
) -> list[dict[str, Any]]:
    points = [
        {
            "timestamp": timestamp,
            "actualKw": actual,
            "predictedKw": predicted,
            "lowerKw": None,
            "upperKw": None,
        }
        for timestamp, actual, predicted in pairs
        if timestamp is not None
    ]

    if points and forward is not None:
        points.append(
            {
                "timestamp": shift_iso(points[-1]["timestamp"], RESOLUTION_MINUTES),
                "actualKw": None,
                "predictedKw": forward,
                "lowerKw": None,
                "upperKw": None,
            }
        )
    return points


def _peak(points: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [p for p in points if p["predictedKw"] is not None]
    if not scored:
        return None
    best = max(scored, key=lambda p: p["predictedKw"])
    return {
        "predictedKw": round(best["predictedKw"], 3),
        "expectedAt": best["timestamp"],
        # Module 3's models expose no predictive distribution.
        "confidence": None,
    }


def _forecast(
    *,
    model_id: str,
    model_name: str,
    target: str,
    horizon: str,
    points: list[dict[str, Any]],
    generated_at: str,
    reported_accuracy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wanted = HORIZON_POINTS.get(horizon, 96)
    window = points[-(wanted + 1) :] if len(points) > wanted else points

    pairs = [
        (p["actualKw"], p["predictedKw"])
        for p in window
        if p["actualKw"] is not None and p["predictedKw"] is not None
    ]

    return {
        "modelId": model_id,
        "modelName": model_name,
        "algorithm": ALGORITHM,
        "target": target,
        "horizon": horizon,
        "resolutionMinutes": RESOLUTION_MINUTES,
        "generatedAt": generated_at,
        "series": window,
        "accuracy": reported_accuracy or accuracy(pairs),
        "peak": _peak(window),
        "origin": "live" if window else "unavailable",
    }


def build_site_forecast(snapshot: Snapshot, horizon: str) -> dict[str, Any]:
    steps = _steps(snapshot)
    pairs: list[tuple[str | None, float | None, float | None]] = []
    for step in steps:
        measured, predicted = _site_pair(step)
        pairs.append((iso(step.get("timestamp")), measured, predicted))

    forward = None
    latest = (snapshot.forecast or {}).get("energy_forecast", {})
    if isinstance(latest, dict) and latest.get("total_load_kw") is not None:
        forward = round(float(latest["total_load_kw"]), 3)

    return _forecast(
        model_id=SITE_MODEL,
        model_name="Site Load Forecast",
        target="Total electrical load - compressor + HVAC (Module 3 LoadForecast)",
        horizon=horizon,
        points=_series_from_pairs(pairs, forward),
        generated_at=(snapshot.forecast_series or {}).get("generated_at", now_iso()),
    )


def build_asset_forecast(
    snapshot: Snapshot, asset_id: str, horizon: str
) -> dict[str, Any]:
    entry = ASSET_MODELS.get(asset_id)
    descriptor = BY_ID.get(asset_id)
    generated_at = (snapshot.forecast_series or {}).get("generated_at", now_iso())

    if entry is None or descriptor is None:
        return _forecast(
            model_id="unknown",
            model_name=asset_id,
            target="unknown",
            horizon=horizon,
            points=[],
            generated_at=generated_at,
        )

    twin_key, model_id, target = entry
    pairs = [
        (
            iso(step.get("timestamp")),
            step.get("measured", {}).get(twin_key),
            step.get("predicted", {}).get(twin_key),
        )
        for step in _steps(snapshot)
    ]

    forward = None
    future_state = (snapshot.forecast or {}).get("future_state", {})
    forward_key = {
        "line-a": "production_line_a_units_per_hour",
        "line-b": "production_line_b_units_per_hour",
        "boiler": "fuel_flow_m3_hr",
        "compressor": "compressor_power_kw",
        "hvac": "hvac_power_kw",
        "solar": "inverter_power_kw",
        "battery": "battery_power_kw",
        "grid": "grid_import_kw",
    }[asset_id]
    if isinstance(future_state, dict) and future_state.get(forward_key) is not None:
        forward = round(float(future_state[forward_key]), 3)

    return _forecast(
        model_id=model_id,
        model_name=f"{descriptor.name} Forecast",
        target=target,
        horizon=horizon,
        points=_series_from_pairs(pairs, forward),
        generated_at=generated_at,
        reported_accuracy=module7_accuracy(snapshot, asset_id),
    )


def build_asset_summaries(snapshot: Snapshot, horizon: str) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []

    for asset_id, (twin_key, _model_id, _target) in ASSET_MODELS.items():
        descriptor = BY_ID[asset_id]
        forecast = build_asset_forecast(snapshot, asset_id, horizon)
        points = forecast["series"]

        actuals = [p["actualKw"] for p in points if p["actualKw"] is not None]
        # The forward-looking part of the series: the points Module 3 predicted
        # for time the plant has not reached yet. Taking a peak across the
        # historical replay instead would compare a night-time reading against a
        # midday one and report it as a forecast change.
        ahead = [
            p["predictedKw"]
            for p in points
            if p["actualKw"] is None and p["predictedKw"] is not None
        ]
        if not actuals or not ahead:
            continue

        current = actuals[-1]
        peak = max(ahead)
        change = percent(peak - current, abs(current)) if current else None

        summaries.append(
            {
                "assetId": asset_id,
                "assetName": descriptor.name,
                "currentKw": round(current, 2),
                "predictedPeakKw": round(peak, 2),
                "changePct": change if change is not None else 0.0,
                "trend": trend_of(change),
                "mapePct": forecast["accuracy"]["mapePct"],
            }
        )

    return summaries


def site_accuracy(snapshot: Snapshot) -> dict[str, Any]:
    return build_site_forecast(snapshot, "24h")["accuracy"]


def next_hour_load_kw(snapshot: Snapshot) -> float | None:
    latest = (snapshot.forecast or {}).get("energy_forecast", {})
    if isinstance(latest, dict) and latest.get("total_load_kw") is not None:
        return round(float(latest["total_load_kw"]), 2)
    return None
