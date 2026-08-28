"""Validation utilities for the Module 3 to Module 4 integration."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from contracts import AgentRecommendation


class AgentValidator:
    """Validate forecasts, registered agents, and agent recommendations."""

    name = "agent_validator"

    REQUIRED_FORECAST_SECTIONS = (
        "future_state",
        "energy_forecast",
    )

    REQUIRED_FUTURE_STATE_FIELDS = (
        "units_per_hour",
        "fuel_flow_m3_hr",
        "compressor_power_kw",
        "hvac_power_kw",
        "battery_power_kw",
        "grid_import_kw",
        "inverter_power_kw",
    )

    REQUIRED_ENERGY_FIELDS = (
        "total_load_kw",
        "renewable_generation_kw",
        "grid_import_kw",
        "boiler_fuel_flow_m3_hr",
    )

    EXPECTED_AGENTS = (
        "cost_optimization_agent",
        "load_balancing_agent",
        "production_scheduler",
        "energy_allocator",
        "renewable_agent",
        "solar_dispatch_agent",
        "battery_management_agent",
        "grid_interaction_agent",
        "hvac_agent",
        "compressor_agent",
        "boiler_agent",
        "equipment_health_agent",
    )

    VALID_PRIORITIES = {
        "low",
        "medium",
        "high",
        "critical",
    }

    def validate_forecast(
        self,
        forecast: Mapping[str, Any],
    ) -> list[str]:
        """Validate the structure of Module 3 forecast output."""

        errors: list[str] = []

        if not isinstance(forecast, Mapping):
            return ["forecast must be a mapping/object"]

        for section in self.REQUIRED_FORECAST_SECTIONS:
            if section not in forecast:
                errors.append(
                    f"missing forecast section: {section}"
                )

        future_state = forecast.get("future_state")

        if isinstance(future_state, Mapping):
            for field in self.REQUIRED_FUTURE_STATE_FIELDS:
                if field not in future_state:
                    errors.append(
                        f"missing future_state field: {field}"
                    )
                else:
                    self._validate_numeric_field(
                        future_state,
                        field,
                        errors,
                        section="future_state",
                    )
        else:
            errors.append(
                "future_state must be an object"
            )

        energy_forecast = forecast.get("energy_forecast")

        if isinstance(energy_forecast, Mapping):
            for field in self.REQUIRED_ENERGY_FIELDS:
                if field not in energy_forecast:
                    errors.append(
                        f"missing energy_forecast field: {field}"
                    )
                else:
                    self._validate_numeric_field(
                        energy_forecast,
                        field,
                        errors,
                        section="energy_forecast",
                    )
        else:
            errors.append(
                "energy_forecast must be an object"
            )

        return errors

    def validate_agents(
        self,
        registered_agents: Iterable[str],
    ) -> list[str]:
        """Validate that all expected Module 4 agents are registered."""

        errors: list[str] = []

        registered = list(registered_agents)

        missing = [
            agent
            for agent in self.EXPECTED_AGENTS
            if agent not in registered
        ]

        unexpected = [
            agent
            for agent in registered
            if agent not in self.EXPECTED_AGENTS
        ]

        if missing:
            errors.append(
                f"missing agents: {missing}"
            )

        if unexpected:
            errors.append(
                f"unexpected agents: {unexpected}"
            )

        if len(registered) != len(set(registered)):
            errors.append(
                "duplicate agent names detected"
            )

        return errors

    def validate_recommendations(
        self,
        recommendations: Iterable[AgentRecommendation],
    ) -> list[str]:
        """Validate generated agent recommendations."""

        errors: list[str] = []

        items = list(recommendations)

        if not items:
            errors.append(
                "no recommendations were generated"
            )
            return errors

        for index, recommendation in enumerate(items):

            if not isinstance(
                recommendation,
                AgentRecommendation,
            ):
                errors.append(
                    f"recommendation {index} is not "
                    "an AgentRecommendation"
                )
                continue

            if not recommendation.agent.strip():
                errors.append(
                    f"recommendation {index} has empty agent name"
                )

            if not recommendation.action.strip():
                errors.append(
                    f"recommendation {index} has empty action"
                )

            if recommendation.priority not in self.VALID_PRIORITIES:
                errors.append(
                    f"recommendation {index} has invalid "
                    f"priority: {recommendation.priority}"
                )

            if not recommendation.reason.strip():
                errors.append(
                    f"recommendation {index} has empty reason"
                )

        return errors

    def validate_complete_pipeline(
        self,
        forecast: Mapping[str, Any],
        registered_agents: Iterable[str],
        recommendations: Iterable[AgentRecommendation],
    ) -> dict[str, Any]:
        """Run all validation checks and return a validation report."""

        forecast_errors = self.validate_forecast(
            forecast
        )

        agent_errors = self.validate_agents(
            registered_agents
        )

        recommendation_items = list(
            recommendations
        )

        recommendation_errors = self.validate_recommendations(
            recommendation_items
        )

        errors = (
            forecast_errors
            + agent_errors
            + recommendation_errors
        )

        return {
            "valid": len(errors) == 0,
            "forecast_valid": len(forecast_errors) == 0,
            "agents_valid": len(agent_errors) == 0,
            "recommendations_valid": (
                len(recommendation_errors) == 0
            ),
            "forecast_errors": forecast_errors,
            "agent_errors": agent_errors,
            "recommendation_errors": recommendation_errors,
            "registered_agent_count": len(
                list(registered_agents)
            ),
            "recommendation_count": len(
                recommendation_items
            ),
        }

    @staticmethod
    def _validate_numeric_field(
        data: Mapping[str, Any],
        field: str,
        errors: list[str],
        *,
        section: str,
    ) -> None:
        """Validate that a forecast field contains a numeric value."""

        value = data[field]

        if isinstance(value, bool):
            errors.append(
                f"{section}.{field} must be numeric"
            )
            return

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            errors.append(
                f"{section}.{field} must be numeric"
            )
            return

        if numeric_value != numeric_value:
            errors.append(
                f"{section}.{field} must not be NaN"
            )

        if numeric_value == float("inf") or numeric_value == float("-inf"):
            errors.append(
                f"{section}.{field} must be finite"
            )