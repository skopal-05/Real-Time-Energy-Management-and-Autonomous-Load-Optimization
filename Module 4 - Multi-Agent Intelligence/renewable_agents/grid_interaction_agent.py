"""Electrical grid import/export management agent."""

from __future__ import annotations

from typing import Any, Mapping

from contracts import AgentRecommendation, number, rounded


class GridInteractionAgent:
    """Manage grid exchange after local generation and storage dispatch."""

    name = "grid_interaction_agent"

    def __init__(self, *, high_tariff_threshold: float = 8.0) -> None:
        if high_tariff_threshold < 0:
            raise ValueError("high_tariff_threshold must be non-negative")
        self.high_tariff_threshold = float(high_tariff_threshold)

    def interact(self, state: Mapping[str, Any]) -> AgentRecommendation:
        net_demand = number(state, "net_demand_kw")
        import_limit = number(state, "grid_import_limit_kw", default=0, minimum=0)
        export_limit = number(state, "grid_export_limit_kw", default=0, minimum=0)
        tariff = number(state, "tariff_inr_kwh", default=0, minimum=0)
        export_price = number(state, "export_price_inr_kwh", default=0, minimum=0)

        grid_import = min(max(0.0, net_demand), import_limit)
        unmet = max(0.0, net_demand - grid_import)
        available_export = max(0.0, -net_demand)
        grid_export = min(available_export, export_limit)
        curtailed_export = max(0.0, available_export - grid_export)

        if unmet > 0.01:
            action = "limit_import_and_shed_load"
            priority = "critical"
            reason = "Net demand exceeds the grid import limit."
        elif grid_export > 0.01:
            action = "export_surplus"
            priority = "low"
            reason = "Local supply exceeds demand and export capacity is available."
        elif grid_import > 0.01:
            action = "import_power"
            priority = "high" if tariff >= self.high_tariff_threshold else "medium"
            reason = "Local resources do not fully cover net demand."
        else:
            action = "islanded_balance"
            priority = "low"
            reason = "Local supply and demand are balanced."

        return AgentRecommendation(
            agent=self.name,
            action=action,
            priority=priority,
            reason=reason,
            setpoints=rounded(
                {
                    "grid_import_kw": grid_import,
                    "grid_export_kw": grid_export,
                    "unserved_load_kw": unmet,
                    "curtailed_export_kw": curtailed_export,
                }
            ),
            expected_impact=rounded(
                {
                    "import_cost_inr_per_hour": grid_import * tariff,
                    "export_revenue_inr_per_hour": grid_export * export_price,
                    "net_grid_cost_inr_per_hour": (
                        grid_import * tariff - grid_export * export_price
                    ),
                }
            ),
            constraints=("grid import limit", "grid export limit"),
        )

    decide = interact
