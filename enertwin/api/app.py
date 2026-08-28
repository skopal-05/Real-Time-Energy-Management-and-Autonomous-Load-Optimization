"""The REST API the existing frontend already knows how to call.

Every path and payload below is dictated by
``frontend/src/services/httpDataSource.ts`` and ``frontend/src/lib/types.ts``,
which were written against a backend that did not exist yet. Connecting the real
system therefore needs no frontend code change - only ``.env.local``:

    NEXT_PUBLIC_API_MODE=live
    NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api

Requests are served from the in-memory snapshot of the last completed pipeline
run. They never block on the modules.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from enertwin import __version__
from enertwin.api.catalog import BY_ID
from enertwin.api.mappers import (
    anomalies as anomaly_mapper,
    assets as asset_mapper,
    decisions as decision_mapper,
    energy as energy_mapper,
    explain as explain_mapper,
    forecasting as forecast_mapper,
    lifecycle as lifecycle_mapper,
    optimization as optimization_mapper,
    reports as report_mapper,
    system as system_mapper,
)
from enertwin.api.mappers.common import now_iso
from enertwin.config import (
    CORS_ORIGINS,
    PIPELINE_INTERVAL_SECONDS,
    TWIN_SYNC_STEPS,
    ensure_platform_dirs,
)
from enertwin.orchestration import (
    PipelineBusy,
    PipelineScheduler,
    Snapshot,
    SnapshotUnavailable,
    store,
)

logger = logging.getLogger("enertwin.api")

_scheduler: PipelineScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run the pipeline once at start-up so the UI has data immediately."""

    global _scheduler
    ensure_platform_dirs()

    logger.info("running the initial pipeline pass...")
    store.run_in_background(twin_steps=TWIN_SYNC_STEPS)

    if PIPELINE_INTERVAL_SECONDS > 0:
        _scheduler = PipelineScheduler(
            store, PIPELINE_INTERVAL_SECONDS, twin_steps=TWIN_SYNC_STEPS
        )
        _scheduler.start()

    yield

    if _scheduler is not None:
        _scheduler.stop()


