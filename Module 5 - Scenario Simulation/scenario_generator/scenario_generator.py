"""Generate future operating scenarios from Modules 3 and 4."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from contracts import Scenario, finite_number
from scenario_generator.scenario_templates import SCENARIO_TEMPLATES
from scenario_generator.scenario_validator import ScenarioValidator


class ScenarioGenerator:
    """Turn Module 3 forecasts and Module 4 recommendations into scenarios."""

    def __init__(self, validator: ScenarioValidator | None = None) -> None:
        self.validator = validator or ScenarioValidator()

    @staticmethod
    def _index_recommendations(
        recommendations: Iterable[Mapping[str, Any]],
    ) -> dict[str, Mapping[str, Any]]:
        """Index recommendations by agent name."""

        return {
            str(item.get("agent", "")): item
            for item in recommendations
            if isinstance(item, Mapping) and item.get("agent")
        }

    @staticmethod
    def _setpoint(
        index: Mapping[str, Mapping[str, Any]],
        agent: str,
        key: str,
        default: float,
    ) -> float:
        """Read a numeric agent setpoint with a safe fallback."""

        item = index.get(agent, {})
        setpoints = item.get("setpoints", {})

        if not isinstance(setpoints, Mapping):
            return default

        raw = setpoints.get(key, default)

        try:
            value = float(raw)
        except (TypeError, ValueError):
            return default

        return max(0.0, value)

    def generate(
        self,
        forecast: Mapping[str, Any],
        recommendations: Iterable[Mapping[str, Any]],
        *,
        horizon_hours: float = 1.0,
    ) -> list[Scenario]:
        """
        Generate deterministic what-if scenarios.

        Module 3 provides:
        - production output in units/hour
        - compressor electrical power in kW
        - HVAC electrical power in kW
        - solar generation in kW
        - boiler fuel flow in m3/hour

        Production output is intentionally NOT treated as electrical
        load because Module 3 does not currently provide a production
        power forecast.
        """

        if horizon_hours <= 0:
            raise ValueError("horizon_hours must be greater than zero")

        future = forecast.get("future_state", {})
        energy = forecast.get("energy_forecast", {})

        if not isinstance(future, Mapping):
            raise ValueError(
                "forecast.future_state must be an object"
            )

        if not isinstance(energy, Mapping):
            raise ValueError(
                "forecast.energy_forecast must be an object"
            )

        # -------------------------------------------------------------
        # Module 3 forecast values
        # -------------------------------------------------------------

        production_units = finite_number(
            future,
            "units_per_hour",
            default=0,
            minimum=0,
        )

        compressor = finite_number(
            future,
            "compressor_power_kw",
            default=0,
            minimum=0,
        )

        hvac = finite_number(
            future,
            "hvac_power_kw",
            default=0,
            minimum=0,
        )

        # Use the solar/inverter forecast directly.
        # Battery power is simulated separately and therefore must not
        # be counted as renewable generation.
        renewable = finite_number(
            future,
            "inverter_power_kw",
            default=0,
            minimum=0,
        )

        boiler = finite_number(
            future,
            "fuel_flow_m3_hr",
            default=0,
            minimum=0,
        )

        recommendation_index = self._index_recommendations(
            recommendations
        )

        # -------------------------------------------------------------
        # Module 4 recommended setpoints
        # -------------------------------------------------------------

        optimized_compressor = self._setpoint(
            recommendation_index,
            "compressor_agent",
            "compressor_power_target_kw",
            compressor,
        )

        optimized_hvac = self._setpoint(
            recommendation_index,
            "hvac_agent",
            "hvac_power_target_kw",
            hvac,
        )

        optimized_boiler = self._setpoint(
            recommendation_index,
            "boiler_agent",
            "boiler_fuel_target_m3_hr",
            boiler,
        )

        recommended_charge = self._setpoint(
            recommendation_index,
            "battery_management_agent",
            "battery_charge_kw",
            0,
        )

        recommended_discharge = self._setpoint(
            recommendation_index,
            "battery_management_agent",
            "battery_discharge_kw",
            0,
        )

        # -------------------------------------------------------------
        # Scenario generation
        # -------------------------------------------------------------

        scenarios: list[Scenario] = []

        for template in SCENARIO_TEMPLATES:

            use_targets = bool(
                template["apply_agent_targets"]
            )

            # There is currently no production electrical-power
            # forecast in Module 3. Therefore production_load_kw stays
            # zero instead of incorrectly reusing total_load_kw.
            production_load_kw = 0.0

            scenario_compressor = (
                optimized_compressor
                if use_targets
                else compressor
            )

            scenario_hvac = (
                optimized_hvac
                if use_targets
                else hvac
            )

            # Apply the scenario load factor only to the explicitly
            # forecasted electrical loads. This creates a controlled
            # what-if variation without inventing a production-energy
            # conversion factor.
            load_factor = float(
                template["load_factor"]
            )

            scenario_compressor = max(
                0.0,
                scenario_compressor * load_factor,
            )

            scenario_hvac = max(
                0.0,
                scenario_hvac * load_factor,
            )

            scenario_renewable = max(
                0.0,
                renewable
                * float(template["renewable_factor"]),
            )

            scenario_boiler = (
                optimized_boiler
                if use_targets
                else boiler
            )

            point = {
                "production_load_kw": round(
                    production_load_kw,
                    3,
                ),
                "compressor_power_kw": round(
                    scenario_compressor,
                    3,
                ),
                "hvac_power_kw": round(
                    scenario_hvac,
                    3,
                ),
                "renewable_generation_kw": round(
                    scenario_renewable,
                    3,
                ),
                "battery_charge_kw": 0.0,
                "battery_discharge_kw": 0.0,
                "grid_export_limit_kw": float(
                    template["export_limit_kw"]
                ),
                "boiler_fuel_m3_hr": round(
                    scenario_boiler,
                    3,
                ),
            }

            # ---------------------------------------------------------
            # Battery dispatch
            # ---------------------------------------------------------

            electrical_load = (
                point["production_load_kw"]
                + point["compressor_power_kw"]
                + point["hvac_power_kw"]
            )

            surplus = max(
                0.0,
                point["renewable_generation_kw"]
                - electrical_load,
            )

            deficit = max(
                0.0,
                electrical_load
                - point["renewable_generation_kw"],
            )

            mode = template["battery_mode"]

            if mode == "recommendation":

                point["battery_charge_kw"] = min(
                    recommended_charge,
                    surplus,
                )

                point["battery_discharge_kw"] = min(
                    recommended_discharge,
                    deficit,
                )

            elif mode == "charge_surplus":

                point["battery_charge_kw"] = min(
                    max(recommended_charge, 40.0),
                    surplus,
                )

            elif mode == "discharge_deficit":

                point["battery_discharge_kw"] = min(
                    max(recommended_discharge, 25.0),
                    deficit,
                )

            # ---------------------------------------------------------
            # Track which Module 4 recommendations were applied
            # ---------------------------------------------------------

            applied_agents = {
                agent
                for agent in (
                    "boiler_agent",
                    "compressor_agent",
                    "hvac_agent",
                )
                if use_targets
                and agent in recommendation_index
            }

            if (
                use_targets
                and "battery_management_agent"
                in recommendation_index
                and (
                    point["battery_charge_kw"] > 0
                    or point["battery_discharge_kw"] > 0
                )
            ):
                applied_agents.add(
                    "battery_management_agent"
                )

            applied = tuple(
                sorted(applied_agents)
            )

            # ---------------------------------------------------------
            # Scenario contract
            # ---------------------------------------------------------

            scenario = Scenario(
                scenario_id=str(
                    template["scenario_id"]
                ),
                name=str(
                    template["name"]
                ),
                description=str(
                    template["description"]
                ),
                horizon_hours=float(
                    horizon_hours
                ),
                operating_point=point,
                applied_recommendations=applied,
                assumptions=(
                    "Production forecast is represented as units/hour "
                    "and is not converted into electrical kW.",
                    "Electrical demand includes compressor and HVAC "
                    "power currently forecast by Module 3.",
                    "Solar/inverter generation is treated as renewable "
                    "generation; battery dispatch is simulated separately.",
                    "Renewable energy is dispatched before battery and "
                    "grid energy.",
                    f"Forecast production output is "
                    f"{production_units:.2f} units/hour.",
                ),
            )

            self.validator.require_valid(
                scenario
            )

            scenarios.append(
                scenario
            )

        return scenarios