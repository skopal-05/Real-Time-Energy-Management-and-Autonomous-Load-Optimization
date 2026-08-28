"""Reusable operating templates for Week 5 what-if scenarios."""

from __future__ import annotations


SCENARIO_TEMPLATES = (
    {
        "scenario_id": "baseline",
        "name": "Forecast Baseline",
        "description": (
            "Forecast operating point with no optimization actions."
        ),
        "load_factor": 1.0,
        "renewable_factor": 1.0,
        "apply_agent_targets": False,
        "export_limit_kw": 100.0,
        "battery_mode": "standby",
    },
    {
        "scenario_id": "agent_optimized",
        "name": "Agent Optimized",
        "description": (
            "Applies feasible Module 4 equipment and dispatch setpoints."
        ),
        "load_factor": 1.0,
        "renewable_factor": 1.0,
        "apply_agent_targets": True,
        "export_limit_kw": 100.0,
        "battery_mode": "recommendation",
    },
    {
        "scenario_id": "renewable_first",
        "name": "Renewable Priority",
        "description": (
            "Prioritizes local renewable use, battery charging, and export."
        ),
        "load_factor": 0.97,
        "renewable_factor": 1.0,
        "apply_agent_targets": True,
        "export_limit_kw": 100.0,
        "battery_mode": "charge_surplus",
    },
    {
        "scenario_id": "cost_saver",
        "name": "Cost Saver",
        "description": (
            "Combines agent targets with flexible electrical load reduction."
        ),
        "load_factor": 0.85,
        "renewable_factor": 1.0,
        "apply_agent_targets": True,
        "export_limit_kw": 100.0,
        "battery_mode": "charge_surplus",
    },
    {
        "scenario_id": "resilience",
        "name": "Renewable Shortfall Resilience",
        "description": (
            "Tests reduced renewable availability while preserving "
            "a battery reserve."
        ),
        "load_factor": 0.90,
        "renewable_factor": 0.50,
        "apply_agent_targets": True,
        "export_limit_kw": 0.0,
        "battery_mode": "discharge_deficit",
    },
)