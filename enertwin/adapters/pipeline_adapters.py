"""One adapter per frozen module.

Each adapter records, in its docstring, exactly how the module is invoked and
why. Read together they are the full inventory of how the platform touches the
seven modules - and the guarantee that it only ever runs them.
"""

from __future__ import annotations

import json
from pathlib import Path

from enertwin.adapters.base import DRIVERS, RunContext, StageResult
from enertwin.config import ARTIFACTS
from enertwin.runner import ModuleProcessError, run_module


def _artifact_map(**paths: Path) -> dict[str, str]:
    return {name: str(path) for name, path in paths.items()}


def _read_json(path: Path) -> dict:
    """Read an artifact a stage just produced, or ``{}`` when unreadable."""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


class Module1DataAcquisition:
    """Module 1 - Data Acquisition.

    Invoked through its own ``main.py``, which runs the full
    generate -> validate -> clean -> feature-engineer -> normalize pipeline.

    Skipped by default. Module 1's outputs are version-controlled and are the
    input every other module reads; regenerating them rewrites tracked files
    with a fresh synthetic dataset. Enable with ``ENERTWIN_REGENERATE_DATA=1``
    or ``RunContext(regenerate_data=True)``.
    """

    module_key = "module1"

    def run(self, context: RunContext) -> StageResult:
        artifacts = _artifact_map(
            raw_data=ARTIFACTS.raw_data_dir,
            cleaned_data=ARTIFACTS.cleaned_data_dir,
        )

        if not context.regenerate_data:
            return StageResult(
                module_key=self.module_key,
                ok=True,
                detail="using the existing Module 1 dataset (regeneration disabled)",
                artifacts=artifacts,
            )

        result = run_module(self.module_key, "main.py", check=False)
        return StageResult.from_process(
            self.module_key, result, artifacts=artifacts
        )


class Module2DigitalTwin:
    """Module 2 - Digital Twin.

    Invoked through the platform driver ``drivers/m2_sync.py``, which runs
    inside the module folder and composes the module's own twin classes and
    ``CSVLoader``.

    A driver is needed because Module 2's own entry point, ``run_realtime.py``,
    loops forever and cannot be called by a request-driven backend. The driver
    performs a bounded number of the same ``sync_once()`` rounds. See the
    driver's docstring for the Module 1 dataset choice and how rejected sensor
    readings are handled.
    """

    module_key = "module2"

    def run(self, context: RunContext) -> StageResult:
        destination = context.path("module2_twin_state.json")
        result = run_module(
            self.module_key,
            DRIVERS / "m2_sync.py",
            args=[
                str(destination),
                str(context.twin_steps),
                f"--source={context.twin_source}",
            ],
            check=False,
        )

        translations: list[str] = []
        detail: str | None = None
        degraded = False
        if result.ok and destination.is_file():
            document = _read_json(destination)
            rejected = document.get("rejected_reading_count", 0)
            degraded = bool(rejected)
            detail = (
                f"{document.get('steps_published', 0)} intervals synchronized "
                f"across 8 twins from the {document.get('source', '?')} dataset"
            )
            if rejected:
                detail += f"; {rejected} readings rejected"
            if context.twin_source == "cleaned":
                translations.append(
                    "twins driven from Module 1's cleaned dataset; the raw "
                    "dataset violates Module 2's declared operating ranges"
                )
            if rejected:
                translations.append(
                    f"{rejected} sensor readings rejected by twin validation "
                    "and reported as data-quality events"
                )

        return StageResult.from_process(
            self.module_key,
            result,
            translations=translations,
            artifacts=_artifact_map(twin_state=destination),
            detail=detail,
            degraded=degraded,
        )


class Module3Forecasting:
    """Module 3 - Forecasting.

    Invoked through ``drivers/m3_forecast.py``, which runs inside the module
    folder and calls ``FutureStateGenerator``'s per-asset forecast methods and
    ``LoadForecast`` - the same public API ``integration/run_forecasting.py``
    uses.

    A driver is needed because ``run_forecasting.py`` forecasts from a
    hard-coded example state rather than live twin state, and because feeding
    real per-asset telemetry through one flat dictionary would cross-wire
    sensors that several assets share by name. See the driver's docstring.

    Writes Module 3's own ``outputs/forecast_output.json`` in Module 3's own
    format, so Modules 4-7 pick it up through their existing default paths.
    """

    module_key = "module3"

    def run(self, context: RunContext) -> StageResult:
        twin_state = context.path("module2_twin_state.json")
        series = context.path("module3_forecast_series.json")

        result = run_module(
            self.module_key,
            DRIVERS / "m3_forecast.py",
            args=[str(twin_state), str(series)],
            check=False,
        )
        detail: str | None = None
        if result.ok and series.is_file():
            document = _read_json(series)
            models = document.get("models", {})
            distinct = {entry.get("emits") for entry in models.values()}
            detail = (
                f"{len(models)} assets scored by {len(distinct)} Random Forest "
                f"models over {document.get('step_count', 0)} intervals"
            )

        return StageResult.from_process(
            self.module_key,
            result,
            translations=[
                "each asset's twin state routed to its own forecasting model "
                "instead of one shared flat state dictionary"
            ]
            if result.ok
            else [],
            artifacts=_artifact_map(
                forecast=ARTIFACTS.forecast_output, forecast_series=series
            ),
            detail=detail,
        )


