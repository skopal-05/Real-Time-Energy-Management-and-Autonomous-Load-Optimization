"""Module 7 SHAP output -> the frontend's ``Explanation`` shapes.

Module 7 computes exact single-reference Shapley values for each Random Forest
and writes both global feature importance and per-sample local explanations.
Everything here is a relabelling of those numbers - no contribution is derived,
rescaled or reordered.
"""

from __future__ import annotations

from typing import Any

from enertwin.api.catalog import METRIC_LABELS
from enertwin.api.mappers.common import iso, number
from enertwin.orchestration import Snapshot

ALGORITHM = "Random Forest Regressor"

#: Module 7 model key -> (frontend model id, display name, target label, unit,
#: assets the model covers).
MODELS: dict[str, tuple[str, str, str, str, tuple[str, ...]]] = {
    "production": (
        "production-rf",
        "Production Throughput Model",
        "Throughput",
        "units/h",
        ("line-a", "line-b"),
    ),
    "boiler": (
        "boiler-rf",
        "Boiler Fuel Model",
        "Fuel flow",
        "m³/h",
        ("boiler",),
    ),
    "compressor": (
        "compressor-rf",
        "Compressor Power Model",
        "Electrical power",
        "kW",
        ("compressor",),
    ),
    "hvac": ("hvac-rf", "HVAC Power Model", "Electrical power", "kW", ("hvac",)),
    "battery": (
        "battery-rf",
        "Battery Power Model",
        "Battery power",
        "kW",
        ("battery",),
    ),
    "grid": ("grid-rf", "Grid Import Model", "Grid import", "kW", ("grid",)),
    "solar": (
        "solar-rf",
        "Solar Output Model",
        "Inverter AC output",
        "kW",
        ("solar",),
    ),
}

BY_MODEL_ID: dict[str, str] = {
    model_id: key for key, (model_id, *_rest) in MODELS.items()
}

ASSET_NAMES: dict[str, str] = {
    "line-a": "Production Line A",
    "line-b": "Production Line B",
    "boiler": "Boiler",
    "compressor": "Compressor",
    "hvac": "HVAC",
    "solar": "Solar PV Array",
    "battery": "Battery Storage",
    "grid": "Grid Connection",
    "site": "Whole Site",
}


def build_models(snapshot: Snapshot) -> list[dict[str, Any]]:
    shap = (snapshot.shap or {}).get("models", {}) or {}

    models: list[dict[str, Any]] = []
    for key, entry in shap.items():
        mapping = MODELS.get(key)
        if mapping is None:
            continue
        model_id, name, target, _unit, scope = mapping
        models.append(
            {
                "id": model_id,
                "name": name,
                "algorithm": ALGORITHM,
                "target": f"{target} ({entry.get('target', key)})",
                "scope": list(scope),
            }
        )
    return models


def build_explanation(
    snapshot: Snapshot, model_id: str, asset_id: str
) -> dict[str, Any] | None:
    shap = snapshot.shap or {}
    key = BY_MODEL_ID.get(model_id)
    if key is None:
        return None

    entry = (shap.get("models") or {}).get(key)
    if not isinstance(entry, dict):
        return None

    _model_id, name, target, unit, scope = MODELS[key]
    if asset_id != "site" and asset_id not in scope:
        return None

    locals_ = entry.get("local_explanations") or []
    if not locals_:
        return None
    sample = locals_[0]

    contributions = []
    for factor in sample.get("top_factors", []) or []:
        feature = str(factor.get("feature", ""))
        label, feature_unit = METRIC_LABELS.get(feature, (feature, ""))
        contributions.append(
            {
                "feature": feature,
                "label": label,
                "shapValue": number(factor, "shap_value") or 0.0,
                "featureValue": number(factor, "feature_value") or 0.0,
                "unit": feature_unit,
            }
        )

    prediction = number(sample, "prediction") or 0.0
    base_value = number(sample, "base_value") or 0.0

    narrative = str(sample.get("summary", ""))
    narrative = (
        f"The model's expected output is {base_value:.3g} {unit}; for this "
        f"operating point it predicts {prediction:.3g} {unit}. {narrative}"
    ).strip()

    return {
        "id": f"{model_id}-{asset_id}",
        "modelId": model_id,
        "modelName": name,
        "algorithm": ALGORITHM,
        "assetId": asset_id,
        "assetName": ASSET_NAMES.get(asset_id, asset_id),
        "target": f"{target} ({entry.get('target', key)})",
        "prediction": round(prediction, 4),
        "baseValue": round(base_value, 4),
        "unit": unit,
        "generatedAt": iso(shap.get("generated_at")) or snapshot.finished_at,
        "contributions": contributions,
        "narrative": narrative,
        "origin": "live",
    }


def global_importance(snapshot: Snapshot) -> dict[str, list[dict[str, Any]]]:
    """Model-native feature importance, keyed by frontend model id."""

    document = (snapshot.feature_importance or {}).get("models", {}) or {}
    result: dict[str, list[dict[str, Any]]] = {}
    for key, entry in document.items():
        mapping = MODELS.get(key)
        if mapping is None:
            continue
        model_id = mapping[0]
        result[model_id] = [
            {
                "feature": item.get("feature"),
                "label": METRIC_LABELS.get(
                    str(item.get("feature")), (str(item.get("feature")), "")
                )[0],
                "importance": number(item, "importance") or 0.0,
                "rank": item.get("rank"),
            }
            for item in entry.get("features", []) or []
        ]
    return result


def mean_model_confidence_pct(snapshot: Snapshot) -> float | None:
    """Mean R² across Module 7's forecast evaluation, as a 0-100 figure.

    Returns ``None`` when Module 7 reported no usable evaluation, rather than
    substituting a placeholder confidence.
    """

    summary = (snapshot.performance or {}).get("forecasting_summary")
    value = number(summary, "mean_r2") if isinstance(summary, dict) else None
    if value is None:
        return None
    return round(max(0.0, min(1.0, value)) * 100, 1)
