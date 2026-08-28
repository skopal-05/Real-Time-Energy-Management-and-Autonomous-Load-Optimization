"""Runnable manual verification for all Week 4 Person 1 and Person 2 work."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from contracts import AgentRecommendation
from production_agents import (
    CostOptimizationAgent,
    EnergyAllocator,
    LoadBalancingAgent,
    ProductionScheduler,
)
from renewable_agents import (
    BatteryManagementAgent,
    GridInteractionAgent,
    RenewableAgent,
    SolarDispatchAgent,
)


Check = tuple[str, Callable[[], Any]]


def require(condition: bool, message: str) -> None:
    """Raise a readable assertion when a manual check fails."""

    if not condition:
        raise AssertionError(message)


def expect_value_error(callback: Callable[[], Any]) -> None:
    """Confirm that invalid input is rejected."""

    try:
        callback()
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def check_contract() -> None:
    result = AgentRecommendation(
        agent="manual_check",
        action="verify",
        priority="low",
        reason="Contract smoke test.",
        setpoints={"target_kw": 10.0},
        expected_impact={"saving_inr": 2.0},
        constraints=("test constraint",),
    )
    encoded = json.dumps(result.as_dict())
    require('"agent": "manual_check"' in encoded, "agent field was not serialized")
    require(result.as_dict()["constraints"] == ["test constraint"], "constraints must be a list")


def check_cost_peak_shift() -> None:
    result = CostOptimizationAgent().optimize(
        {
            "production_load_kw": 100,
            "renewable_generation_kw": 20,
            "tariff_inr_kwh": 10,
            "off_peak_tariff_inr_kwh": 5,
            "flexible_load_fraction": 0.15,
        }
    )
    require(result.action == "shift_flexible_load", "peak load was not shifted")
    require(result.setpoints["load_to_shift_kw"] == 15, "incorrect shifted load")
    require(result.expected_impact["estimated_savings_inr"] == 75, "incorrect savings")


def check_cost_low_tariff() -> None:
    result = CostOptimizationAgent().optimize(
        {
            "production_load_kw": 100,
            "tariff_inr_kwh": 6,
            "off_peak_tariff_inr_kwh": 4,
        }
    )
    require(result.action == "maintain_schedule", "low tariff should not trigger shifting")


def check_load_balance_full_supply() -> None:
    result = LoadBalancingAgent().balance(
        {
            "line_a": {"requested_power_kw": 60},
            "line_b": {"requested_power_kw": 40},
        },
        120,
    )
    targets = result.setpoints["line_power_targets_kw"]
    require(targets == {"line_a": 60.0, "line_b": 40.0}, "requests were not fully served")


def check_load_balance_shortage() -> None:
    result = LoadBalancingAgent().balance(
        {
            "line_a": {
                "requested_power_kw": 70,
                "minimum_power_kw": 30,
                "priority_weight": 2,
            },
            "line_b": {
                "requested_power_kw": 50,
                "minimum_power_kw": 20,
                "priority_weight": 1,
            },
        },
        90,
    )
    targets = result.setpoints["line_power_targets_kw"]
    require(abs(sum(targets.values()) - 90) < 0.01, "allocation exceeds available power")
    require(targets["line_a"] > targets["line_b"], "priority weighting was not applied")


def check_scheduler_feasible() -> None:
    result = ProductionScheduler().schedule(
        [
            {"job_id": "job-1", "energy_kwh": 20, "deadline_slot": 1},
            {"job_id": "job-2", "energy_kwh": 10, "deadline_slot": 1},
        ],
        [
            {
                "slot_id": "peak",
                "capacity_kwh": 40,
                "renewable_kwh": 0,
                "tariff_inr_kwh": 10,
            },
            {
                "slot_id": "solar",
                "capacity_kwh": 40,
                "renewable_kwh": 30,
                "tariff_inr_kwh": 7,
            },
        ],
    )
    require(result.action == "schedule_production", "feasible jobs were not scheduled")
    require(
        all(item["slot_id"] == "solar" for item in result.setpoints["assignments"]),
        "scheduler did not choose the renewable slot",
    )


def check_scheduler_infeasible() -> None:
    result = ProductionScheduler().schedule(
        [{"job_id": "large", "energy_kwh": 50, "deadline_slot": 0}],
        [{"slot_id": "now", "capacity_kwh": 20, "tariff_inr_kwh": 5}],
    )
    require(result.priority == "high", "unscheduled job did not raise priority")
    require(result.setpoints["unscheduled_jobs"] == ["large"], "missing unscheduled job")


def check_energy_allocation() -> None:
    result = EnergyAllocator().allocate(
        {
            "production_demand_kw": 100,
            "renewable_available_kw": 30,
            "battery_discharge_available_kw": 25,
            "grid_import_limit_kw": 100,
            "battery_cost_inr_kwh": 2,
            "grid_tariff_inr_kwh": 8,
        }
    )
    require(result.setpoints["renewable_to_production_kw"] == 30, "renewable not first")
    require(result.setpoints["battery_to_production_kw"] == 25, "battery not dispatched")
    require(result.setpoints["grid_to_production_kw"] == 45, "incorrect grid allocation")


def check_energy_shortfall() -> None:
    result = EnergyAllocator().allocate(
        {
            "production_demand_kw": 100,
            "renewable_available_kw": 10,
            "battery_discharge_available_kw": 10,
            "grid_import_limit_kw": 20,
        }
    )
    require(result.priority == "critical", "shortfall must be critical")
    require(result.setpoints["unserved_production_kw"] == 60, "incorrect shortfall")


def check_renewable_dispatch() -> None:
    result = RenewableAgent().optimize(
        {
            "plant_demand_kw": 100,
            "solar_available_kw": 55,
            "battery_discharge_available_kw": 35,
            "battery_reserve_kw": 10,
        }
    )
    require(result.setpoints["solar_to_load_kw"] == 55, "solar dispatch is incorrect")
    require(result.setpoints["battery_to_load_kw"] == 25, "reserve was not preserved")
    require(result.setpoints["grid_to_load_kw"] == 20, "grid residual is incorrect")


def check_solar_dispatch() -> None:
    result = SolarDispatchAgent().dispatch(
        {
            "solar_generation_kw": 100,
            "site_demand_kw": 40,
            "battery_charge_headroom_kw": 25,
            "battery_charge_limit_kw": 20,
            "grid_export_limit_kw": 30,
        }
    )
    expected = {
        "solar_to_load_kw": 40.0,
        "solar_to_battery_kw": 20.0,
        "solar_to_grid_kw": 30.0,
        "solar_curtailed_kw": 10.0,
    }
    require(result.setpoints == expected, "solar dispatch order or limits are incorrect")


def check_battery_charge() -> None:
    result = BatteryManagementAgent().manage(
        {
            "state_of_charge_percent": 50,
            "capacity_kwh": 100,
            "renewable_surplus_kw": 30,
            "maximum_charge_kw": 20,
        }
    )
    require(result.action == "charge_from_renewable", "battery did not charge")
    require(result.setpoints["projected_soc_percent"] == 70, "projected SOC is incorrect")


def check_battery_discharge() -> None:
    result = BatteryManagementAgent().manage(
        {
            "state_of_charge_percent": 60,
            "capacity_kwh": 100,
            "site_deficit_kw": 30,
            "tariff_inr_kwh": 10,
            "maximum_discharge_kw": 25,
        }
    )
    require(result.action == "discharge_to_load", "battery did not discharge at peak")
    require(result.setpoints["battery_discharge_kw"] == 25, "discharge limit not applied")


def check_battery_reserve() -> None:
    result = BatteryManagementAgent().manage(
        {
            "state_of_charge_percent": 20,
            "capacity_kwh": 100,
            "site_deficit_kw": 30,
            "tariff_inr_kwh": 10,
        }
    )
    require(result.action == "protect_reserve", "minimum SOC was not protected")
    require(result.setpoints["battery_discharge_kw"] == 0, "reserve was discharged")


def check_grid_import() -> None:
    result = GridInteractionAgent().interact(
        {
            "net_demand_kw": 70,
            "grid_import_limit_kw": 100,
            "tariff_inr_kwh": 6,
        }
    )
    require(result.setpoints["grid_import_kw"] == 70, "grid import is incorrect")
    require(result.setpoints["unserved_load_kw"] == 0, "unexpected unserved load")


def check_grid_export() -> None:
    result = GridInteractionAgent().interact(
        {
            "net_demand_kw": -50,
            "grid_export_limit_kw": 30,
            "export_price_inr_kwh": 4,
        }
    )
    require(result.setpoints["grid_export_kw"] == 30, "export limit not applied")
    require(result.setpoints["curtailed_export_kw"] == 20, "curtailment is incorrect")


def check_grid_overload() -> None:
    result = GridInteractionAgent().interact(
        {
            "net_demand_kw": 120,
            "grid_import_limit_kw": 80,
            "tariff_inr_kwh": 6,
        }
    )
    require(result.priority == "critical", "grid overload must be critical")
    require(result.setpoints["unserved_load_kw"] == 40, "grid shortfall is incorrect")


def check_invalid_inputs() -> None:
    expect_value_error(
        lambda: CostOptimizationAgent().optimize(
            {"production_load_kw": -1, "tariff_inr_kwh": 5}
        )
    )
    expect_value_error(
        lambda: SolarDispatchAgent().dispatch(
            {"solar_generation_kw": -1, "site_demand_kw": 10}
        )
    )
    expect_value_error(
        lambda: BatteryManagementAgent().manage(
            {"state_of_charge_percent": 101, "capacity_kwh": 100}
        )
    )


CHECKS: tuple[Check, ...] = (
    ("Shared recommendation contract", check_contract),
    ("Cost optimizer - peak shift", check_cost_peak_shift),
    ("Cost optimizer - low tariff", check_cost_low_tariff),
    ("Load balancer - full supply", check_load_balance_full_supply),
    ("Load balancer - shortage", check_load_balance_shortage),
    ("Production scheduler - feasible", check_scheduler_feasible),
    ("Production scheduler - infeasible", check_scheduler_infeasible),
    ("Energy allocator - normal dispatch", check_energy_allocation),
    ("Energy allocator - supply shortfall", check_energy_shortfall),
    ("Renewable agent - reserve-aware dispatch", check_renewable_dispatch),
    ("Solar dispatch - load, battery, grid, curtailment", check_solar_dispatch),
    ("Battery manager - renewable charging", check_battery_charge),
    ("Battery manager - peak discharge", check_battery_discharge),
    ("Battery manager - reserve protection", check_battery_reserve),
    ("Grid agent - import", check_grid_import),
    ("Grid agent - export", check_grid_export),
    ("Grid agent - import overload", check_grid_overload),
    ("Invalid input rejection", check_invalid_inputs),
)


def main() -> None:
    passed = 0
    print("WEEK 4 PERSON 1 AND PERSON 2 MANUAL VERIFICATION")
    print("=" * 58)
    for label, callback in CHECKS:
        try:
            callback()
        except Exception as exc:
            print(f"[FAIL] {label}: {type(exc).__name__}: {exc}")
        else:
            passed += 1
            print(f"[PASS] {label}")

    print("=" * 58)
    print(f"Passed: {passed}/{len(CHECKS)}")
    if passed != len(CHECKS):
        raise SystemExit(1)
    print("RESULT: ALL MANUAL CHECKS PASSED")


if __name__ == "__main__":
    main()
