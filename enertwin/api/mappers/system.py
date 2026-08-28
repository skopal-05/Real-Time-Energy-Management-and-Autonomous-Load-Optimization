"""Pipeline state and module artifacts -> ``SystemStatus`` and ``SystemEvent``.

Every event here is something that actually happened during the last run: a
module stage completing or failing, a boundary translation being applied, a
sensor reading being rejected by a twin, an anomaly being flagged, a
high-priority agent decision, or the optimizer converging. Nothing is scripted.
"""

from __future__ import annotations

from typing import Any

from enertwin.api.catalog import BY_ID, CATALOG
from enertwin.api.mappers.anomalies import build_anomalies
from enertwin.api.mappers.assets import build_assets
from enertwin.api.mappers.common import iso, now_iso, percent
from enertwin.api.mappers.decisions import build_objective, build_recommendations
from enertwin.api.mappers.energy import site_totals
from enertwin.api.mappers.explain import mean_model_confidence_pct
from enertwin.api.mappers.forecasting import next_hour_load_kw
from enertwin.api.mappers.lifecycle import build_model_lifecycle
from enertwin.orchestration import Snapshot

STAGE_LABELS: dict[str, tuple[str, str]] = {
    "module1": ("Data Acquisition", "Module 1"),
    "module2": ("Digital Twin", "Module 2"),
    "module3": ("Forecasting", "Module 3 · Random Forest"),
    "module4": ("Decision Agents", "Module 4 · Multi-agent"),
    "module5": ("Scenario Simulation", "Module 5"),
    "module6": ("Optimisation", "Module 6 · Genetic Algorithm"),
    "module7": ("Explainability & Evaluation", "Module 7 · SHAP + Isolation Forest"),
}


#: The frontend's pipeline strip (``PIPELINE_STEPS`` in lib/constants.ts) keys
#: its steps by these ids and looks each one up in ``pipelineStages``. Its seven
#: steps are not the project's seven modules: it shows anomaly detection and
#: explainability as separate steps - both Module 7 - and folds scenario
#: simulation into the optimisation step. This is the mapping between the two.
STRIP_STEPS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    ("acquisition", "Data Acquisition", "Module 1", ("module1",)),
    ("twin", "Digital Twin", "Module 2", ("module2",)),
    ("forecast", "Forecasting", "Module 3 · Random Forest", ("module3",)),
    ("agents", "Decision Agents", "Module 4 · Multi-agent", ("module4",)),
    (
        "optimizer",
        "Optimisation",
        "Modules 5-6 · Scenarios + Genetic Algorithm",
        ("module5", "module6"),
    ),
    ("anomaly", "Anomaly Detection", "Module 7 · Isolation Forest", ("module7",)),
    ("xai", "Explainability", "Module 7 · SHAP", ("module7",)),
)


def build_pipeline_stages(snapshot: Snapshot) -> list[dict[str, Any]]:
    """Stage status keyed the way the frontend's pipeline strip looks it up."""

    by_module = {entry.get("module"): entry for entry in snapshot.stages}

    stages: list[dict[str, Any]] = []
    for step_id, label, module_label, module_keys in STRIP_STEPS:
        entries = [by_module[key] for key in module_keys if key in by_module]

        if not entries:
            state, detail = "idle", "not reached in the last run"
        elif all(entry.get("ok") for entry in entries):
            # Interface translations are design decisions, not degradations;
            # only a stage that flagged itself degraded shows as needing
            # attention.
            state = (
                "degraded"
                if any(entry.get("degraded") for entry in entries)
                else "ok"
            )
            detail = str(entries[-1].get("detail") or "completed")
        else:
            state = "down"
            failed = next(entry for entry in entries if not entry.get("ok"))
            detail = str(failed.get("detail") or "failed")

        stages.append(
            {
                "id": step_id,
                "label": label,
                "module": module_label,
                "state": state,
                "detail": detail[:160],
            }
        )

    return stages


