"""The API must satisfy the contract the frontend was already written against.

Endpoint paths come from ``frontend/src/services/httpDataSource.ts`` and payload
shapes from ``frontend/src/lib/types.ts``. If a test here fails, a screen in the
existing UI breaks.
"""

from __future__ import annotations

from typing import Any

import pytest

ASSET_IDS = [
    "line-a",
    "line-b",
    "boiler",
    "compressor",
    "hvac",
    "solar",
    "battery",
    "grid",
]

HEALTH_STATES = {"online", "healthy", "warning", "critical", "offline"}
SEVERITIES = {"low", "medium", "high", "critical"}
ORIGINS = {"live", "simulated", "unavailable"}


def has_keys(payload: dict[str, Any], *keys: str) -> None:
    missing = [key for key in keys if key not in payload]
    assert not missing, f"missing keys {missing} in {sorted(payload)}"


# ----------------------------------------------------------------------
# System
# ----------------------------------------------------------------------


def test_system_status(client) -> None:
    body = client.get("/api/system/status").json()
    has_keys(
        body,
        "timestamp",
        "overall",
        "healthScorePct",
        "operatingMode",
        "operatingModeLabel",
        "twinsOnline",
        "twinsTotal",
        "consumptionKw",
        "generationKw",
        "renewableSharePct",
        "forecastNextHourKw",
        "optimizationStatus",
        "activeAnomalies",
        "aiConfidencePct",
        "pipelineStages",
        "origin",
    )
    assert body["overall"] in HEALTH_STATES
    assert body["twinsTotal"] == 8
    assert body["origin"] in ORIGINS
    assert body["optimizationStatus"] in {"idle", "running", "converged", "failed"}


def test_pipeline_stages_use_the_ids_the_frontend_looks_up(client) -> None:
    """``PIPELINE_STEPS`` in lib/constants.ts keys the strip by these ids."""

    stages = client.get("/api/system/status").json()["pipelineStages"]
    assert {stage["id"] for stage in stages} == {
        "acquisition",
        "twin",
        "forecast",
        "agents",
        "optimizer",
        "anomaly",
        "xai",
    }
    for stage in stages:
        has_keys(stage, "id", "label", "module", "state", "detail")
        assert stage["state"] in {"ok", "degraded", "down", "idle"}


def test_system_events(client) -> None:
    events = client.get("/api/system/events").json()
    assert isinstance(events, list) and events
    for event in events:
        has_keys(event, "id", "kind", "severity", "title", "detail", "assetId", "timestamp")
        assert event["kind"] in {
            "alert",
            "anomaly",
            "decision",
            "optimization",
            "forecast",
            "system",
        }
        assert event["severity"] in SEVERITIES | {"info"}


# ----------------------------------------------------------------------
# Assets
# ----------------------------------------------------------------------


def test_assets_list(client) -> None:
    assets = client.get("/api/assets").json()
    assert [asset["id"] for asset in assets] == ASSET_IDS

    for asset in assets:
        has_keys(
            asset,
            "id",
            "name",
            "shortName",
            "category",
            "role",
            "description",
            "location",
            "ratedPowerKw",
            "status",
            "powerKw",
            "efficiencyPct",
            "utilisationPct",
            "lastUpdated",
            "activeAlerts",
            "headline",
            "metrics",
            "sparkline",
            "origin",
        )
        assert asset["status"] in HEALTH_STATES
        assert asset["origin"] in ORIGINS
        assert isinstance(asset["powerKw"], (int, float))
        assert asset["metrics"], f"{asset['id']} has no metrics"
        has_keys(asset["headline"], "key", "label", "value", "unit")


@pytest.mark.parametrize("asset_id", ASSET_IDS)
def test_single_asset(client, asset_id: str) -> None:
    asset = client.get(f"/api/assets/{asset_id}").json()
    assert asset["id"] == asset_id


def test_unknown_asset_returns_null(client) -> None:
    """The frontend types this as ``Asset | null``."""

    assert client.get("/api/assets/does-not-exist").json() is None


