"""Module 4 agents and Module 5/6 outputs -> the frontend's decision layer.

Recommendations come from two modules and are labelled with their real source:
Module 4's twelve rule-based agents plus its deterministic rule engine, and
Module 6's optimizer. The operating objective is read from the scenario Module 5
ranked first.
"""

from __future__ import annotations

from typing import Any

from enertwin.api.mappers.common import iso, now_iso, number, title_case
from enertwin.orchestration import Snapshot

#: Which assets each Module 4 agent reasons about. Domain metadata about the
#: agents, not a reinterpretation of their output.
AGENT_SCOPE: dict[str, tuple[str, tuple[str, ...]]] = {
    "cost_optimization_agent": (
        "Shifts flexible load away from peak tariff windows.",
        ("line-a", "line-b", "grid"),
    ),
    "load_balancing_agent": (
        "Distributes available power between the two production lines.",
        ("line-a", "line-b"),
    ),
    "production_scheduler": (
        "Places production jobs into slots by tariff and renewable availability.",
        ("line-a", "line-b"),
    ),
    "energy_allocator": (
        "Allocates renewable, battery and grid energy across site demand.",
        ("line-a", "line-b", "compressor", "hvac"),
    ),
    "renewable_agent": (
        "Maximises renewable use against plant demand.",
        ("solar", "battery", "grid"),
    ),
    "solar_dispatch_agent": (
        "Routes solar output between site load, battery charging and export.",
        ("solar", "battery", "grid"),
    ),
    "battery_management_agent": (
        "Schedules charge and discharge within the state-of-charge reserve.",
        ("battery",),
    ),
    "grid_interaction_agent": (
        "Sets import and export against the connection limits and tariff.",
        ("grid",),
    ),
    "hvac_agent": (
        "Holds the zone setpoint at the lowest feasible HVAC power.",
        ("hvac",),
    ),
    "compressor_agent": (
        "Holds air pressure at the lowest feasible compressor power.",
        ("compressor",),
    ),
    "boiler_agent": (
        "Holds the lowest feasible fuel flow that maintains efficiency.",
        ("boiler",),
    ),
    "equipment_health_agent": (
        "Watches health and anomaly scores across the plant.",
        ("line-a", "line-b", "boiler", "compressor", "hvac"),
    ),
    "rule_engine": (
        "Deterministic safety and energy-management rules evaluated every cycle.",
        ("line-a", "line-b", "boiler", "compressor", "hvac", "battery", "grid"),
    ),
}

#: Which asset a Module 6 recommendation's ``equipment`` field refers to.
EQUIPMENT_TO_ASSET: dict[str, str] = {
    "battery": "battery",
    "grid": "grid",
    "compressor": "compressor",
    "hvac": "hvac",
    "boiler": "boiler",
    "production": "line-a",
}

SCENARIO_TO_MODE: dict[str, tuple[str, str]] = {
    "cost_saver": ("cost-optimal", "Cost Optimal"),
    "renewable_first": ("carbon-minimal", "Carbon Minimal"),
    "resilience": ("resilience", "Resilience"),
    "agent_optimized": ("peak-shaving", "Peak Shaving"),
    "baseline": ("resilience", "Baseline"),
}

IMPACT_LABELS: dict[str, tuple[str, str]] = {
    "energy_saving_kwh": ("Energy saved", "kWh"),
    "cost_saving_inr": ("Cost saved", "₹"),
    "emissions_avoided_kg_co2e": ("Emissions avoided", "kg CO₂e"),
    "grid_import_reduction_kw": ("Grid import reduction", "kW"),
    "renewable_absorption_kw": ("Renewable absorbed", "kW"),
    "import_cost_inr_per_hour": ("Import cost", "₹/h"),
    "export_revenue_inr_per_hour": ("Export revenue", "₹/h"),
    "net_grid_cost_inr_per_hour": ("Net grid cost", "₹/h"),
    "fuel_saving_m3_hr": ("Fuel saved", "m³/h"),
    "power_saving_kw": ("Power saved", "kW"),
}


