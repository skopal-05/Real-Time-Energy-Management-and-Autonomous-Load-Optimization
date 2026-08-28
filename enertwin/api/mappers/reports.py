"""Aggregated performance reporting across the whole run.

Module 1's cleaned dataset covers a single 24-hour day at 15-minute resolution.
The ``week`` and ``month`` periods therefore report over the same window as
``day`` - the range returned is always the range the data actually spans, so the
UI's date range reflects reality rather than the period label.
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
from typing import Any

from enertwin.api.catalog import CATALOG, CURRENCY
from enertwin.api.mappers.anomalies import anomaly_counts_by_asset, anomaly_stats
from enertwin.api.mappers.assets import build_assets
from enertwin.api.mappers.energy import SAMPLE_MINUTES, build_energy_window, site_totals
from enertwin.api.mappers.forecasting import site_accuracy
from enertwin.api.mappers.optimization import optimization_impact
from enertwin.api.mappers.common import number, percent
from enertwin.orchestration import Snapshot

PERIOD_HOURS: dict[str, float] = {"day": 24, "week": 24 * 7, "month": 24 * 31}


def _bucket_label(timestamp: str, hourly: bool) -> str:
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return timestamp
    return parsed.strftime("%H:00") if hourly else parsed.strftime("%d %b")


def _series(readings: list[dict[str, Any]], period: str) -> list[dict[str, Any]]:
    interval_hours = SAMPLE_MINUTES / 60
    buckets: OrderedDict[str, dict[str, float]] = OrderedDict()

    # Bucket by hour whenever the data spans two days or less, whatever period
    # was asked for. Module 1's dataset covers a single day, so bucketing a
    # "week" by day would collapse the whole chart into one bar.
    span_hours = len(readings) * interval_hours
    hourly = period == "day" or span_hours <= 48

    for reading in readings:
        label = _bucket_label(reading["timestamp"], hourly)
        bucket = buckets.setdefault(
            label, {"consumptionKwh": 0.0, "generationKwh": 0.0, "peakKw": 0.0}
        )
        bucket["consumptionKwh"] += reading["consumptionKw"] * interval_hours
        bucket["generationKwh"] += reading["generationKw"] * interval_hours
        bucket["peakKw"] = max(bucket["peakKw"], reading["consumptionKw"])

    return [
        {
            "label": label,
            "consumptionKwh": round(values["consumptionKwh"], 2),
            "generationKwh": round(values["generationKwh"], 2),
            "peakKw": round(values["peakKw"], 2),
        }
        for label, values in buckets.items()
    ]


def _asset_breakdown(snapshot: Snapshot) -> list[dict[str, Any]]:
    history = (snapshot.twin or {}).get("history", []) or []
    interval_hours = SAMPLE_MINUTES / 60

    rows: list[dict[str, Any]] = []
    assets = {
        asset["id"]: asset
        for asset in build_assets(snapshot, anomaly_counts_by_asset(snapshot))
    }

    energies: dict[str, float] = {}
    availability: dict[str, tuple[int, int]] = {}

    for descriptor in CATALOG:
        if descriptor.power_field is None or descriptor.power_is_generation:
            continue
        total_kwh = 0.0
        present = 0
        for states in history:
            state = states.get(descriptor.twin_key)
            value = number(state, descriptor.power_field) if state else None
            if value is None:
                continue
            present += 1
            total_kwh += max(value, 0.0) * interval_hours
        energies[descriptor.id] = total_kwh
        availability[descriptor.id] = (present, len(history))

    consumed = sum(energies.values())

    for descriptor in CATALOG:
        if descriptor.id not in energies:
            continue
        present, expected = availability[descriptor.id]
        asset = assets.get(descriptor.id, {})
        rows.append(
            {
                "assetId": descriptor.id,
                "assetName": descriptor.name,
                "energyKwh": round(energies[descriptor.id], 2),
                "sharePct": percent(energies[descriptor.id], consumed) or 0.0,
                "efficiencyPct": asset.get("efficiencyPct"),
                "availabilityPct": percent(present, expected) or 0.0,
            }
        )

    rows.sort(key=lambda row: row["energyKwh"], reverse=True)
    return rows


def build_report(snapshot: Snapshot, period: str) -> dict[str, Any]:
    hours = PERIOD_HOURS.get(period, 24)
    readings = build_energy_window(snapshot, hours, SAMPLE_MINUTES)
    totals = site_totals(snapshot, hours)

    if not readings:
        return {
            "period": period,
            "rangeStart": snapshot.started_at,
            "rangeEnd": snapshot.finished_at,
            "totals": {
                "consumptionKwh": 0.0,
                "generationKwh": 0.0,
                "gridImportKwh": 0.0,
                "gridExportKwh": 0.0,
                "renewableSharePct": 0.0,
                "peakDemandKw": 0.0,
                "averageLoadKw": 0.0,
                "loadFactorPct": 0.0,
            },
            "series": [],
            "assetBreakdown": [],
            "forecastPerformance": site_accuracy(snapshot),
            "anomalyStats": anomaly_stats(snapshot),
            "optimizationImpact": optimization_impact(snapshot),
            "origin": "unavailable",
        }

    return {
        "period": period,
        "rangeStart": totals["rangeStart"],
        "rangeEnd": totals["rangeEnd"],
        "totals": {
            "consumptionKwh": totals["consumptionKwh"],
            "generationKwh": totals["generationKwh"],
            "gridImportKwh": totals["gridImportKwh"],
            "gridExportKwh": totals["gridExportKwh"],
            "renewableSharePct": totals["renewableSharePct"],
            "peakDemandKw": totals["peakDemandKw"],
            "averageLoadKw": totals["averageLoadKw"],
            "loadFactorPct": totals["loadFactorPct"],
        },
        "series": _series(readings, period),
        "assetBreakdown": _asset_breakdown(snapshot),
        "forecastPerformance": site_accuracy(snapshot),
        "anomalyStats": anomaly_stats(snapshot),
        "optimizationImpact": optimization_impact(snapshot),
        "origin": "live",
    }


__all__ = ["CURRENCY", "build_report"]
