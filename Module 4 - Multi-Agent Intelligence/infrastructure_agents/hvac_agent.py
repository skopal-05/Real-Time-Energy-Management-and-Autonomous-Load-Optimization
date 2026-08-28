"""HVAC energy management agent for Module 4."""

from __future__ import annotations

from typing import Any, Mapping

from contracts import AgentRecommendation, number, rounded


class HVACAgent:
    """Recommend HVAC operating actions based on forecast demand and limits."""

    name = "hvac_agent"

    def __init__(
        self,
        *,
        high_power_threshold_kw: float = 80.0,
        maximum_reduction_fraction: float = 0.15,
    ) -> None:
        if high_power_threshold_kw < 0:
            raise ValueError("high_power_threshold_kw must be non-negative")

        if not 0 <= maximum_reduction_fraction <= 1:
            raise ValueError(
                "maximum_reduction_fraction must be between 0 and 1"
            )

        self.high_power_threshold_kw = float(high_power_threshold_kw)
        self.maximum_reduction_fraction = float(maximum_reduction_fraction)

    def optimize(self, state: Mapping[str, Any]) -> AgentRecommendation:
        """Recommend an HVAC power target while respecting comfort constraints."""

        forecast_power = number(
            state,
            "hvac_power_kw",
            minimum=0,
        )

        temperature = number(
            state,
            "temperature_c",
            default=24.0,
        )

        target_temperature = number(
            state,
            "target_temperature_c",
            default=24.0,
        )

        minimum_temperature = number(
            state,
            "minimum_temperature_c",
            default=20.0,
        )

        maximum_temperature = number(
            state,
            "maximum_temperature_c",
            default=28.0,
        )

        maximum_power = number(
            state,
            "maximum_hvac_power_kw",
            default=forecast_power,
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

        # Keep the requested comfort target within the allowed temperature range.
        safe_target_temperature = min(
            maximum_temperature,
            max(minimum_temperature, target_temperature),
        )

        reduction = 0.0
        action = "maintain_hvac"
        priority = "low"
        reason = "Forecast HVAC demand is within the configured operating range."

        # If HVAC demand is high and the current temperature is reasonably
        # close to the desired target, a controlled reduction is possible.
        temperature_deviation = abs(
            temperature - safe_target_temperature
        )

        if (
            forecast_power > self.high_power_threshold_kw
            and temperature_deviation <= 2.0
        ):
            reduction = min(
                forecast_power * reduction_fraction,
                forecast_power,
            )

            action = "optimize_hvac_load"
            priority = (
                "high"
                if forecast_power >= self.high_power_threshold_kw * 1.25
                else "medium"
            )
            reason = (
                "HVAC forecast demand is high and controlled load reduction "
                "is possible without exceeding the configured comfort range."
            )

        target_power = max(
            0.0,
            min(maximum_power, forecast_power - reduction),
        )

        return AgentRecommendation(
            agent=self.name,
            action=action,
            priority=priority,
            reason=reason,
            setpoints=rounded(
                {
                    "hvac_power_target_kw": target_power,
                    "hvac_load_reduction_kw": reduction,
                    "target_temperature_c": safe_target_temperature,
                }
            ),
            expected_impact=rounded(
                {
                    "forecast_hvac_power_kw": forecast_power,
                    "optimized_hvac_power_kw": target_power,
                    "estimated_power_saving_kw": reduction,
                }
            ),
            constraints=(
                f"maximum_reduction_fraction={self.maximum_reduction_fraction}",
                f"temperature_range={minimum_temperature}..{maximum_temperature}",
                "HVAC power cannot exceed maximum_hvac_power_kw",
            ),
        )

    decide = optimize