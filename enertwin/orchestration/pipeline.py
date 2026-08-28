"""End-to-end orchestration of the seven modules.

Runs each adapter in order. A failing stage stops the chain, because every
downstream module reads the previous one's artifact - but whatever completed is
still returned, so the API can serve a partial system honestly instead of
showing nothing.
"""

from __future__ import annotations

import logging
from typing import Any

from enertwin.adapters import PIPELINE, RunContext
from enertwin.config import (
    PIPELINE_INTERVAL_SECONDS,
    REGENERATE_DATA,
    TWIN_SYNC_STEPS,
    ensure_platform_dirs,
)
from enertwin.orchestration.snapshot import Snapshot, load_snapshot, now_iso

logger = logging.getLogger("enertwin.pipeline")


def run_pipeline(
    *,
    twin_steps: int | None = None,
    twin_source: str = "cleaned",
    horizon_hours: float = 1.0,
    regenerate_data: bool | None = None,
    stop_on_failure: bool = True,
) -> Snapshot:
    """Run Modules 1-7 in order and return the resulting snapshot."""

    ensure_platform_dirs()

    context = RunContext.create(
        twin_steps=twin_steps if twin_steps is not None else TWIN_SYNC_STEPS,
        twin_source=twin_source,
        horizon_hours=horizon_hours,
        regenerate_data=(
            REGENERATE_DATA if regenerate_data is None else regenerate_data
        ),
    )
    context.workspace.mkdir(parents=True, exist_ok=True)

    started_at = now_iso()
    stages: list[dict[str, Any]] = []
    ok = True

    logger.info("pipeline run %s started", context.run_id)

    for adapter in PIPELINE:
        try:
            result = adapter.run(context)
        except Exception as error:  # an adapter itself failed, not the module
            logger.exception("adapter %s raised", adapter.module_key)
            from enertwin.adapters import StageResult

            result = StageResult(
                module_key=adapter.module_key,
                ok=False,
                detail=f"adapter error: {type(error).__name__}: {error}",
            )

        stages.append(result.as_dict())
        level = logging.INFO if result.ok else logging.ERROR
        logger.log(
            level,
            "  %-8s %-34s %s (%.2fs)",
            result.module_key,
            result.title,
            "ok" if result.ok else f"FAILED - {result.detail}",
            result.duration_seconds,
        )
        for note in result.translations:
            logger.info("           translation: %s", note)

        if not result.ok:
            ok = False
            if stop_on_failure:
                logger.error(
                    "stopping: downstream modules read %s's artifact",
                    result.module_key,
                )
                break

    snapshot = load_snapshot(
        run_id=context.run_id,
        started_at=started_at,
        finished_at=now_iso(),
        ok=ok,
        stages=stages,
        workspace=context.workspace,
    )

    logger.info(
        "pipeline run %s finished: %s", context.run_id, "ok" if ok else "incomplete"
    )
    return snapshot


def default_interval_seconds() -> int:
    return PIPELINE_INTERVAL_SECONDS