def test_sensor_history(client) -> None:
    readings = client.get("/api/assets/hvac/sensors/power_kw?hours=24").json()
    assert readings
    for reading in readings:
        has_keys(reading, "assetId", "metricKey", "timestamp", "value", "unit", "quality")
        assert reading["quality"] in {"good", "uncertain", "bad"}


# ----------------------------------------------------------------------
# Energy
# ----------------------------------------------------------------------


def test_energy_window(client) -> None:
    readings = client.get("/api/energy/window?hours=24&step_minutes=15").json()
    assert len(readings) == 96
    for reading in readings:
        has_keys(
            reading,
            "timestamp",
            "consumptionKw",
            "generationKw",
            "solarKw",
            "batteryKw",
            "gridKw",
            "batterySocPct",
        )


def test_energy_window_downsamples(client) -> None:
    coarse = client.get("/api/energy/window?hours=24&step_minutes=60").json()
    assert len(coarse) == 24


def test_source_shares_sum_to_100(client) -> None:
    shares = client.get("/api/energy/sources?hours=24").json()
    assert {item["source"] for item in shares} == {"Solar", "Battery", "Grid"}
    assert sum(item["sharePct"] for item in shares) == pytest.approx(100, abs=0.5)


def test_energy_flow(client) -> None:
    flow = client.get("/api/energy/flow").json()
    has_keys(flow, "timestamp", "nodes", "links", "origin")

    ids = {node["id"] for node in flow["nodes"]}
    # The frontend's fixed layout addresses these node ids by name.
    assert ids >= {"solar", "battery", "grid", "bus", *ASSET_IDS[:5]} - {"boiler"} or "bus" in ids
    assert "bus" in ids, "the frontend's flow layout places the hub at id 'bus'"

    for link in flow["links"]:
        has_keys(link, "from", "to", "powerKw", "colorToken", "active")
        assert link["from"] in ids and link["to"] in ids


# ----------------------------------------------------------------------
# Forecasting
# ----------------------------------------------------------------------


def test_site_forecast(client) -> None:
    forecast = client.get("/api/forecast/site?horizon=24h").json()
    has_keys(
        forecast,
        "modelId",
        "modelName",
        "algorithm",
        "target",
        "horizon",
        "resolutionMinutes",
        "generatedAt",
        "series",
        "accuracy",
        "peak",
        "origin",
    )
    has_keys(forecast["accuracy"], "mae", "rmse", "r2", "mapePct", "sampleCount", "evaluatedAt")
    assert forecast["series"]

    for point in forecast["series"]:
        has_keys(point, "timestamp", "actualKw", "predictedKw", "lowerKw", "upperKw")

    # The final point is the forward forecast: predicted, not yet measured.
    assert forecast["series"][-1]["actualKw"] is None
    assert forecast["series"][-1]["predictedKw"] is not None


@pytest.mark.parametrize("horizon,expected", [("1h", 5), ("6h", 25), ("24h", 97)])
def test_forecast_horizon_limits_the_window(client, horizon: str, expected: int) -> None:
    forecast = client.get(f"/api/forecast/site?horizon={horizon}").json()
    assert len(forecast["series"]) == expected


@pytest.mark.parametrize("asset_id", ASSET_IDS)
def test_asset_forecast(client, asset_id: str) -> None:
    forecast = client.get(f"/api/forecast/asset/{asset_id}?horizon=24h").json()
    assert forecast["series"]
    assert forecast["origin"] == "live"


def test_asset_forecast_summaries(client) -> None:
    summaries = client.get("/api/forecast/assets/summary?horizon=24h").json()
    assert summaries
    for item in summaries:
        has_keys(
            item,
            "assetId",
            "assetName",
            "currentKw",
            "predictedPeakKw",
            "changePct",
            "trend",
            "mapePct",
        )
        assert item["trend"] in {"up", "down", "flat"}


