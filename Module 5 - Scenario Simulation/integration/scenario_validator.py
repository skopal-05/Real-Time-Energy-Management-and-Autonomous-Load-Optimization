"""Validation for Module 3, Module 4, and Module 5 JSON contracts."""

from __future__ import annotations

from math import isfinite
from typing import Any, Iterable, Mapping

from contracts import ScenarioResult


class IntegrationValidator:
    """Validate external inputs and completed scenario comparisons."""

    FORECAST_KEYS = {
        "future_state": (
            "compressor_power_kw",
            "hvac_power_kw",
            "inverter_power_kw",
            "fuel_flow_m3_hr",
        ),
        "energy_forecast": (
            "total_load_kw",
            "renewable_generation_kw",
            "boiler_fuel_flow_m3_hr",
        ),
    }

    REQUIRED_SCENARIOS = {
        "baseline",
        "agent_optimized",
        "renewable_first",
        "cost_saver",
        "resilience",
    }

    def validate_forecast(
        self,
        forecast: Mapping[str, Any],
    ) -> list[str]:
        """Validate the Module 3 forecast contract."""

        errors: list[str] = []

        if not isinstance(forecast, Mapping):
            return ["forecast must be an object"]

        for section, keys in self.FORECAST_KEYS.items():

            value = forecast.get(section)

            if not isinstance(value, Mapping):
                errors.append(
                    f"{section} must be an object"
                )
                continue

            for key in keys:

                if key not in value:
                    errors.append(
                        f"{section}.{key} is missing"
                    )
                    continue

                raw = value[key]

                if isinstance(raw, bool):
                    errors.append(
                        f"{section}.{key} must be numeric"
                    )
                    continue

                try:
                    numeric_value = float(raw)
                except (TypeError, ValueError):
                    errors.append(
                        f"{section}.{key} must be numeric"
                    )
                    continue

                if not isfinite(numeric_value):
                    errors.append(
                        f"{section}.{key} must be finite"
                    )
                elif numeric_value < 0:
                    errors.append(
                        f"{section}.{key} must be non-negative"
                    )

        return errors

    def validate_recommendations(
        self,
        recommendations: Iterable[Mapping[str, Any]],
    ) -> list[str]:
        """Validate Module 4 recommendation objects."""

        errors: list[str] = []

        items = list(recommendations)

        if not items:
            return [
                "recommendations must not be empty"
            ]

        for index, item in enumerate(items):

            if not isinstance(item, Mapping):
                errors.append(
                    f"recommendation {index} must be an object"
                )
                continue

            for key in (
                "agent",
                "action",
                "priority",
                "setpoints",
            ):
                if key not in item:
                    errors.append(
                        f"recommendation {index} "
                        f"missing {key}"
                    )

            agent = item.get("agent")

            if not isinstance(agent, str) or not agent.strip():
                errors.append(
                    f"recommendation {index} "
                    "agent must be a non-empty string"
                )

            action = item.get("action")

            if not isinstance(action, str) or not action.strip():
                errors.append(
                    f"recommendation {index} "
                    "action must be a non-empty string"
                )

            priority = item.get("priority")

            if priority not in {
                "low",
                "medium",
                "high",
                "critical",
            }:
                errors.append(
                    f"recommendation {index} "
                    f"has invalid priority: {priority}"
                )

            if not isinstance(
                item.get("setpoints"),
                Mapping,
            ):
                errors.append(
                    f"recommendation {index} "
                    "setpoints must be an object"
                )

        return errors

    def validate_results(
        self,
        results: Iterable[ScenarioResult],
    ) -> list[str]:
        """Validate completed scenario results."""

        items = list(results)

        errors: list[str] = []

        if len(items) < 2:
            errors.append(
                "at least two scenarios are required "
                "for comparison"
            )
            return errors

        ids = [
            item.scenario.scenario_id
            for item in items
        ]

        if len(ids) != len(set(ids)):
            errors.append(
                "scenario identifiers must be unique"
            )

        missing_scenarios = (
            self.REQUIRED_SCENARIOS
            - set(ids)
        )

        if missing_scenarios:
            errors.append(
                "missing required scenarios: "
                + ", ".join(
                    sorted(missing_scenarios)
                )
            )

        ranks = [
            item.rank
            for item in items
        ]

        if sorted(ranks) != list(
            range(1, len(items) + 1)
        ):
            errors.append(
                "scenario ranks must be consecutive "
                "starting at 1"
            )

        ranked_items = sorted(
            items,
            key=lambda item: item.rank,
        )

        if ranked_items[0].rank != 1:
            errors.append(
                "best scenario must have rank 1"
            )

        for item in items:

            scenario_id = (
                item.scenario.scenario_id
            )

            if not 0 <= item.score <= 100:
                errors.append(
                    f"{scenario_id} score must be "
                    "between 0 and 100"
                )

            if not isfinite(item.score):
                errors.append(
                    f"{scenario_id} score must be finite"
                )

            energy = item.energy
            cost = item.cost
            carbon = item.carbon

            required_energy = (
                "useful_electrical_load_kwh",
                "grid_import_kwh",
                "grid_export_kwh",
                "battery_charge_kwh",
                "battery_discharge_kwh",
                "boiler_fuel_m3",
            )

            required_cost = (
                "net_operating_cost_inr",
                "cost_saving_inr",
            )

            required_carbon = (
                "total_emissions_kg_co2e",
                "emissions_avoided_kg_co2e",
            )

            for key in required_energy:
                if key not in energy:
                    errors.append(
                        f"{scenario_id} missing "
                        f"energy.{key}"
                    )
                elif (
                    isinstance(energy[key], bool)
                    or not isinstance(
                        energy[key],
                        (int, float),
                    )
                    or not isfinite(
                        float(energy[key])
                    )
                ):
                    errors.append(
                        f"{scenario_id} energy.{key} "
                        "must be finite numeric"
                    )

            for key in required_cost:
                if key not in cost:
                    errors.append(
                        f"{scenario_id} missing "
                        f"cost.{key}"
                    )

            for key in required_carbon:
                if key not in carbon:
                    errors.append(
                        f"{scenario_id} missing "
                        f"carbon.{key}"
                    )

            if energy.get(
                "grid_import_kwh",
                0,
            ) < 0:
                errors.append(
                    f"{scenario_id} has negative "
                    "grid import"
                )

            if energy.get(
                "grid_export_kwh",
                0,
            ) < 0:
                errors.append(
                    f"{scenario_id} has negative "
                    "grid export"
                )

            if (
                energy.get(
                    "battery_charge_kwh",
                    0,
                ) > 0
                and energy.get(
                    "battery_discharge_kwh",
                    0,
                ) > 0
            ):
                errors.append(
                    f"{scenario_id} battery cannot "
                    "charge and discharge simultaneously"
                )

        return errors

    @staticmethod
    def require_valid(
        errors: list[str],
        label: str,
    ) -> None:
        """Raise an exception when validation fails."""

        if errors:
            raise ValueError(
                f"invalid {label}: "
                + "; ".join(errors)
            )