def build_status(snapshot: Snapshot) -> dict[str, Any]:
    from enertwin.api.mappers.anomalies import anomaly_counts_by_asset

    anomaly_counts = anomaly_counts_by_asset(snapshot)
    assets = build_assets(snapshot, anomaly_counts)
    totals = site_totals(snapshot, hours=24)
    latest = totals.get("latest", {})

    twins_total = len(CATALOG)
    twins_online = sum(1 for asset in assets if asset["status"] != "offline")

    stages = build_pipeline_stages(snapshot)
    stages_ok = sum(1 for stage in stages if stage["state"] == "ok")

    healthy_assets = sum(
        1 for asset in assets if asset["status"] in {"healthy", "online"}
    )
    # Two equally weighted halves: how much of the pipeline ran, and how many
    # twins are in a healthy state. Both are directly observable.
    health_score = round(
        (stages_ok / len(stages) * 50) + (healthy_assets / max(twins_total, 1) * 50), 1
    )

    warning_assets = sum(1 for asset in assets if asset["status"] == "warning")
    critical_assets = sum(1 for asset in assets if asset["status"] == "critical")

    if not snapshot.ok or critical_assets:
        overall = "critical" if critical_assets else "warning"
    elif warning_assets:
        overall = "warning"
    else:
        overall = "healthy"

    objective = build_objective(snapshot)
    anomalies = build_anomalies(snapshot)

    optimization_status = "idle"
    if snapshot.optimization_report:
        feasible = (snapshot.optimization_report.get("summary") or {}).get("feasible")
        optimization_status = "converged" if feasible else "failed"

    solar_kw = latest.get("solarKw")
    grid_kw = latest.get("gridKw")
    renewable_share = None
    if solar_kw is not None and grid_kw is not None:
        supplied = max(solar_kw, 0.0) + max(grid_kw, 0.0)
        renewable_share = percent(max(solar_kw, 0.0), supplied)

    return {
        "timestamp": latest.get("timestamp") or snapshot.finished_at or now_iso(),
        "overall": overall,
        "healthScorePct": health_score,
        "operatingMode": objective["mode"],
        "operatingModeLabel": objective["label"],
        "twinsOnline": twins_online,
        "twinsTotal": twins_total,
        "consumptionKw": latest.get("consumptionKw", 0.0),
        "generationKw": latest.get("generationKw", 0.0),
        "renewableSharePct": renewable_share if renewable_share is not None else 0.0,
        "forecastNextHourKw": next_hour_load_kw(snapshot),
        "optimizationStatus": optimization_status,
        "activeAnomalies": len(anomalies),
        "aiConfidencePct": mean_model_confidence_pct(snapshot),
        "pipelineStages": stages,
        "origin": "live" if snapshot.twin else "unavailable",
    }


