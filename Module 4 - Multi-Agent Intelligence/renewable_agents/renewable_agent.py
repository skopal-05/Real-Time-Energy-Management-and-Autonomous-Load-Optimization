"""Plant-level renewable energy optimization agent."""

from __future__ import annotations

from typing import Any, Mapping

from contracts import AgentRecommendation, number, rounded


class RenewableAgent:
    """Coordinate solar, battery discharge, and grid supply for plant demand."""

    name = "renewable_agent"

    def optimize(self, state: Mapping[str, Any]) -> AgentRecommendation:
        demand = number(state, "plant_demand_kw", minimum=0)
        solar = number(state, "solar_available_kw", default=0, minimum=0)
        battery = number(state, "battery_discharge_available_kw", default=0, minimum=0)
        reserve = number(state, "battery_reserve_kw", default=0, minimum=0)
        dispatchable_battery = max(0.0, battery - reserve)

        solar_to_load = min(demand, solar)
        remaining = demand - solar_to_load
        battery_to_load = min(remaining, dispatchable_battery)
        grid_to_load = max(0.0, remaining - battery_to_load)
        solar_surplus = max(0.0, solar - solar_to_load)
        renewable_served = solar_to_load + battery_to_load
        penetration = renewable_served / demand * 100 if demand else 100.0

        return AgentRecommendation(
            agent=self.name,
            action="maximize_renewable_supply",
            priority="medium" if grid_to_load > 0 else "low",
            reason=(
                "Renewable sources are dispatched before grid import while preserving reserve."
            ),
            setpoints=rounded(
                {
                    "solar_to_load_kw": solar_to_load,
                    "battery_to_load_kw": battery_to_load,
                    "grid_to_load_kw": grid_to_load,
                    "solar_surplus_kw": solar_surplus,
                }
            ),
            expected_impact=rounded(
                {
                    "renewable_energy_served_kw": renewable_served,
                    "renewable_penetration_percent": penetration,
                    "avoided_grid_import_kw": renewable_served,
                }
            ),
            constraints=("battery reserve is preserved", "renewable-first dispatch"),
        )

    decide = optimize