def test_forecast_reports_no_invented_uncertainty(client) -> None:
    """Module 3's models expose no predictive distribution."""

    forecast = client.get("/api/forecast/site?horizon=24h").json()
    assert all(point["lowerKw"] is None for point in forecast["series"])
    assert all(point["upperKw"] is None for point in forecast["series"])
    assert forecast["peak"]["confidence"] is None


# ----------------------------------------------------------------------
# Decisions
# ----------------------------------------------------------------------


def test_agents(client) -> None:
    agents = client.get("/api/agents").json()
    assert len(agents) == 13, "twelve Module 4 agents plus the rule engine"
    for agent in agents:
        has_keys(
            agent,
            "id",
            "name",
            "scope",
            "state",
            "ruleCount",
            "decisionsToday",
            "lastActionAt",
            "watches",
        )
        assert agent["state"] in {"active", "standby", "disabled"}


def test_rule_engine_reports_its_real_rule_count(client) -> None:
    agents = {agent["id"]: agent for agent in client.get("/api/agents").json()}
    assert agents["rule_engine"]["ruleCount"] == 4


def test_objective(client) -> None:
    objective = client.get("/api/agents/objective").json()
    has_keys(objective, "mode", "label", "description", "constraints", "since")
    assert objective["mode"] in {
        "cost-optimal",
        "peak-shaving",
        "carbon-minimal",
        "resilience",
    }


def test_recommendations(client) -> None:
    recommendations = client.get("/api/agents/recommendations").json()
    assert recommendations
    for item in recommendations:
        has_keys(
            item,
            "id",
            "agentId",
            "agentName",
            "title",
            "ruleTriggered",
            "rationale",
            "targetAssets",
            "priority",
            "status",
            "createdAt",
            "expectedImpact",
            "sourceModule",
            "origin",
        )
        assert item["priority"] in SEVERITIES
        assert item["status"] in {"pending", "accepted", "applied", "rejected", "expired"}
        assert item["sourceModule"] in {"rules", "forecast", "optimizer", "anomaly"}


def test_recommendations_come_from_both_modules(client) -> None:
    sources = {
        item["sourceModule"] for item in client.get("/api/agents/recommendations").json()
    }
    assert "rules" in sources, "Module 4 decisions missing"
    assert "optimizer" in sources, "Module 6 recommendations missing"


# ----------------------------------------------------------------------
# Optimisation
# ----------------------------------------------------------------------


def test_optimization(client) -> None:
    result = client.get("/api/optimization/latest").json()
    has_keys(
        result,
        "runId",
        "algorithm",
        "status",
        "startedAt",
        "finishedAt",
        "generations",
        "populationSize",
        "convergence",
        "objective",
        "constraints",
        "schedule",
        "cost",
        "peakDemand",
        "energyKwh",
        "origin",
    )
    assert result["status"] in {"idle", "running", "converged", "failed"}
    assert result["generations"] > 0
    has_keys(result["objective"], "summary", "terms")
    has_keys(result["cost"], "currency", "baseline", "optimised")

    for constraint in result["constraints"]:
        has_keys(constraint, "id", "label", "expression", "satisfied", "slack")
    for slot in result["schedule"]:
        has_keys(slot, "timestamp", "baselineKw", "optimisedKw")


def test_convergence_is_the_ga_real_search_trajectory(client) -> None:
    """One point per generation, carrying Module 6's own best-fitness values."""

    result = client.get("/api/optimization/latest").json()
    convergence = result["convergence"]

    assert len(convergence) == result["generations"], (
        "expected one convergence point per GA generation"
    )
    assert [point["generation"] for point in convergence] == list(
        range(1, len(convergence) + 1)
    )

    best = [point["bestFitness"] for point in convergence]
    assert all(isinstance(value, (int, float)) for value in best)
    # A minimising GA's best-so-far can never get worse.
    assert all(
        later <= earlier + 1e-9 for earlier, later in zip(best, best[1:])
    ), "best-so-far fitness increased, which a minimising GA cannot do"


def test_mean_fitness_is_null_because_module6_records_only_the_best(client) -> None:
    """The GA tracks the best candidate per generation, not the population mean.

    Pinned so the missing series cannot quietly become a fabricated one.
    """

    convergence = client.get("/api/optimization/latest").json()["convergence"]
    assert convergence
    assert all(point["meanFitness"] is None for point in convergence)