def _impacts(source: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(source, dict):
        return []
    items: list[dict[str, Any]] = []
    for key, raw in source.items():
        label, unit = IMPACT_LABELS.get(key, (title_case(key), ""))
        value = number(source, key)
        items.append({"label": label, "value": round(value, 3) if value is not None else None, "unit": unit})
        del raw
    return items


def build_agents(snapshot: Snapshot) -> list[dict[str, Any]]:
    detail = snapshot.agents or {}
    registered: list[str] = list(detail.get("registered_agents", []))
    rules = detail.get("rules", []) or []
    recommendations = detail.get("recommendations", []) or []
    generated_at = iso(detail.get("generated_at")) or snapshot.finished_at

    decisions_by_agent: dict[str, int] = {}
    for item in recommendations:
        name = item.get("agent")
        if name:
            decisions_by_agent[name] = decisions_by_agent.get(name, 0) + 1

    names = registered + (["rule_engine"] if rules else [])
    agents: list[dict[str, Any]] = []
    for name in names:
        scope, watches = AGENT_SCOPE.get(name, ("Module 4 agent.", ()))
        decisions = decisions_by_agent.get(name, 0)
        agents.append(
            {
                "id": name,
                "name": title_case(name),
                "scope": scope,
                "state": "active" if decisions else "standby",
                # Only the rule engine carries an explicit rule set; the agents
                # encode their logic directly, so their rule count is 0 rather
                # than an invented figure.
                "ruleCount": len(rules) if name == "rule_engine" else 0,
                "decisionsToday": decisions,
                "lastActionAt": generated_at if decisions else None,
                "watches": list(watches),
            }
        )
    return agents


def build_recommendations(snapshot: Snapshot) -> list[dict[str, Any]]:
    detail = snapshot.agents or {}
    generated_at = iso(detail.get("generated_at")) or snapshot.finished_at
    rules_by_action = {
        rule.get("action"): rule for rule in (detail.get("rules") or [])
    }

    results: list[dict[str, Any]] = []

    for index, item in enumerate(detail.get("recommendations", []) or []):
        agent = item.get("agent", "unknown")
        scope, watches = AGENT_SCOPE.get(agent, ("Module 4 agent.", ()))
        action = item.get("action", "")
        rule = rules_by_action.get(action)

        if rule:
            triggered = f"{rule['name']}: {rule['condition']}"
        elif item.get("constraints"):
            triggered = " AND ".join(str(c) for c in item["constraints"])
        else:
            triggered = action

        setpoints = item.get("setpoints") or {}
        rationale = item.get("reason", "")
        if setpoints:
            rendered = ", ".join(
                f"{title_case(key)} = {value}" for key, value in setpoints.items()
            )
            rationale = f"{rationale} Recommended setpoints: {rendered}."

        results.append(
            {
                "id": f"m4-{index:03d}-{agent}",
                "agentId": agent,
                "agentName": title_case(agent),
                "title": title_case(action) if action else title_case(agent),
                "ruleTriggered": triggered,
                "rationale": rationale or scope,
                "targetAssets": list(watches),
                "priority": item.get("priority", "low"),
                # Module 4 emits advisory decisions; nothing in the chain
                # actuates them, so they are reported as pending.
                "status": "pending",
                "createdAt": generated_at,
                "expectedImpact": _impacts(item.get("expected_impact")),
                "sourceModule": (
                    "anomaly" if agent == "equipment_health_agent" else "rules"
                ),
                "origin": "live",
            }
        )

    optimization = snapshot.optimization_recommendations or {}
    optimizer_generated = iso(optimization.get("generated_at")) or generated_at
    for index, item in enumerate(optimization.get("recommendations", []) or []):
        equipment = str(item.get("equipment", ""))
        asset = EQUIPMENT_TO_ASSET.get(equipment)
        current = number(item, "current_value")
        recommended = number(item, "recommended_value")
        unit = item.get("unit", "")

        rationale = item.get("reason", "")
        if current is not None and recommended is not None:
            rationale = (
                f"{rationale} Move from {current:g} {unit} to {recommended:g} {unit}."
            )

        results.append(
            {
                "id": f"m6-{index:03d}-{item.get('recommendation_id', equipment)}",
                "agentId": "optimization_engine",
                "agentName": "Optimization Engine",
                "title": title_case(str(item.get("action", ""))),
                "ruleTriggered": (
                    "genetic algorithm optimum, constraints respected"
                    if item.get("constraints_respected")
                    else "genetic algorithm optimum, constraints violated"
                ),
                "rationale": rationale,
                "targetAssets": [asset] if asset else [],
                "priority": item.get("priority", "low"),
                "status": "pending",
                "createdAt": optimizer_generated,
                "expectedImpact": _impacts(item.get("expected_impact")),
                "sourceModule": "optimizer",
                "origin": "live",
            }
        )

    return results


def build_objective(snapshot: Snapshot) -> dict[str, Any]:
    result = (snapshot.scenarios or {}).get("result", {}) or {}
    best = result.get("best_scenario") or {}

    scenario_id = str(best.get("scenario_id", "baseline"))
    mode, label = SCENARIO_TO_MODE.get(scenario_id, ("resilience", "Resilience"))

    description = best.get("description") or (
        "No scenario has been ranked yet."
    )
    ranking = best.get("ranking", {}) or {}
    score = ranking.get("score")
    if score is not None:
        description = (
            f"{description} Module 5 ranked this scenario first with a weighted "
            f"score of {score:.2f}/100."
        )

    constraints = list(best.get("assumptions") or [])
    applied = best.get("applied_recommendations") or []
    if applied:
        constraints.append(
            "Applies Module 4 setpoints from: "
            + ", ".join(title_case(str(name)) for name in applied)
        )

    return {
        "mode": mode,
        "label": label,
        "description": description,
        "constraints": constraints,
        "since": iso(result.get("generated_at")) or snapshot.finished_at or now_iso(),
    }
