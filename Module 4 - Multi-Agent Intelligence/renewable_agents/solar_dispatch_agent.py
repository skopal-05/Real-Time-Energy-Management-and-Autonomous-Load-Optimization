"""Solar generation dispatch agent."""

from __future__ import annotations

from typing import Any, Mapping

from contracts import AgentRecommendation, number, rounded


class SolarDispatchAgent:
    """Dispatch solar to load, battery, export, then curtailment."""

    name = "solar_dispatch_agent"

    def dispatch(self, state: Mapping[str, Any]) -> AgentRecommendation:
        generation = number(state, "solar_generation_kw", minimum=0)
        demand = number(state, "site_demand_kw", minimum=0)
        battery_headroom = number(state, "battery_charge_headroom_kw", default=0, minimum=0)
        charge_limit = number(
            state,
            "battery_charge_limit_kw",
            default=battery_headroom,
            minimum=0,
        )
        export_limit = number(state, "grid_export_limit_kw", default=0, minimum=0)

        to_load = min(generation, demand)
        surplus = generation - to_load
        to_battery = min(surplus, battery_headroom, charge_limit)
        surplus -= to_battery
        to_grid = min(surplus, export_limit)
        curtailed = max(0.0, surplus - to_grid)

        return AgentRecommendation(
            agent=self.name,
            action="dispatch_solar" if curtailed <= 0.01 else "dispatch_and_curtail",
            priority="medium" if curtailed > 0.01 else "low",
            reason=(
                "Solar is allocated to local demand, storage, and export in that order."
            ),
            setpoints=rounded(
                {
                    "solar_to_load_kw": to_load,
                    "solar_to_battery_kw": to_battery,
                    "solar_to_grid_kw": to_grid,
                    "solar_curtailed_kw": curtailed,
                }
            ),
            expected_impact=rounded(
                {
                    "solar_utilized_kw": generation - curtailed,
                    "self_consumption_percent": (
                        (to_load + to_battery) / generation * 100 if generation else 100
                    ),
                }
            ),
            constraints=(
                "battery charge headroom and charge-power limit",
                "grid export limit",
            ),
        )

    decide = dispatch