app = FastAPI(
    title="EnerTwin Integration API",
    version=__version__,
    description=(
        "Integration layer over the seven modules of the Generative Digital Twin "
        "platform. The modules are executed, never modified."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def snapshot() -> Snapshot:
    """The latest completed run, or a 503 explaining that none exists yet."""

    try:
        return store.require_snapshot()
    except SnapshotUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


# ======================================================================
# Platform endpoints - not part of the frontend contract
# ======================================================================


@app.get("/api/health")
def health() -> dict[str, Any]:
    current = store.snapshot
    return {
        "status": "ok" if current and current.ok else "degraded",
        "version": __version__,
        "hasSnapshot": current is not None,
        "pipelineRunning": store.is_running,
        "timestamp": now_iso(),
    }


@app.get("/api/pipeline/status")
def pipeline_status() -> dict[str, Any]:
    return store.status()


@app.post("/api/pipeline/run")
def pipeline_run(
    payload: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    """Trigger an end-to-end run of Modules 1-7."""

    kwargs: dict[str, Any] = {
        "twin_steps": int(payload.get("twinSteps", TWIN_SYNC_STEPS)),
        "twin_source": str(payload.get("twinSource", "cleaned")),
        "horizon_hours": float(payload.get("horizonHours", 1.0)),
    }
    if "regenerateData" in payload:
        kwargs["regenerate_data"] = bool(payload["regenerateData"])

    if payload.get("wait"):
        try:
            result = store.run_now(**kwargs)
        except PipelineBusy as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"started": True, "completed": True, "run": result.as_dict()}

    started = store.run_in_background(**kwargs)
    if not started:
        raise HTTPException(
            status_code=409, detail="A pipeline run is already in progress."
        )
    return {"started": True, "completed": False}


@app.get("/api/pipeline/translations")
def pipeline_translations() -> dict[str, Any]:
    """Every interface translation the platform applied in the last run."""

    current = snapshot()
    return {
        "runId": current.run_id,
        "translations": current.translations,
        "stages": current.stages,
    }


# ======================================================================
# System
# ======================================================================


@app.get("/api/system/status")
def system_status() -> dict[str, Any]:
    return system_mapper.build_status(snapshot())


@app.get("/api/system/events")
def system_events() -> list[dict[str, Any]]:
    return system_mapper.build_events(snapshot())


# ======================================================================
# Assets and twins
# ======================================================================


@app.get("/api/assets")
def assets() -> list[dict[str, Any]]:
    current = snapshot()
    return asset_mapper.build_assets(
        current, anomaly_mapper.anomaly_counts_by_asset(current)
    )


@app.get("/api/assets/{asset_id}")
def asset(asset_id: str) -> Any:
    descriptor = BY_ID.get(asset_id)
    if descriptor is None:
        return JSONResponse(content=None)
    current = snapshot()
    return asset_mapper.build_asset(
        descriptor, current, anomaly_mapper.anomaly_counts_by_asset(current)
    )


@app.get("/api/assets/{asset_id}/sensors/{metric_key}")
def sensor_history(
    asset_id: str, metric_key: str, hours: float = Query(default=24)
) -> list[dict[str, Any]]:
    return asset_mapper.build_sensor_history(snapshot(), asset_id, metric_key, hours)


# ======================================================================
# Energy
# ======================================================================


@app.get("/api/energy/window")
def energy_window(
    hours: float = Query(default=24), step_minutes: int = Query(default=15)
) -> list[dict[str, Any]]:
    return energy_mapper.build_energy_window(snapshot(), hours, step_minutes)


@app.get("/api/energy/sources")
def energy_sources(hours: float = Query(default=24)) -> list[dict[str, Any]]:
    return energy_mapper.build_source_shares(snapshot(), hours)


@app.get("/api/energy/flow")
def energy_flow() -> dict[str, Any]:
    return energy_mapper.build_energy_flow(snapshot())


# ======================================================================
# Forecasting
# ======================================================================


@app.get("/api/forecast/site")
def forecast_site(horizon: str = Query(default="24h")) -> dict[str, Any]:
    return forecast_mapper.build_site_forecast(snapshot(), horizon)


@app.get("/api/forecast/asset/{asset_id}")
def forecast_asset(asset_id: str, horizon: str = Query(default="24h")) -> dict[str, Any]:
    return forecast_mapper.build_asset_forecast(snapshot(), asset_id, horizon)


@app.get("/api/forecast/assets/summary")
def forecast_summary(horizon: str = Query(default="24h")) -> list[dict[str, Any]]:
    return forecast_mapper.build_asset_summaries(snapshot(), horizon)


# ======================================================================
# Decisions
# ======================================================================


@app.get("/api/agents")
def agents() -> list[dict[str, Any]]:
    return decision_mapper.build_agents(snapshot())


@app.get("/api/agents/objective")
def objective() -> dict[str, Any]:
    return decision_mapper.build_objective(snapshot())


@app.get("/api/agents/recommendations")
def recommendations() -> list[dict[str, Any]]:
    return decision_mapper.build_recommendations(snapshot())


# ======================================================================
# Optimisation
# ======================================================================


@app.get("/api/optimization/latest")
def optimization_latest() -> dict[str, Any]:
    return optimization_mapper.build_optimization(snapshot())


# ======================================================================
# Anomalies
# ======================================================================


@app.get("/api/anomalies")
def anomalies() -> list[dict[str, Any]]:
    return anomaly_mapper.build_anomalies(snapshot())


@app.get("/api/anomalies/scores")
def anomaly_scores(hours: float = Query(default=24)) -> dict[str, Any]:
    return anomaly_mapper.build_anomaly_scores(snapshot(), hours)


# ======================================================================
# Explainability
# ======================================================================


@app.get("/api/explain/models")
def explain_models() -> list[dict[str, Any]]:
    return explain_mapper.build_models(snapshot())


@app.get("/api/explain")
def explain(
    model_id: str = Query(...), asset_id: str = Query(default="site")
) -> Any:
    result = explain_mapper.build_explanation(snapshot(), model_id, asset_id)
    return JSONResponse(content=result)


@app.get("/api/models/lifecycle")
def model_lifecycle() -> dict[str, Any]:
    """Module 7's drift monitoring and retraining decisions, per model.

    Not part of the frontend contract: Module 7 produces this on every run and
    the existing UI has no screen for it, so the platform serves it rather than
    letting the module's model-lifecycle work stay invisible.
    """

    return lifecycle_mapper.build_model_lifecycle(snapshot())


@app.get("/api/models/evaluation")
def model_evaluation() -> dict[str, Any]:
    """Module 7's end-to-end assessment of the Modules 3-7 chain.

    Also outside the frontend contract, for the same reason.
    """

    return lifecycle_mapper.build_pipeline_evaluation(snapshot())


@app.get("/api/explain/importance")
def explain_importance() -> dict[str, Any]:
    """Model-native feature importance. Not part of the frontend contract."""

    return explain_mapper.global_importance(snapshot())


# ======================================================================
# Reporting
# ======================================================================


@app.get("/api/reports")
def reports(period: str = Query(default="day")) -> dict[str, Any]:
    return report_mapper.build_report(snapshot(), period)


# ======================================================================
# Authentication
# ======================================================================
#
# The platform has no identity provider. Rather than pretend otherwise, these
# endpoints issue a session flagged ``demo: true`` - the same flag the
# frontend's own demo adapter sets, which every sign-in screen already surfaces.
# Wiring a real provider means replacing these three handlers and nothing else.


def _demo_session(name: str, email: str, organisation: str) -> dict[str, Any]:
    return {
        "user": {
            "id": "demo-user",
            "name": name,
            "email": email,
            "role": "engineer",
            "organisation": organisation,
        },
        "token": "",
        "issuedAt": now_iso(),
        "expiresAt": None,
        "demo": True,
    }


def _display_name(email: str) -> str:
    local = email.split("@")[0] or "operator"
    return " ".join(part.capitalize() for part in local.replace(".", " ").replace("_", " ").replace("-", " ").split())


@app.post("/api/auth/login")
def auth_login(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    email = str(payload.get("email", "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="An email address is required.")
    return _demo_session(_display_name(email), email, "Demo Plant")


@app.post("/api/auth/register")
def auth_register(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    email = str(payload.get("email", "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="An email address is required.")
    return _demo_session(
        str(payload.get("name") or _display_name(email)),
        email,
        str(payload.get("organisation") or "Demo Plant"),
    )


@app.post("/api/auth/logout", status_code=204)
def auth_logout() -> None:
    return None
