"""End-to-end orchestration: all seven modules run and hand off correctly."""

from __future__ import annotations

from enertwin.config import ARTIFACTS
from enertwin.orchestration import Snapshot

MODULE_ORDER = [
    "module1",
    "module2",
    "module3",
    "module4",
    "module5",
    "module6",
    "module7",
]


def test_every_stage_succeeds(snapshot: Snapshot) -> None:
    failed = [
        f"{stage['module']}: {stage['detail']}"
        for stage in snapshot.stages
        if not stage["ok"]
    ]
    assert snapshot.ok and not failed, "pipeline stages failed:\n  " + "\n  ".join(
        failed
    )


def test_stages_run_in_architecture_order(snapshot: Snapshot) -> None:
    assert [stage["module"] for stage in snapshot.stages] == MODULE_ORDER


def test_every_module_artifact_is_loaded(snapshot: Snapshot) -> None:
    for name in (
        "twin",
        "forecast",
        "forecast_series",
        "agents",
        "scenarios",
        "optimization_report",
        "optimized_state",
        "shap",
        "feature_importance",
        "anomalies",
        "performance",
        "final_report",
    ):
        assert getattr(snapshot, name), f"missing artifact: {name}"


def test_module3_writes_its_own_artifact_in_its_own_format(snapshot: Snapshot) -> None:
    """Modules 4-7 find the forecast at Module 3's default path, unchanged."""

    assert ARTIFACTS.forecast_output.is_file()
    forecast = snapshot.forecast
    assert set(forecast) >= {"future_state", "energy_forecast"}
    for key in ("compressor_power_kw", "hvac_power_kw", "inverter_power_kw", "fuel_flow_m3_hr"):
        assert key in forecast["future_state"], key
    for key in ("total_load_kw", "renewable_generation_kw", "boiler_fuel_flow_m3_hr"):
        assert key in forecast["energy_forecast"], key


def test_twin_synchronizes_all_eight_assets(snapshot: Snapshot) -> None:
    twin = snapshot.twin
    assert len(twin["assets"]) == 8
    assert twin["steps_published"] == 96, "expected a full 24-hour day of state"
    for asset in twin["assets"]:
        assert twin["states"][asset], f"{asset} has no state"


def test_cleaned_dataset_produces_no_rejected_readings(snapshot: Snapshot) -> None:
    """Module 1's cleaned data satisfies every Module 2 operating range."""

    assert snapshot.twin["source"] == "cleaned"
    assert snapshot.twin["rejected_reading_count"] == 0


def test_every_module4_agent_returns_a_real_decision(snapshot: Snapshot) -> None:
    """The Module 3 boundary translation keeps all twelve agents working."""

    errored = [
        item["agent"]
        for item in snapshot.agents["recommendations"]
        if item["action"] == "agent_execution_error"
    ]
    assert not errored, f"agents failed: {errored}"
    assert len(snapshot.agents["registered_agents"]) == 12


def test_module5_ranks_every_required_scenario(snapshot: Snapshot) -> None:
    result = snapshot.scenarios["result"]
    ids = {item["scenario_id"] for item in result["scenarios"]}
    assert ids >= {
        "baseline",
        "agent_optimized",
        "renewable_first",
        "cost_saver",
        "resilience",
    }
    assert result["best_scenario"]["ranking"]["rank"] == 1


def test_module6_reaches_a_feasible_optimum(snapshot: Snapshot) -> None:
    report = snapshot.optimization_report
    assert report["summary"]["feasible"] is True
    assert report["algorithm"]["name"] == "real_valued_genetic_algorithm"
    assert report["algorithm"]["generations"] > 0


def test_module7_explains_every_forecasting_model(snapshot: Snapshot) -> None:
    assert len(snapshot.shap["models"]) == 7
    assert len(snapshot.feature_importance["models"]) == 7
    assert snapshot.anomalies["method"] == "isolation_forest"
    assert snapshot.performance["forecasting_summary"]["model_count"] == 7


def test_boundary_translations_are_recorded(snapshot: Snapshot) -> None:
    """Every reshaping between modules is visible, not silent."""

    notes = snapshot.translations
    assert notes, "expected the platform to record its boundary translations"
    assert any("cleaned dataset" in note for note in notes)
