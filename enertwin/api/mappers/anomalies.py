"""Module 7 Isolation Forest output -> the frontend's ``Anomaly`` shapes.

Two translations, both recorded here:

* **Sign.** Module 7 scores higher = more anomalous, with the decision boundary
  at zero. The frontend's contract is the sklearn convention - more negative =
  more anomalous, anomalous below the threshold - so scores are negated and the
  threshold stays at zero. Ordering and separation are preserved exactly.

* **Attribution.** Module 7 detects on the two production lines' data
  concatenated, and its records carry a row index into that combined frame
  rather than an asset or a timestamp. Each record's feature values are matched
  back against the synchronized twin history to recover which line it came from
  and when. A record that matches nothing is reported with its asset left as the
  production line pair's first member and its provenance marked ``simulated``,
  so the UI never claims an attribution the data does not support.
"""

from __future__ import annotations

from typing import Any, Mapping

from enertwin.api.catalog import METRIC_LABELS
from enertwin.api.mappers.common import iso, number, severity_from_score
from enertwin.orchestration import Snapshot

PRODUCTION_ASSETS = ("line-a", "line-b")
PRODUCTION_TWIN_KEYS = {"line-a": "production_line_a", "line-b": "production_line_b"}

#: Module 7's detector decides at zero in its own scoring space.
RAW_THRESHOLD = 0.0

TOLERANCE = 1e-6


def _match_record(
    values: Mapping[str, Any], history: list[dict[str, Any]]
) -> tuple[str | None, str | None]:
    """Find the twin reading whose features match this scored record."""

    wanted = {key: number(values, key) for key in values}
    for states in history:
        for asset_id, twin_key in PRODUCTION_TWIN_KEYS.items():
            state = states.get(twin_key)
            if not isinstance(state, Mapping):
                continue
            if all(
                wanted[key] is not None
                and (candidate := number(state, key)) is not None
                and abs(candidate - wanted[key]) < TOLERANCE
                for key in wanted
            ):
                return asset_id, iso(state.get("timestamp"))
    return None, None


def _dominant_feature(
    values: Mapping[str, Any], history: list[dict[str, Any]]
) -> tuple[str, float, tuple[float, float]]:
    """The feature furthest from its observed range, and that range."""

    ranges: dict[str, list[float]] = {key: [] for key in values}
    for states in history:
        for twin_key in PRODUCTION_TWIN_KEYS.values():
            state = states.get(twin_key)
            if not isinstance(state, Mapping):
                continue
            for key in ranges:
                value = number(state, key)
                if value is not None:
                    ranges[key].append(value)

    best_key = next(iter(values))
    best_deviation = -1.0
    best_range = (0.0, 0.0)

    for key, observed in ranges.items():
        value = number(values, key)
        if value is None or not observed:
            continue
        low, high = min(observed), max(observed)
        span = high - low
        if span <= 0:
            continue
        centre = (high + low) / 2
        deviation = abs(value - centre) / (span / 2)
        if deviation > best_deviation:
            best_key, best_deviation, best_range = key, deviation, (low, high)

    return best_key, best_deviation, best_range


def build_anomalies(snapshot: Snapshot) -> list[dict[str, Any]]:
    report = snapshot.anomalies or {}
    records = report.get("records", []) or []
    history = (snapshot.twin or {}).get("history", []) or []
    detected_default = iso(report.get("generated_at")) or snapshot.finished_at

    results: list[dict[str, Any]] = []
    for record in records:
        if not record.get("is_anomaly"):
            continue

        values = record.get("values", {}) or {}
        asset_id, timestamp = _match_record(values, history)
        matched = asset_id is not None
        asset_id = asset_id or PRODUCTION_ASSETS[0]

        feature, _deviation, (low, high) = _dominant_feature(values, history)
        label, unit = METRIC_LABELS.get(feature, (feature, ""))

        raw = number(record, "raw_score") or 0.0
        score = -raw  # frontend convention: more negative = more anomalous
        severity = severity_from_score(raw, 0.02)

        observed = number(values, feature)
        results.append(
            {
                "id": f"m7-anomaly-{record.get('row_index')}",
                "assetId": asset_id,
                "assetName": (
                    "Production Line A" if asset_id == "line-a" else "Production Line B"
                ),
                "metricKey": feature,
                "metricLabel": label,
                "detectedAt": timestamp or detected_default,
                "severity": severity,
                "status": "active",
                "score": round(score, 6),
                "threshold": RAW_THRESHOLD,
                "observedValue": round(observed, 3) if observed is not None else 0.0,
                "expectedRange": [round(low, 3), round(high, 3)],
                "unit": unit,
                "summary": (
                    f"Isolation Forest flagged this operating point across "
                    f"{', '.join(report.get('feature_names', []))}. "
                    f"{label} read {observed:.3g} {unit} against an observed range of "
                    f"{low:.3g}-{high:.3g} {unit} over the synchronized window."
                    if observed is not None
                    else "Isolation Forest flagged this operating point."
                ),
                "origin": "live" if matched else "simulated",
            }
        )

    results.sort(key=lambda item: item["score"])
    return results


def build_anomaly_scores(snapshot: Snapshot, hours: float) -> dict[str, Any]:
    """Every scored window, for the score-over-time scatter plot."""

    report = snapshot.anomalies or {}
    records = report.get("records", []) or []
    history = (snapshot.twin or {}).get("history", []) or []

    points: list[dict[str, Any]] = []
    for record in records:
        values = record.get("values", {}) or {}
        _asset_id, timestamp = _match_record(values, history)
        raw = number(record, "raw_score") or 0.0

        if timestamp:
            epoch_ms = int(
                __import__("datetime")
                .datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                .timestamp()
                * 1000
            )
        else:
            epoch_ms = record.get("row_index", 0)

        points.append(
            {
                "timestamp": epoch_ms,
                "score": round(-raw, 6),
                "anomalous": bool(record.get("is_anomaly")),
                "label": str(record.get("label", "")),
            }
        )

    points.sort(key=lambda item: item["timestamp"])
    wanted = max(1, int(hours * 4))
    return {"points": points[-wanted:], "threshold": RAW_THRESHOLD}


def anomaly_counts_by_asset(snapshot: Snapshot) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in build_anomalies(snapshot):
        counts[item["assetId"]] = counts.get(item["assetId"], 0) + 1
    return counts


def anomaly_stats(snapshot: Snapshot) -> dict[str, Any]:
    items = build_anomalies(snapshot)
    by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for item in items:
        by_severity[item["severity"]] = by_severity.get(item["severity"], 0) + 1

    return {
        "total": len(items),
        "active": len(items),
        "acknowledged": 0,
        "resolved": 0,
        "bySeverity": by_severity,
        # Nothing in the chain acknowledges or resolves anomalies, so there is
        # no resolution time to report.
        "meanTimeToResolveMinutes": None,
    }