class Module4MultiAgent:
    """Module 4 - Multi-Agent Intelligence.

    Invoked through ``drivers/m4_agents.py``, which runs inside the module
    folder and follows the sequence documented by the module's own
    ``integration/integration_test.py``: ``AgentController`` ->
    ``AgentValidator`` -> ``OutputManager``.

    A driver is needed only because Module 4 ships no ``__main__``.
    """

    module_key = "module4"

    def run(self, context: RunContext) -> StageResult:
        agent_detail = context.path("module4_agent_detail.json")
        adapted = context.path("module4_adapted_forecast.json")
        result = run_module(
            self.module_key,
            DRIVERS / "m4_agents.py",
            args=[str(ARTIFACTS.forecast_output), str(adapted), str(agent_detail)],
            check=False,
        )

        translations: list[str] = []
        detail: str | None = None
        degraded = False
        if result.ok and agent_detail.is_file():
            document = _read_json(agent_detail)
            translations = list(document.get("boundary_translations", []))
            failed = document.get("failed_agents", [])
            detail = (
                f"{document.get('recommendation_count', 0)} decisions from "
                f"{len(document.get('registered_agents', []))} agents and "
                f"{len(document.get('rules', []))} rules"
            )
            degraded = bool(failed)
            if failed:
                detail += f"; {len(failed)} agent(s) errored"
                translations.append(
                    f"{len(failed)} agent(s) returned an execution error: "
                    f"{', '.join(failed)}"
                )

        return StageResult.from_process(
            self.module_key,
            result,
            translations=translations,
            artifacts=_artifact_map(
                recommendations=ARTIFACTS.agent_recommendations,
                report=ARTIFACTS.agent_report,
                optimized_state=ARTIFACTS.agent_optimized_state,
                agent_detail=agent_detail,
                adapted_forecast=adapted,
            ),
            detail=detail,
            degraded=degraded,
        )


class Module5ScenarioSimulation:
    """Module 5 - Scenario Simulation.

    Invoked through ``drivers/m5_scenarios.py``, which runs inside the module
    folder and calls the module's own ``ScenarioController.run()``.

    A driver is needed for the Module 3 -> Module 5 boundary translation: the
    two modules disagree on whether battery power counts as renewable
    generation, and Module 5's validator rejects the negative value Module 3
    emits while the battery charges. See the driver's docstring.
    """

    module_key = "module5"

    def run(self, context: RunContext) -> StageResult:
        adapted = context.path("module5_adapted_forecast.json")
        scenario_detail = context.path("module5_detail.json")

        result = run_module(
            self.module_key,
            DRIVERS / "m5_scenarios.py",
            args=[
                str(ARTIFACTS.forecast_output),
                str(ARTIFACTS.agent_recommendations),
                str(adapted),
                str(scenario_detail),
                str(context.horizon_hours),
            ],
            check=False,
        )

        translations: list[str] = []
        detail: str | None = None
        if result.ok and scenario_detail.is_file():
            document = _read_json(scenario_detail)
            translations = list(document.get("boundary_translations", []))
            report = (document.get("result", {}) or {}).get("report", {}) or {}
            if report:
                detail = (
                    f"{report.get('scenario_count', 0)} scenarios simulated; "
                    f"best = {report.get('best_scenario_name', '-')} "
                    f"({float(report.get('best_score', 0)):.1f}/100)"
                )

        return StageResult.from_process(
            self.module_key,
            result,
            translations=translations,
            artifacts=_artifact_map(
                scenarios=ARTIFACTS.scenarios,
                comparison=ARTIFACTS.scenario_comparison,
                best_scenario=ARTIFACTS.best_scenario,
                report=ARTIFACTS.simulation_report,
                adapted_forecast=adapted,
                detail=scenario_detail,
            ),
            detail=detail,
        )


