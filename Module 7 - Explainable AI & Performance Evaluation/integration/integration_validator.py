"""
Final validation utilities for Module 7 integration.

Validates the complete:
Module 3 → Module 4 → Module 5 → Module 6 → Module 7
pipeline.
"""

from __future__ import annotations

from math import isfinite
from pathlib import Path
from typing import Any, Mapping


class FinalIntegrationValidator:
    """Validate upstream artifacts and final Module 7 outputs."""

    name = "final_integration_validator"

    # ==============================================================
    # MODULE 3
    # ==============================================================

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

    # ==============================================================
    # MODULE 4
    # ==============================================================

    REQUIRED_RECOMMENDATION_FIELDS = (
        "agent",
        "action",
        "priority",
        "setpoints",
    )

    VALID_PRIORITIES = {
        "low",
        "medium",
        "high",
        "critical",
    }

    # ==============================================================
    # MODULE 5
    # ==============================================================

    REQUIRED_SCENARIO_IDS = {
        "baseline",
        "agent_optimized",
        "renewable_first",
        "cost_saver",
        "resilience",
    }

    # ==============================================================
    # MODULE 6
    # ==============================================================

    REQUIRED_OPTIMIZATION_REPORT_SECTIONS = (
        "summary",
        "baseline_metrics",
        "optimized_metrics",
    )

    # ==============================================================
    # FORECAST VALIDATION
    # ==============================================================

    def validate_forecast(
        self,
        forecast: Mapping[str, Any],
    ) -> list[str]:

        errors: list[str] = []

        if not isinstance(
            forecast,
            Mapping,
        ):
            return [
                "forecast must be an object"
            ]

        for section in self.REQUIRED_FORECAST_SECTIONS:
            if section not in forecast:
                errors.append(
                    f"missing forecast section: {section}"
                )

        future_state = forecast.get(
            "future_state"
        )

        energy_forecast = forecast.get(
            "energy_forecast"
        )

        if not isinstance(
            future_state,
            Mapping,
        ):
            errors.append(
                "future_state must be an object"
            )
        else:
            for field in self.REQUIRED_FUTURE_STATE_FIELDS:
                self._validate_numeric_field(
                    future_state,
                    field,
                    errors,
                    "future_state",
                )

        if not isinstance(
            energy_forecast,
            Mapping,
        ):
            errors.append(
                "energy_forecast must be an object"
            )
        else:
            for field in self.REQUIRED_ENERGY_FIELDS:
                self._validate_numeric_field(
                    energy_forecast,
                    field,
                    errors,
                    "energy_forecast",
                )

        return errors

    # ==============================================================
    # RECOMMENDATION VALIDATION
    # ==============================================================

    def validate_recommendations(
        self,
        recommendations: list[Mapping[str, Any]],
    ) -> list[str]:

        errors: list[str] = []

        if not recommendations:
            return [
                "recommendations must not be empty"
            ]

        for index, recommendation in enumerate(
            recommendations
        ):

            label = (
                f"recommendation[{index}]"
            )

            for field in self.REQUIRED_RECOMMENDATION_FIELDS:
                if field not in recommendation:
                    errors.append(
                        f"{label} missing {field}"
                    )

            agent = recommendation.get(
                "agent"
            )

            action = recommendation.get(
                "action"
            )

            priority = recommendation.get(
                "priority"
            )

            setpoints = recommendation.get(
                "setpoints"
            )

            if not isinstance(
                agent,
                str,
            ) or not agent.strip():
                errors.append(
                    f"{label}.agent invalid"
                )

            if not isinstance(
                action,
                str,
            ) or not action.strip():
                errors.append(
                    f"{label}.action invalid"
                )

            if priority not in self.VALID_PRIORITIES:
                errors.append(
                    f"{label}.priority invalid: "
                    f"{priority}"
                )

            if not isinstance(
                setpoints,
                Mapping,
            ):
                errors.append(
                    f"{label}.setpoints must be an object"
                )

        return errors

    # ==============================================================
    # SCENARIO VALIDATION
    # ==============================================================

    def validate_scenarios(
        self,
        scenarios: list[Mapping[str, Any]],
    ) -> list[str]:

        errors: list[str] = []

        if not scenarios:
            return [
                "ranked scenarios must not be empty"
            ]

        scenario_ids = {
            item.get("scenario_id")
            for item in scenarios
        }

        missing = (
            self.REQUIRED_SCENARIO_IDS
            - scenario_ids
        )

        if missing:
            errors.append(
                "missing scenarios: "
                + ", ".join(
                    sorted(missing)
                )
            )

        ranks = []

        for index, scenario in enumerate(
            scenarios
        ):

            scenario_id = scenario.get(
                "scenario_id",
                f"scenario_{index}",
            )

            ranking = scenario.get(
                "ranking"
            )

            if not isinstance(
                ranking,
                Mapping,
            ):
                errors.append(
                    f"{scenario_id} missing ranking"
                )
                continue

            rank = ranking.get(
                "rank"
            )

            score = ranking.get(
                "score"
            )

            if not isinstance(
                rank,
                int,
            ):
                errors.append(
                    f"{scenario_id} rank must be integer"
                )
            else:
                ranks.append(rank)

            if (
                not isinstance(
                    score,
                    (int, float),
                )
                or isinstance(
                    score,
                    bool,
                )
                or not isfinite(
                    float(score)
                )
            ):
                errors.append(
                    f"{scenario_id} score must be finite numeric"
                )

        if ranks and sorted(ranks) != list(
            range(
                1,
                len(ranks) + 1,
            )
        ):
            errors.append(
                "scenario ranks must be consecutive starting at 1"
            )

        return errors

    # ==============================================================
    # OPTIMIZATION VALIDATION
    # ==============================================================

    def validate_optimization_report(
        self,
        report: Mapping[str, Any],
    ) -> list[str]:

        errors: list[str] = []

        if not isinstance(
            report,
            Mapping,
        ):
            return [
                "optimization report must be an object"
            ]

        for section in self.REQUIRED_OPTIMIZATION_REPORT_SECTIONS:
            if section not in report:
                errors.append(
                    f"optimization report missing {section}"
                )

        summary = report.get(
            "summary"
        )

        if not isinstance(
            summary,
            Mapping,
        ):
            errors.append(
                "optimization summary must be an object"
            )
        elif summary.get(
            "feasible"
        ) is not True:
            errors.append(
                "optimization result is not feasible"
            )

        baseline = report.get(
            "baseline_metrics"
        )

        optimized = report.get(
            "optimized_metrics"
        )

        if not isinstance(
            baseline,
            Mapping,
        ):
            errors.append(
                "baseline_metrics must be an object"
            )

        if not isinstance(
            optimized,
            Mapping,
        ):
            errors.append(
                "optimized_metrics must be an object"
            )

        return errors

    # ==============================================================
    # OPTIMIZED STATE
    # ==============================================================

    def validate_optimized_state(
        self,
        state: Mapping[str, Any],
    ) -> list[str]:

        errors: list[str] = []

        required = (
            "production_load_kw",
            "compressor_power_kw",
            "hvac_power_kw",
            "battery_charge_kw",
            "battery_discharge_kw",
            "grid_export_limit_kw",
            "boiler_fuel_m3_hr",
            "renewable_generation_kw",
            "projected_soc_percent",
        )

        for field in required:

            if field not in state:
                errors.append(
                    f"optimized_state missing {field}"
                )
                continue

            value = state[field]

            if (
                isinstance(
                    value,
                    bool,
                )
                or not isinstance(
                    value,
                    (int, float),
                )
                or not isfinite(
                    float(value)
                )
            ):
                errors.append(
                    f"optimized_state.{field} "
                    "must be finite numeric"
                )

        soc = state.get(
            "projected_soc_percent"
        )

        if isinstance(
            soc,
            (int, float),
        ) and not isinstance(
            soc,
            bool,
        ):
            if not 0 <= float(soc) <= 100:
                errors.append(
                    "projected_soc_percent must be between 0 and 100"
                )

        return errors

    # ==============================================================
    # MODULE 7 OUTPUT VALIDATION
    # ==============================================================

    def validate_final_output(
        self,
        result: Mapping[str, Any],
    ) -> list[str]:

        errors: list[str] = []

        required = (
            "generated_at",
            "module",
            "pipeline",
            "performance",
            "monitoring",
            "explainability",
            "anomaly_detection",
            "validation",
        )

        for field in required:
            if field not in result:
                errors.append(
                    f"final output missing {field}"
                )

        validation = result.get(
            "validation"
        )

        if isinstance(
            validation,
            Mapping,
        ):
            if validation.get(
                "valid"
            ) is not True:
                errors.append(
                    "final validation status is not valid"
                )

        return errors

    # ==============================================================
    # OUTPUT FILE VALIDATION
    # ==============================================================

    @staticmethod
    def validate_output_files(
        output_files: Mapping[str, str],
    ) -> list[str]:

        errors: list[str] = []

        required = (
            "performance",
            "monitoring",
            "explainability",
            "anomalies",
            "final_report",
        )

        for name in required:

            if name not in output_files:
                errors.append(
                    f"missing output path: {name}"
                )
                continue

            path = Path(
                output_files[name]
            )

            if not path.is_file():
                errors.append(
                    f"output file does not exist: {path}"
                )

        return errors

    # ==============================================================
    # COMPLETE VALIDATION
    # ==============================================================

    def validate_pipeline(
        self,
        *,
        forecast: Mapping[str, Any],
        recommendations: list[Mapping[str, Any]],
        scenarios: list[Mapping[str, Any]],
        optimization_report: Mapping[str, Any],
        optimized_state: Mapping[str, Any],
        final_output: Mapping[str, Any] | None = None,
        output_files: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:

        forecast_errors = self.validate_forecast(
            forecast
        )

        recommendation_errors = (
            self.validate_recommendations(
                recommendations
            )
        )

        scenario_errors = (
            self.validate_scenarios(
                scenarios
            )
        )

        optimization_errors = (
            self.validate_optimization_report(
                optimization_report
            )
        )

        optimized_state_errors = (
            self.validate_optimized_state(
                optimized_state
            )
        )

        final_output_errors = []

        if final_output is not None:
            final_output_errors = (
                self.validate_final_output(
                    final_output
                )
            )

        output_errors = []

        if output_files is not None:
            output_errors = (
                self.validate_output_files(
                    output_files
                )
            )

        all_errors = (
            forecast_errors
            + recommendation_errors
            + scenario_errors
            + optimization_errors
            + optimized_state_errors
            + final_output_errors
            + output_errors
        )

        return {
            "valid": not all_errors,
            "forecast_valid": not forecast_errors,
            "recommendations_valid": not recommendation_errors,
            "scenarios_valid": not scenario_errors,
            "optimization_valid": not optimization_errors,
            "optimized_state_valid": not optimized_state_errors,
            "final_output_valid": not final_output_errors,
            "outputs_valid": not output_errors,
            "forecast_errors": forecast_errors,
            "recommendation_errors": recommendation_errors,
            "scenario_errors": scenario_errors,
            "optimization_errors": optimization_errors,
            "optimized_state_errors": optimized_state_errors,
            "final_output_errors": final_output_errors,
            "output_errors": output_errors,
        }

    # ==============================================================
    # HELPERS
    # ==============================================================

    @staticmethod
    def _validate_numeric_field(
        data: Mapping[str, Any],
        field: str,
        errors: list[str],
        section: str,
    ) -> None:

        if field not in data:
            errors.append(
                f"{section}.{field} missing"
            )
            return

        value = data[field]

        if (
            isinstance(
                value,
                bool,
            )
            or not isinstance(
                value,
                (int, float),
            )
            or not isfinite(
                float(value)
            )
        ):
            errors.append(
                f"{section}.{field} must be finite numeric"
            )

    @staticmethod
    def require_valid(
        errors: list[str],
        label: str,
    ) -> None:

        if errors:
            raise ValueError(
                f"invalid {label}: "
                + "; ".join(errors)
            )