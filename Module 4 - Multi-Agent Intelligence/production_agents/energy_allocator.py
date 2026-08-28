"""Energy allocation engine for production demand."""

from __future__ import annotations

from typing import Any, Mapping

from contracts import AgentRecommendation, number, rounded


class EnergyAllocator:
    """Allocate renewable, battery, and grid supply in economic order."""

    name = "energy_allocator"

    def allocate(self, state: Mapping[str, Any]) -> AgentRecommendation:
        demand = number(state, "production_demand_kw", minimum=0)
        renewable = number(state, "renewable_available_kw", default=0, minimum=0)
        battery = number(state, "battery_discharge_available_kw", default=0, minimum=0)
        grid_limit = number(state, "grid_import_limit_kw", default=demand, minimum=0)
        battery_cost = number(state, "battery_cost_inr_kwh", default=0, minimum=0)
        grid_cost = number(state, "grid_tariff_inr_kwh", default=0, minimum=0)

        renewable_used = min(demand, renewable)
        remaining = demand - renewable_used

        battery_first = battery_cost <= grid_cost
        battery_used = min(remaining, battery) if battery_first else 0.0
        remaining -= battery_used
        grid_used = min(remaining, grid_limit)
        remaining -= grid_used

        if not battery_first and remaining > 0:
            extra_battery = min(remaining, battery)
            battery_used += extra_battery
            remaining -= extra_battery

        unmet = max(0.0, remaining)
        cost = battery_used * battery_cost + grid_used * grid_cost
        renewable_surplus = max(0.0, renewable - renewable_used)

        return AgentRecommendation(
            agent=self.name,
            action="allocate_energy" if unmet <= 0.01 else "allocate_with_shortfall",
            priority="critical" if unmet > 0.01 else "low",
            reason=(
                "Supply limits cannot fully serve production demand."
                if unmet > 0.01
                else "Production demand is covered using the least-cost available sources."
            ),
            setpoints=rounded(
                {
                    "renewable_to_production_kw": renewable_used,
                    "battery_to_production_kw": battery_used,
                    "grid_to_production_kw": grid_used,
                    "renewable_surplus_kw": renewable_surplus,
                    "unserved_production_kw": unmet,
                }
            ),
            expected_impact=rounded(
                {
                    "served_production_kw": demand - unmet,
                    "renewable_share_percent": (
                        renewable_used / demand * 100 if demand else 0
                    ),
                    "estimated_cost_inr_per_hour": cost,
                }
            ),
            constraints=(
                "renewable energy has first dispatch priority",
                "battery and grid power limits",
                "battery is dispatched economically unless needed to avoid a shortfall",
            ),
        )

    decide = allocate