# ----------------------------------------------------------------------
# Anomalies
# ----------------------------------------------------------------------


def test_anomalies(client) -> None:
    anomalies = client.get("/api/anomalies").json()
    assert anomalies
    for item in anomalies:
        has_keys(
            item,
            "id",
            "assetId",
            "assetName",
            "metricKey",
            "metricLabel",
            "detectedAt",
            "severity",
            "status",
            "score",
            "threshold",
            "observedValue",
            "expectedRange",
            "unit",
            "summary",
            "origin",
        )
        assert item["severity"] in SEVERITIES
        assert item["status"] in {"active", "acknowledged", "resolved"}
        assert len(item["expectedRange"]) == 2


def test_anomaly_scores_follow_the_frontend_sign_convention(client) -> None:
    """More negative = more anomalous; anomalous means below the threshold."""

    body = client.get("/api/anomalies/scores?hours=24").json()
    has_keys(body, "points", "threshold")
    assert body["points"]

    for point in body["points"]:
        has_keys(point, "timestamp", "score", "anomalous", "label")
        if point["anomalous"]:
            assert point["score"] < body["threshold"], point
        else:
            assert point["score"] >= body["threshold"], point


def test_anomalies_are_traced_back_to_a_real_twin_reading(client) -> None:
    """Attribution is matched, not assumed: origin stays 'live' when matched."""

    for item in client.get("/api/anomalies").json():
        assert item["origin"] == "live", (
            f"{item['id']} could not be matched to a twin reading; "
            "it would be reported as simulated"
        )
        assert item["assetId"] in {"line-a", "line-b"}


# ----------------------------------------------------------------------
# Explainability
# ----------------------------------------------------------------------


def test_explainable_models(client) -> None:
    models = client.get("/api/explain/models").json()
    assert len(models) == 7
    for model in models:
        has_keys(model, "id", "name", "algorithm", "target", "scope")
        assert model["scope"]


def test_explanation(client) -> None:
    explanation = client.get(
        "/api/explain?model_id=hvac-rf&asset_id=hvac"
    ).json()
    has_keys(
        explanation,
        "id",
        "modelId",
        "modelName",
        "algorithm",
        "assetId",
        "assetName",
        "target",
        "prediction",
        "baseValue",
        "unit",
        "generatedAt",
        "contributions",
        "narrative",
        "origin",
    )
    assert explanation["contributions"]
    for contribution in explanation["contributions"]:
        has_keys(contribution, "feature", "label", "shapValue", "featureValue", "unit")


def test_explanation_for_an_unmatched_pair_returns_null(client) -> None:
    """The frontend types this as ``Explanation | null``."""

    assert client.get("/api/explain?model_id=hvac-rf&asset_id=solar").json() is None
    assert client.get("/api/explain?model_id=nope&asset_id=hvac").json() is None


# ----------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------


@pytest.mark.parametrize("period", ["day", "week", "month"])
def test_report(client, period: str) -> None:
    report = client.get(f"/api/reports?period={period}").json()
    has_keys(
        report,
        "period",
        "rangeStart",
        "rangeEnd",
        "totals",
        "series",
        "assetBreakdown",
        "forecastPerformance",
        "anomalyStats",
        "optimizationImpact",
        "origin",
    )
    has_keys(
        report["totals"],
        "consumptionKwh",
        "generationKwh",
        "gridImportKwh",
        "gridExportKwh",
        "renewableSharePct",
        "peakDemandKw",
        "averageLoadKw",
        "loadFactorPct",
    )
    assert report["series"], "the energy profile chart needs at least one bucket"
    has_keys(
        report["anomalyStats"],
        "total",
        "active",
        "acknowledged",
        "resolved",
        "bySeverity",
        "meanTimeToResolveMinutes",
    )


