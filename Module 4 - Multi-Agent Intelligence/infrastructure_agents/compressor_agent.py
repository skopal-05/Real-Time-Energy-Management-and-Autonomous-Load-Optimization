"""Compressor energy optimization agent for Module 4."""

from __future__ import annotations

from typing import Any, Mapping

from contracts import AgentRecommendation, number, rounded


class CompressorAgent:
    """Recommend compressor operating actions based on forecast power demand."""

    name = "compressor_agent"

    def __init__(
        self,
        *,
        high_power_threshold_kw: float = 60.0,
        maximum_reduction_fraction: float = 0.15,
        minimum_pressure_bar: float = 5.0,
    ) -> None:
        if high_power_threshold_kw < 0:
            raise ValueError(
                "high_power_threshold_kw must be non-negative"
            )

        if not 0 <= maximum_reduction_fraction <= 1:
            raise ValueError(
                "maximum_reduction_fraction must be between 0 and 1"
            )

        if minimum_pressure_bar < 0:
            raise ValueError(
                "minimum_pressure_bar must be non-negative"
            )

        self.high_power_threshold_kw = float(high_power_threshold_kw)
        self.maximum_reduction_fraction = float(maximum_reduction_fraction)
        self.minimum_pressure_bar = float(minimum_pressure_bar)

    def optimize(self, state: Mapping[str, Any]) -> AgentRecommendation:
        """Optimize compressor power while protecting minimum pressure."""

        forecast_power = number(
            state,
            "compressor_power_kw",
            minimum=0,
        )

        pressure = number(
            state,
            "pressure_bar",
            default=self.minimum_pressure_bar,
            minimum=0,
        )

        target_pressure = number(
            state,
            "target_pressure_bar",
            default=self.minimum_pressure_bar,
            minimum=0,
        )

        maximum_power = number(
            state,
            "maximum_compressor_power_kw",
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

        reduction = 0.0
        action = "maintain_compressor"
        priority = "low"
        reason = (
            "Forecast compressor demand is within the configured "
            "operating range."
        )

        # Do not reduce compressor load when pressure is already below
        # the required minimum.
        pressure_safe = pressure >= self.minimum_pressure_bar

        # Controlled reduction is possible only when sufficient pressure
        # is available and compressor demand is high.
        if (
            forecast_power > self.high_power_threshold_kw
            and pressure_safe
            and pressure >= target_pressure
        ):
            reduction = min(
                forecast_power * reduction_fraction,
                forecast_power,
            )

            action = "optimize_compressor_load"
            priority = (
                "high"
                if forecast_power >= self.high_power_threshold_kw * 1.25
                else "medium"
            )
            reason = (
                "Compressor forecast demand is high and power reduction "
                "is possible while maintaining the required pressure."
            )

        elif pressure < self.minimum_pressure_bar:
            action = "protect_compressor_pressure"
            priority = "critical"
            reason = (
                "Compressor pressure is below the configured minimum; "
                "load reduction is not recommended."
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
                    "compressor_power_target_kw": target_power,
                    "compressor_load_reduction_kw": reduction,
                    "target_pressure_bar": target_pressure,
                }
            ),
            expected_impact=rounded(
                {
                    "forecast_compressor_power_kw": forecast_power,
                    "optimized_compressor_power_kw": target_power,
                    "estimated_power_saving_kw": reduction,
                }
            ),
            constraints=(
                f"minimum_pressure_bar={self.minimum_pressure_bar}",
                f"maximum_reduction_fraction={self.maximum_reduction_fraction}",
                "compressor power cannot exceed maximum_compressor_power_kw",
            ),
        )

    decide = optimize