class Module6Optimization:
    """Module 6 - Optimization Engine.

    Invoked through the module's own entry point,
    ``integration/optimization_controller.py``. It already resolves Module 4's
    and Module 5's outputs from their default locations, which is exactly where
    the previous stages wrote them. No driver and no translation are needed.
    """

    module_key = "module6"

    def run(self, context: RunContext) -> StageResult:
        result = run_module(
            self.module_key, "integration/optimization_controller.py", check=False
        )

        detail: str | None = None
        degraded = False
        if result.ok:
            report = _read_json(ARTIFACTS.optimization_report)
            summary = report.get("summary", {})
            if summary:
                algorithm = report.get("algorithm", {})
                feasible = bool(summary.get("feasible"))
                degraded = not feasible
                detail = (
                    f"GA over {algorithm.get('generations', '?')} generations: "
                    f"{'feasible' if feasible else 'infeasible'}; cost delta "
                    f"₹{float(summary.get('cost_saving_inr') or 0):,.2f}, carbon "
                    f"delta {float(summary.get('emissions_avoided_kg_co2e') or 0):,.1f} "
                    "kg CO₂e"
                )

        return StageResult.from_process(
            self.module_key,
            result,
            artifacts=_artifact_map(
                report=ARTIFACTS.optimization_report,
                optimized_state=ARTIFACTS.optimized_state,
                recommendations=ARTIFACTS.optimization_recommendations,
            ),
            detail=detail,
            degraded=degraded,
        )


class Module7Explainability:
    """Module 7 - Explainable AI & Performance Evaluation.

    Invoked through both of the module's own entry points, in the order the
    module documents:

    1. ``run_person_1_2.py`` - SHAP explanations, feature importance, Isolation
       Forest anomaly detection, model monitoring and retraining assessment.
    2. ``integration/final_controller.py`` - the Modules 3-7 final report.

    Both resolve their inputs from default paths already populated by the
    earlier stages. No driver and no translation are needed.
    """

    module_key = "module7"

    def run(self, context: RunContext) -> StageResult:
        artifacts = _artifact_map(
            final_report=ARTIFACTS.final_report,
            performance=ARTIFACTS.performance_report,
            final_performance=ARTIFACTS.final_performance,
            monitoring=ARTIFACTS.model_monitoring,
            retraining=ARTIFACTS.retraining_report,
            shap=ARTIFACTS.shap_explanations,
            feature_importance=ARTIFACTS.feature_importance,
            anomalies=ARTIFACTS.anomaly_report,
        )

        analysis = run_module(self.module_key, "run_person_1_2.py", check=False)
        if not analysis.ok:
            return StageResult.from_process(
                self.module_key, analysis, artifacts=artifacts
            )

        final = run_module(
            self.module_key, "integration/final_controller.py", check=False
        )
        detail: str | None = None
        if final.ok:
            shap = _read_json(ARTIFACTS.shap_explanations).get("models", {})
            anomalies = _read_json(ARTIFACTS.anomaly_report)
            summary = _read_json(ARTIFACTS.performance_report).get(
                "forecasting_summary", {}
            )
            retraining = _read_json(ARTIFACTS.retraining_report).get("models", {})
            triggered = sum(
                1 for item in retraining.values() if item.get("triggered")
            )
            promoted = sum(1 for item in retraining.values() if item.get("promoted"))

            detail = (
                f"SHAP for {len(shap)} models; "
                f"{anomalies.get('anomaly_count', 0)} of "
                f"{anomalies.get('record_count', 0)} windows flagged"
            )
            if summary.get("mean_r2") is not None:
                detail += f"; mean held-out R² {float(summary['mean_r2']):.3f}"
            if retraining:
                detail += (
                    f"; retraining evaluated for {triggered}/{len(retraining)} "
                    f"models, {promoted} promoted"
                )

        stage = StageResult.from_process(
            self.module_key, final, artifacts=artifacts, detail=detail
        )
        stage.duration_seconds += analysis.duration_seconds
        return stage


#: Execution order. This is the architecture diagram, in code.
PIPELINE: tuple[object, ...] = (
    Module1DataAcquisition(),
    Module2DigitalTwin(),
    Module3Forecasting(),
    Module4MultiAgent(),
    Module5ScenarioSimulation(),
    Module6Optimization(),
    Module7Explainability(),
)

__all__ = [
    "PIPELINE",
    "Module1DataAcquisition",
    "Module2DigitalTwin",
    "Module3Forecasting",
    "Module4MultiAgent",
    "Module5ScenarioSimulation",
    "Module6Optimization",
    "Module7Explainability",
    "ModuleProcessError",
]
