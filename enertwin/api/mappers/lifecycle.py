"""Module 7's model-lifecycle layer -> a serving shape.

Module 7 does more than explain and score: on every run it also monitors each
Random Forest for drift, trains a candidate replacement where a retraining
trigger fires, compares the candidate against the incumbent, and records whether
it was promoted. That work was previously invisible - the artifacts were written
and nothing read them.

Nothing here re-decides anything. Module 7's ``RetrainingPipeline`` owns the
trigger, the comparison and the promotion decision; this module reformats what
it already concluded, and preserves its own safety policy verbatim.
"""

from __future__ import annotations

from typing import Any

from enertwin.api.mappers.common import iso, number
from enertwin.api.mappers.explain import MODELS
from enertwin.orchestration import Snapshot

#: How Module 7's per-model statuses read to an operator.
STATUS_LABELS: dict[str, str] = {
    "not_required": "No retraining needed",
    "candidate_rejected": "Candidate rejected",
    "candidate_promoted": "Candidate promoted",
    "promoted": "Candidate promoted",
    "failed": "Retraining failed",
}

#: The metrics Module 7 reports per model, and how to label them.
METRIC_LABELS: tuple[tuple[str, str, str], ...] = (
    ("rmse", "RMSE", ""),
    ("mae", "MAE", ""),
    ("r2", "R²", ""),
    ("mape_percent", "MAPE", "%"),
    ("wape_percent", "WAPE", "%"),
    ("bias", "Bias", ""),
    ("max_error", "Max error", ""),
    ("sample_count", "Samples", ""),
)


def _metrics(source: Any) -> dict[str, Any] | None:
    if not isinstance(source, dict):
        return None
    return {
        key: number(source, key)
        for key, _label, _unit in METRIC_LABELS
        if number(source, key) is not None
    }


def _model_display(key: str) -> tuple[str, str]:
    """Frontend model id and display name for a Module 7 model key."""

    mapping = MODELS.get(key)
    if mapping is None:
        return key, key.replace("_", " ").title()
    model_id, name, *_rest = mapping
    return model_id, name


def build_model_lifecycle(snapshot: Snapshot) -> dict[str, Any]:
    """Per-model drift monitoring and retraining outcomes."""

    retraining = snapshot.retraining or {}
    monitoring = snapshot.monitoring or {}
    models = retraining.get("models") or {}

    entries: list[dict[str, Any]] = []
    for key, record in models.items():
        if not isinstance(record, dict):
            continue

        model_id, name = _model_display(key)
        status = str(record.get("status", "unknown"))
        current = _metrics(record.get("current_metrics"))
        candidate = _metrics(record.get("candidate_metrics"))

        entries.append(
            {
                "id": model_id,
                "name": name,
                "moduleKey": key,
                "modelFile": record.get("model"),
                "retrainingTriggered": bool(record.get("triggered")),
                "status": status,
                "statusLabel": STATUS_LABELS.get(
                    status, status.replace("_", " ").capitalize()
                ),
                "promoted": bool(record.get("promoted")),
                # Module 7 refuses to promote without an explicit promotion
                # path; null means no path was configured, which is why a
                # candidate that improved could still be held back.
                "promotionPath": record.get("promotion_path"),
                "rmseImprovementPct": number(record, "rmse_improvement_percent"),
                "currentMetrics": current,
                "candidateMetrics": candidate,
            }
        )

    entries.sort(key=lambda item: item["name"])

    triggered = [item for item in entries if item["retrainingTriggered"]]
    promoted = [item for item in entries if item["promoted"]]
    improved = [
        item
        for item in entries
        if (item["rmseImprovementPct"] or 0) > 0 and item["retrainingTriggered"]
    ]

    return {
        "generatedAt": iso(retraining.get("generated_at")) or snapshot.finished_at,
        # Module 7's own words, not a paraphrase.
        "safetyPolicy": retraining.get("safety_policy"),
        "summary": {
            "modelCount": len(entries),
            "retrainingTriggered": len(triggered),
            "candidatesImproved": len(improved),
            "promoted": len(promoted),
            # No model is ever promoted while every promotion_path is null.
            "promotionBlocked": bool(triggered) and not promoted,
        },
        "driftMonitoring": {
            "status": monitoring.get("status"),
            "evaluated": bool(monitoring.get("evaluated")),
            "retrainingRequired": bool(monitoring.get("retraining_required")),
            "reason": monitoring.get("reason"),
        },
        "models": entries,
        "origin": "live" if entries else "unavailable",
    }


def build_pipeline_evaluation(snapshot: Snapshot) -> dict[str, Any]:
    """Module 7's end-to-end assessment of the Modules 3-7 chain."""

    final = snapshot.final_report or {}
    performance = snapshot.performance or {}

    return {
        "generatedAt": iso(final.get("generated_at")) or snapshot.finished_at,
        "pipeline": final.get("pipeline"),
        "validation": final.get("validation"),
        "forecastingSummary": performance.get("forecasting_summary"),
        "decisionPipeline": performance.get("decision_pipeline"),
        "scenarioEvaluation": performance.get("scenario_evaluation"),
        "optimizationBenchmark": performance.get("optimization_benchmark"),
        # Module 7 records where a joblib model was written by a different
        # scikit-learn version than the one loading it. Empty is the good case.
        "modelCompatibilityWarnings": performance.get(
            "model_compatibility_warnings", []
        ),
        "origin": "live" if final or performance else "unavailable",
    }
