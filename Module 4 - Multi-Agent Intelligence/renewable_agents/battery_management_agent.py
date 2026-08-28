"""Battery dispatch strategy agent."""

from __future__ import annotations

from typing import Any, Mapping

from contracts import AgentRecommendation, number, rounded


class BatteryManagementAgent:
    """Select charge, discharge, or standby while protecting state of charge."""

    name = "battery_management_agent"

    def __init__(
        self,
        *,
        minimum_soc_percent: float = 20,
        maximum_soc_percent: float = 90,
        peak_tariff_threshold: float = 8,
    ) -> None:
        if not 0 <= minimum_soc_percent < maximum_soc_percent <= 100:
            raise ValueError("SOC limits must satisfy 0 <= minimum < maximum <= 100")
        self.minimum_soc_percent = float(minimum_soc_percent)
        self.maximum_soc_percent = float(maximum_soc_percent)
        self.peak_tariff_threshold = float(peak_tariff_threshold)

    def manage(self, state: Mapping[str, Any]) -> AgentRecommendation:
        soc = number(state, "state_of_charge_percent", minimum=0, maximum=100)
        capacity = number(state, "capacity_kwh", minimum=0)
        surplus = number(state, "renewable_surplus_kw", default=0, minimum=0)
        deficit = number(state, "site_deficit_kw", default=0, minimum=0)
        tariff = number(state, "tariff_inr_kwh", default=0, minimum=0)
        max_charge = number(state, "maximum_charge_kw", default=capacity, minimum=0)
        max_discharge = number(state, "maximum_discharge_kw", default=capacity, minimum=0)
        interval = number(state, "interval_hours", default=1, minimum=0.001)

        charge_headroom_kwh = max(
            0.0, capacity * (self.maximum_soc_percent - soc) / 100
        )
        discharge_available_kwh = max(
            0.0, capacity * (soc - self.minimum_soc_percent) / 100
        )

        charge = min(surplus, max_charge, charge_headroom_kwh / interval)
        discharge = 0.0
        action = "standby"
        reason = "No economic or renewable dispatch condition is active."
        priority = "low"

        if charge > 0.01:
            action = "charge_from_renewable"
            reason = "Renewable surplus is available and the battery has SOC headroom."
            priority = "medium"
        elif deficit > 0 and tariff >= self.peak_tariff_threshold:
            discharge = min(
                deficit, max_discharge, discharge_available_kwh / interval
            )
            if discharge > 0.01:
                action = "discharge_to_load"
                reason = "Peak-price demand can be served without violating reserve SOC."
                priority = "high"
            elif soc <= self.minimum_soc_percent:
                action = "protect_reserve"
                reason = "Battery reserve SOC prevents discharge."
                priority = "high"

        projected_energy_delta = (charge - discharge) * interval
        projected_soc = soc + (
            projected_energy_delta / capacity * 100 if capacity else 0
        )
        projected_soc = min(self.maximum_soc_percent, max(self.minimum_soc_percent, projected_soc))

        return AgentRecommendation(
            agent=self.name,
            action=action,
            priority=priority,
            reason=reason,
            setpoints=rounded(
                {
                    "battery_charge_kw": charge,
                    "battery_discharge_kw": discharge,
                    "battery_power_kw": discharge - charge,
                    "projected_soc_percent": projected_soc,
                }
            ),
            expected_impact=rounded(
                {
                    "grid_import_reduction_kw": discharge,
                    "renewable_absorption_kw": charge,
                }
            ),
            constraints=(
                f"minimum_soc_percent={self.minimum_soc_percent}",
                f"maximum_soc_percent={self.maximum_soc_percent}",
                "battery power and interval energy limits",
            ),
        )

    decide = manage