def build_events(snapshot: Snapshot) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    run_time = snapshot.finished_at or now_iso()

    for entry in snapshot.stages:
        key = entry.get("module", "")
        label, module = STAGE_LABELS.get(key, (key, key))
        ok = entry.get("ok")
        events.append(
            {
                "id": f"stage-{key}",
                "kind": "system",
                "severity": "info" if ok else "high",
                "title": f"{label} {'completed' if ok else 'failed'}",
                "detail": f"{module}: {entry.get('detail', '')}",
                "assetId": None,
                "timestamp": run_time,
            }
        )
        for index, note in enumerate(entry.get("translations", [])):
            events.append(
                {
                    "id": f"translation-{key}-{index}",
                    "kind": "system",
                    "severity": "low",
                    "title": f"{label}: interface translation applied",
                    "detail": note,
                    "assetId": None,
                    "timestamp": run_time,
                }
            )

    for reading in (snapshot.twin or {}).get("rejected_readings", [])[:20]:
        asset = reading.get("asset")
        descriptor = next(
            (item for item in CATALOG if item.twin_key == asset), None
        )
        events.append(
            {
                "id": f"rejected-{asset}-{reading.get('step')}",
                "kind": "alert",
                "severity": "medium",
                "title": "Sensor reading rejected by digital twin",
                "detail": str(reading.get("reason", "")),
                "assetId": descriptor.id if descriptor else None,
                "timestamp": iso(reading.get("timestamp")) or run_time,
            }
        )

    for anomaly in build_anomalies(snapshot)[:20]:
        events.append(
            {
                "id": f"event-{anomaly['id']}",
                "kind": "anomaly",
                "severity": anomaly["severity"],
                "title": f"Anomaly detected on {anomaly['assetName']}",
                "detail": anomaly["summary"],
                "assetId": anomaly["assetId"],
                "timestamp": anomaly["detectedAt"],
            }
        )

    for recommendation in build_recommendations(snapshot):
        if recommendation["priority"] not in {"high", "critical"}:
            continue
        events.append(
            {
                "id": f"event-{recommendation['id']}",
                "kind": (
                    "optimization"
                    if recommendation["sourceModule"] == "optimizer"
                    else "decision"
                ),
                "severity": recommendation["priority"],
                "title": f"{recommendation['agentName']}: {recommendation['title']}",
                "detail": recommendation["rationale"],
                "assetId": (
                    recommendation["targetAssets"][0]
                    if recommendation["targetAssets"]
                    else None
                ),
                "timestamp": recommendation["createdAt"],
            }
        )

    # Module 7's model-lifecycle work: retraining triggers, candidate
    # comparisons and promotion decisions. Without this the whole layer runs
    # every cycle with nothing to show for it.
    lifecycle = build_model_lifecycle(snapshot)
    lifecycle_summary = lifecycle["summary"]
    if lifecycle_summary["retrainingTriggered"]:
        events.append(
            {
                "id": "event-retraining",
                "kind": "system",
                "severity": "medium" if lifecycle_summary["promotionBlocked"] else "info",
                "title": (
                    f"Retraining evaluated for "
                    f"{lifecycle_summary['retrainingTriggered']} of "
                    f"{lifecycle_summary['modelCount']} models"
                ),
                "detail": (
                    f"{lifecycle_summary['candidatesImproved']} candidate(s) beat the "
                    f"incumbent; {lifecycle_summary['promoted']} promoted. "
                    + (lifecycle["safetyPolicy"] or "")
                ).strip(),
                "assetId": None,
                "timestamp": lifecycle["generatedAt"],
            }
        )

    for model in lifecycle["models"]:
        if not model["retrainingTriggered"] or model["promoted"]:
            continue
        improvement = model["rmseImprovementPct"]
        events.append(
            {
                "id": f"event-retraining-{model['id']}",
                "kind": "system",
                "severity": "low",
                "title": f"{model['name']}: {model['statusLabel'].lower()}",
                "detail": (
                    f"Retraining triggered; the candidate changed RMSE by "
                    f"{improvement:+.4f}%. "
                    if improvement is not None
                    else "Retraining triggered. "
                )
                + (
                    "No promotion path is configured, so no candidate can replace "
                    "the model in service."
                    if model["promotionPath"] is None
                    else f"Promotion path: {model['promotionPath']}"
                ),
                "assetId": None,
                "timestamp": lifecycle["generatedAt"],
            }
        )

    drift = lifecycle["driftMonitoring"]
    if drift.get("status") and not drift.get("evaluated"):
        events.append(
            {
                "id": "event-drift-monitoring",
                "kind": "system",
                "severity": "low",
                "title": "Model drift monitoring did not evaluate",
                "detail": str(drift.get("reason") or ""),
                "assetId": None,
                "timestamp": lifecycle["generatedAt"],
            }
        )

    scenarios = (snapshot.scenarios or {}).get("result", {}) or {}
    report = scenarios.get("report") or {}
    if report:
        events.append(
            {
                "id": "event-scenario",
                "kind": "optimization",
                "severity": "info",
                "title": f"Scenario selected: {report.get('best_scenario_name', '-')}",
                "detail": (
                    f"{report.get('scenario_count', 0)} scenarios simulated; "
                    f"weighted score {report.get('best_score', 0):.2f}/100."
                ),
                "assetId": None,
                "timestamp": iso(report.get("generated_at")) or run_time,
            }
        )

    events.sort(key=lambda item: item["timestamp"] or "", reverse=True)
    return events


def asset_exists(asset_id: str) -> bool:
    return asset_id in BY_ID