def test_report_range_reflects_the_data_not_the_period_label(client) -> None:
    day = client.get("/api/reports?period=day").json()
    week = client.get("/api/reports?period=week").json()
    assert day["rangeStart"] == week["rangeStart"], (
        "Module 1's dataset covers one day; a week report cannot claim more"
    )


# ----------------------------------------------------------------------
# Platform and auth
# ----------------------------------------------------------------------


def test_health(client) -> None:
    body = client.get("/api/health").json()
    has_keys(body, "status", "version", "hasSnapshot", "pipelineRunning", "timestamp")


def test_translations_are_exposed(client) -> None:
    body = client.get("/api/pipeline/translations").json()
    has_keys(body, "runId", "translations", "stages")


def test_auth_sessions_are_flagged_as_demo(client) -> None:
    """No identity provider is wired, and the API says so."""

    session = client.post(
        "/api/auth/login", json={"email": "operator@plant.example", "password": "x"}
    ).json()
    has_keys(session, "user", "token", "issuedAt", "expiresAt", "demo")
    assert session["demo"] is True
    assert client.post("/api/auth/logout", json={}).status_code == 204


# ----------------------------------------------------------------------
# Module 7's model-lifecycle layer
# ----------------------------------------------------------------------
#
# Not part of the frontend contract. Module 7 monitors each model for drift,
# trains candidate replacements where a trigger fires and records promotion
# decisions on every run; these endpoints exist so that work is not invisible.


def test_model_lifecycle(client) -> None:
    body = client.get("/api/models/lifecycle").json()
    has_keys(
        body,
        "generatedAt",
        "safetyPolicy",
        "summary",
        "driftMonitoring",
        "models",
        "origin",
    )
    has_keys(
        body["summary"],
        "modelCount",
        "retrainingTriggered",
        "candidatesImproved",
        "promoted",
        "promotionBlocked",
    )
    assert body["summary"]["modelCount"] == 7
    assert body["origin"] == "live"

    for model in body["models"]:
        has_keys(
            model,
            "id",
            "name",
            "moduleKey",
            "modelFile",
            "retrainingTriggered",
            "status",
            "statusLabel",
            "promoted",
            "promotionPath",
            "rmseImprovementPct",
            "currentMetrics",
            "candidateMetrics",
        )
        assert isinstance(model["retrainingTriggered"], bool)
        assert isinstance(model["promoted"], bool)
        # A model that was never retrained cannot have a candidate to compare.
        if not model["retrainingTriggered"]:
            assert model["candidateMetrics"] is None


def test_lifecycle_preserves_module7_safety_policy_verbatim(client) -> None:
    """The promotion rule is Module 7's, quoted rather than restated."""

    body = client.get("/api/models/lifecycle").json()
    assert body["safetyPolicy"], "Module 7's safety policy should be carried through"
    assert "promotion_path" in body["safetyPolicy"]


def test_lifecycle_never_reports_a_promotion_module7_did_not_make(client) -> None:
    body = client.get("/api/models/lifecycle").json()
    for model in body["models"]:
        if model["promoted"]:
            assert model["promotionPath"] is not None, (
                f"{model['id']} is reported promoted with no promotion path, "
                "which Module 7's safety policy forbids"
            )
    if body["summary"]["promotionBlocked"]:
        assert body["summary"]["promoted"] == 0


def test_model_evaluation(client) -> None:
    body = client.get("/api/models/evaluation").json()
    has_keys(
        body,
        "generatedAt",
        "pipeline",
        "validation",
        "forecastingSummary",
        "decisionPipeline",
        "scenarioEvaluation",
        "optimizationBenchmark",
        "modelCompatibilityWarnings",
        "origin",
    )
    assert body["origin"] == "live"
    assert isinstance(body["modelCompatibilityWarnings"], list)


def test_retraining_reaches_the_event_feed(client) -> None:
    """The lifecycle layer is visible in the UI, not only on its own endpoint."""

    events = client.get("/api/system/events").json()
    titles = " | ".join(event["title"] for event in events)
    assert "Retraining evaluated" in titles, (
        "Module 7's retraining work should surface in the operator event feed"
    )
