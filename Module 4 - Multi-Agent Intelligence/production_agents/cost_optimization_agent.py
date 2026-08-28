"""Production cost optimization agent."""

from __future__ import annotations

from typing import Any, Mapping

from contracts import AgentRecommendation, clamp, number, rounded


class CostOptimizationAgent:
    """Recommend load shifting when grid energy is expensive."""

    name = "cost_optimization_agent"

    def __init__(
        self,
        *,
        peak_tariff_threshold: float = 8.0,
        maximum_shift_fraction: float = 0.20,
    ) -> None:
        if peak_tariff_threshold < 0:
            raise ValueError("peak_tariff_threshold must be non-negative")
        if not 0 <= maximum_shift_fraction <= 1:
            raise ValueError("maximum_shift_fraction must be between 0 and 1")
        self.peak_tariff_threshold = float(peak_tariff_threshold)
        self.maximum_shift_fraction = float(maximum_shift_fraction)

    def optimize(self, state: Mapping[str, Any]) -> AgentRecommendation:
        """Compare present and off-peak costs and recommend a safe load target."""

        load = number(state, "production_load_kw", minimum=0)
        renewable = number(state, "renewable_generation_kw", default=0, minimum=0)
        tariff = number(state, "tariff_inr_kwh", minimum=0)
        off_peak = number(
            state,
            "off_peak_tariff_inr_kwh",
            default=tariff,
            minimum=0,
        )
        flexible_fraction = number(
            state,
            "flexible_load_fraction",
            default=self.maximum_shift_fraction,
            minimum=0,
            maximum=1,
        )
        flexible_fraction = min(flexible_fraction, self.maximum_shift_fraction)

        grid_served_load = max(0.0, load - renewable)
        shift = 0.0
        if tariff > self.peak_tariff_threshold and tariff > off_peak:
            shift = min(load * flexible_fraction, grid_served_load)

        target = load - shift
        savings = shift * max(0.0, tariff - off_peak)
        baseline_cost = grid_served_load * tariff
        optimized_cost = max(0.0, target - renewable) * tariff + shift * off_peak

        if shift > 0:
            action = "shift_flexible_load"
            priority = "high" if tariff >= self.peak_tariff_threshold * 1.25 else "medium"
            reason = "Current grid tariff exceeds the configured peak threshold."
        else:
            action = "maintain_schedule"
            priority = "low"
            reason = "Load shifting would not reduce the forecast energy cost."

        return AgentRecommendation(
            agent=self.name,
            action=action,
            priority=priority,
            reason=reason,
            setpoints=rounded(
                {
                    "production_load_target_kw": target,
                    "load_to_shift_kw": shift,
                }
            ),
            expected_impact=rounded(
                {
                    "baseline_cost_inr": baseline_cost,
                    "optimized_cost_inr": optimized_cost,
                    "estimated_savings_inr": clamp(savings, 0.0, baseline_cost),
                }
            ),
            constraints=(
                f"maximum_shift_fraction={self.maximum_shift_fraction}",
                "renewable generation is consumed before grid energy",
            ),
        )

    decide = optimize
