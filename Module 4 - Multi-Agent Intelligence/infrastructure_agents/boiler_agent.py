"""Boiler energy and fuel optimization agent for Module 4."""

from __future__ import annotations

from typing import Any, Mapping

from contracts import AgentRecommendation, number, rounded


class BoilerAgent:
    """Recommend boiler operating actions based on forecast fuel demand."""

    name = "boiler_agent"

    def __init__(
        self,
        *,
        high_fuel_threshold_m3_hr: float = 50.0,
        maximum_reduction_fraction: float = 0.15,
        minimum_efficiency_percent: float = 70.0,
    ) -> None:
        if high_fuel_threshold_m3_hr < 0:
            raise ValueError(
                "high_fuel_threshold_m3_hr must be non-negative"
            )

        if not 0 <= maximum_reduction_fraction <= 1:
            raise ValueError(
                "maximum_reduction_fraction must be between 0 and 1"
            )

        if not 0 <= minimum_efficiency_percent <= 100:
            raise ValueError(
                "minimum_efficiency_percent must be between 0 and 100"
            )

        self.high_fuel_threshold_m3_hr = float(high_fuel_threshold_m3_hr)
        self.maximum_reduction_fraction = float(maximum_reduction_fraction)
        self.minimum_efficiency_percent = float(minimum_efficiency_percent)

    def optimize(self, state: Mapping[str, Any]) -> AgentRecommendation:
        """Optimize boiler fuel consumption while protecting efficiency."""

        forecast_fuel = number(
            state,
            "fuel_flow_m3_hr",
            minimum=0,
        )

        efficiency = number(
            state,
            "efficiency_percent",
            default=100.0,
            minimum=0,
            maximum=100,
        )

        required_efficiency = number(
            state,
            "required_efficiency_percent",
            default=self.minimum_efficiency_percent,
            minimum=0,
            maximum=100,
        )

        maximum_fuel = number(
            state,
            "maximum_fuel_flow_m3_hr",
            default=forecast_fuel,
            minimum=0,
        )

        reduction_fraction = number(
            state,
            "maximum_reduction_fraction",
            default=self.maximum_reduction_fraction,
            minimum=0,
            maximum=1,
        )

        reduction_fraction = min(
            reduction_fraction,
            self.maximum_reduction_fraction,
        )

        reduction = 0.0
        action = "maintain_boiler"
        priority = "low"
        reason = (
            "Forecast boiler fuel demand is within the configured "
            "operating range."
        )

        # If efficiency is below the required level, avoid reducing
        # fuel because further reduction may affect boiler performance.
        if efficiency < required_efficiency:
            action = "protect_boiler_efficiency"
            priority = "high"
            reason = (
                "Boiler efficiency is below the required operating level; "
                "fuel reduction is not recommended."
            )

        elif forecast_fuel > self.high_fuel_threshold_m3_hr:
            reduction = min(
                forecast_fuel * reduction_fraction,
                forecast_fuel,
            )

            action = "optimize_boiler_fuel"
            priority = (
                "high"
                if forecast_fuel >= self.high_fuel_threshold_m3_hr * 1.25
                else "medium"
            )
            reason = (
                "Forecast boiler fuel demand is high and controlled "
                "fuel reduction is possible while maintaining efficiency."
            )

        target_fuel = max(
            0.0,
            min(maximum_fuel, forecast_fuel - reduction),
        )

        return AgentRecommendation(
            agent=self.name,
            action=action,
            priority=priority,
            reason=reason,
            setpoints=rounded(
                {
                    "boiler_fuel_target_m3_hr": target_fuel,
                    "boiler_fuel_reduction_m3_hr": reduction,
                    "required_efficiency_percent": required_efficiency,
                }
            ),
            expected_impact=rounded(
                {
                    "forecast_fuel_flow_m3_hr": forecast_fuel,
                    "optimized_fuel_flow_m3_hr": target_fuel,
                    "estimated_fuel_saving_m3_hr": reduction,
                }
            ),
            constraints=(
                f"minimum_efficiency_percent={self.minimum_efficiency_percent}",
                f"maximum_reduction_fraction={self.maximum_reduction_fraction}",
                "fuel flow cannot exceed maximum_fuel_flow_m3_hr",
            ),
        )

    decide = optimize