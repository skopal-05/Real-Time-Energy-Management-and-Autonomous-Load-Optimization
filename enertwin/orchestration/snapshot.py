"""The platform's normalised view of one pipeline run.

A snapshot holds the artifacts the seven modules produced, loaded into memory
exactly as they were written. Nothing here reinterprets a module's numbers; the
API mappers do that, separately and visibly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from enertwin.config import ARTIFACTS


def read_json(path: str | Path) -> Any | None:
    """Read a JSON artifact, or return ``None`` when it is absent or invalid."""

    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


@dataclass
class Snapshot:
    """Everything the API needs from one end-to-end run."""

    run_id: str
    started_at: str
    finished_at: str
    ok: bool
    stages: list[dict[str, Any]] = field(default_factory=list)

    # Module artifacts, as written by the modules themselves.
    twin: dict[str, Any] | None = None
    forecast: dict[str, Any] | None = None
    forecast_series: dict[str, Any] | None = None
    agents: dict[str, Any] | None = None
    scenarios: dict[str, Any] | None = None
    optimization_report: dict[str, Any] | None = None
    optimized_state: dict[str, Any] | None = None
    optimization_recommendations: dict[str, Any] | None = None
    shap: dict[str, Any] | None = None
    feature_importance: dict[str, Any] | None = None
    anomalies: dict[str, Any] | None = None
    performance: dict[str, Any] | None = None
    monitoring: dict[str, Any] | None = None
    retraining: dict[str, Any] | None = None
    final_report: dict[str, Any] | None = None

    @property
    def translations(self) -> list[str]:
        """Every interface translation performed across the run."""

        notes: list[str] = []
        for stage in self.stages:
            notes.extend(stage.get("translations", []))
        return notes

    def stage(self, module_key: str) -> dict[str, Any] | None:
        for entry in self.stages:
            if entry.get("module") == module_key:
                return entry
        return None

    def stage_ok(self, module_key: str) -> bool:
        entry = self.stage(module_key)
        return bool(entry and entry.get("ok"))

    def as_dict(self) -> dict[str, Any]:
        """Run metadata only - artifact payloads are served by the API."""

        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "ok": self.ok,
            "stages": self.stages,
            "translations": self.translations,
        }


def load_snapshot(
    run_id: str,
    started_at: str,
    finished_at: str,
    ok: bool,
    stages: list[dict[str, Any]],
    workspace: Path,
) -> Snapshot:
    """Assemble a snapshot from the artifacts on disk after a run."""

    return Snapshot(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        ok=ok,
        stages=stages,
        twin=read_json(workspace / "module2_twin_state.json"),
        forecast=read_json(ARTIFACTS.forecast_output),
        forecast_series=read_json(workspace / "module3_forecast_series.json"),
        agents=read_json(workspace / "module4_agent_detail.json"),
        scenarios=read_json(workspace / "module5_detail.json"),
        optimization_report=read_json(ARTIFACTS.optimization_report),
        optimized_state=read_json(ARTIFACTS.optimized_state),
        optimization_recommendations=read_json(ARTIFACTS.optimization_recommendations),
        shap=read_json(ARTIFACTS.shap_explanations),
        feature_importance=read_json(ARTIFACTS.feature_importance),
        anomalies=read_json(ARTIFACTS.anomaly_report),
        performance=read_json(ARTIFACTS.performance_report),
        monitoring=read_json(ARTIFACTS.model_monitoring),
        retraining=read_json(ARTIFACTS.retraining_report),
        final_report=read_json(ARTIFACTS.final_report),
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
