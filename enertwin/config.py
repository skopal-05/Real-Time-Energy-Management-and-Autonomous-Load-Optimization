"""Filesystem layout and runtime settings for the integration layer.

Every path a module owns is declared here once. Nothing in this file changes a
module — it only records where each module already reads and writes.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# Module roots. These names are the on-disk folder names and must not change.
# --------------------------------------------------------------------------

MODULE_ROOTS: dict[str, Path] = {
    "module1": PROJECT_ROOT / "Module 1 - Data Acquisition",
    "module2": PROJECT_ROOT / "Module 2 - Digital Twin",
    "module3": PROJECT_ROOT / "Module 3 - Forecasting",
    "module4": PROJECT_ROOT / "Module 4 - Multi-Agent Intelligence",
    "module5": PROJECT_ROOT / "Module 5 - Scenario Simulation",
    "module6": PROJECT_ROOT / "Module 6 - Optimization Engine",
    "module7": PROJECT_ROOT / "Module 7 - Explainable AI & Performance Evaluation",
}

MODULE_TITLES: dict[str, str] = {
    "module1": "Data Acquisition",
    "module2": "Digital Twin",
    "module3": "Forecasting",
    "module4": "Multi-Agent Intelligence",
    "module5": "Scenario Simulation",
    "module6": "Optimization Engine",
    "module7": "Explainable AI & Performance Evaluation",
}

# --------------------------------------------------------------------------
# Artifacts each module produces natively. The chain between modules 3-7 is
# already file-based; these constants simply name the files the modules
# themselves read and write.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Artifacts:
    """Canonical locations of every module output the platform consumes."""

    # Module 1 - raw and cleaned telemetry
    raw_data_dir: Path = MODULE_ROOTS["module1"] / "outputs"
    cleaned_data_dir: Path = MODULE_ROOTS["module1"] / "outputs" / "cleaned_data"
    normalized_data_dir: Path = MODULE_ROOTS["module1"] / "outputs" / "normalized_data"

    # Module 2 - live twin snapshots (written by the platform driver, see
    # adapters/drivers/m2_sync.py; the module's own state folder is untouched)
    twin_states_dir: Path = MODULE_ROOTS["module2"] / "outputs" / "states"

    # Module 3
    forecast_output: Path = MODULE_ROOTS["module3"] / "outputs" / "forecast_output.json"

    # Module 4
    agent_recommendations: Path = (
        MODULE_ROOTS["module4"] / "outputs" / "recommendations" / "recommendations.json"
    )
    agent_report: Path = (
        MODULE_ROOTS["module4"] / "outputs" / "reports" / "intelligence_report.json"
    )
    agent_optimized_state: Path = (
        MODULE_ROOTS["module4"] / "outputs" / "optimized_states" / "optimized_state.json"
    )

    # Module 5
    scenarios: Path = (
        MODULE_ROOTS["module5"] / "outputs" / "scenarios" / "generated_scenarios.json"
    )
    scenario_comparison: Path = (
        MODULE_ROOTS["module5"] / "outputs" / "comparisons" / "scenario_comparison.json"
    )
    best_scenario: Path = (
        MODULE_ROOTS["module5"] / "outputs" / "best_scenario" / "best_scenario.json"
    )
    simulation_report: Path = (
        MODULE_ROOTS["module5"] / "outputs" / "reports" / "simulation_report.json"
    )

    # Module 6
    optimization_report: Path = (
        MODULE_ROOTS["module6"] / "outputs" / "reports" / "optimization_report.json"
    )
    optimized_state: Path = (
        MODULE_ROOTS["module6"] / "outputs" / "optimized_states" / "optimized_state.json"
    )
    optimization_recommendations: Path = (
        MODULE_ROOTS["module6"] / "outputs" / "recommendations" / "recommendations.json"
    )

    # Module 7
    final_report: Path = (
        MODULE_ROOTS["module7"] / "outputs" / "reports" / "final_integration_report.json"
    )
    performance_report: Path = (
        MODULE_ROOTS["module7"] / "outputs" / "performance" / "performance_report.json"
    )
    final_performance: Path = (
        MODULE_ROOTS["module7"] / "outputs" / "performance" / "final_performance.json"
    )
    model_monitoring: Path = (
        MODULE_ROOTS["module7"] / "outputs" / "performance" / "model_monitoring.json"
    )
    retraining_report: Path = (
        MODULE_ROOTS["module7"] / "outputs" / "performance" / "retraining_report.json"
    )
    shap_explanations: Path = (
        MODULE_ROOTS["module7"] / "outputs" / "explanations" / "shap_explanations.json"
    )
    feature_importance: Path = (
        MODULE_ROOTS["module7"] / "outputs" / "explanations" / "feature_importance.json"
    )
    anomaly_report: Path = (
        MODULE_ROOTS["module7"] / "outputs" / "anomalies" / "anomaly_report.json"
    )
    anomaly_status: Path = (
        MODULE_ROOTS["module7"] / "outputs" / "anomalies" / "anomaly_status.json"
    )


ARTIFACTS = Artifacts()

# --------------------------------------------------------------------------
# Platform-owned storage. Never written inside a module folder.
# --------------------------------------------------------------------------

PLATFORM_DATA_DIR = Path(
    os.environ.get("ENERTWIN_DATA_DIR", PROJECT_ROOT / "enertwin_data")
)
RUNS_DIR = PLATFORM_DATA_DIR / "runs"
SNAPSHOT_FILE = PLATFORM_DATA_DIR / "latest_snapshot.json"
TWIN_STREAM_FILE = PLATFORM_DATA_DIR / "twin_stream.json"


def ensure_platform_dirs() -> None:
    """Create the platform's own storage directories."""

    for directory in (PLATFORM_DATA_DIR, RUNS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# Runtime settings
# --------------------------------------------------------------------------


def module_python() -> str:
    """The interpreter used to execute module subprocesses.

    Defaults to the interpreter running the platform, which is the project
    virtual environment in every supported setup.
    """

    return os.environ.get("ENERTWIN_PYTHON", sys.executable)


#: Seconds before a module subprocess is considered hung.
MODULE_TIMEOUT_SECONDS = int(os.environ.get("ENERTWIN_MODULE_TIMEOUT", "900"))

#: How many Module 1 CSV rows the digital twin advances through per pipeline run.
#: 96 covers the whole of Module 1's cleaned dataset - 24 hours at 15-minute
#: resolution. Anything less leaves part of the day unsynchronized, and Module 7
#: scores its anomalies over the entire dataset, so its detections could not
#: then be traced back to a twin reading.
TWIN_SYNC_STEPS = int(os.environ.get("ENERTWIN_TWIN_SYNC_STEPS", "96"))

#: Seconds between automatic background pipeline runs. 0 disables the scheduler.
PIPELINE_INTERVAL_SECONDS = int(os.environ.get("ENERTWIN_PIPELINE_INTERVAL", "0"))

#: Whether a pipeline run should regenerate Module 1's synthetic dataset.
#: Off by default: Module 1's outputs are version-controlled inputs for the
#: rest of the chain, and regenerating them rewrites tracked files.
REGENERATE_DATA = os.environ.get("ENERTWIN_REGENERATE_DATA", "0") == "1"

#: CORS origins permitted to call the API. Covers the Next.js dev server's
#: default port and the fallback used when 3000 is already taken.
_DEFAULT_CORS = ",".join(
    f"http://{host}:{port}"
    for host in ("localhost", "127.0.0.1")
    for port in (3000, 3010)
)

CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ENERTWIN_CORS_ORIGINS", _DEFAULT_CORS).split(",")
    if origin.strip()
]
