"""Validation utilities for Module 4/5 to Module 6 integration."""

from __future__ import annotations

from math import isfinite
from pathlib import Path
from typing import Any, Mapping

from contracts import (
    DECISION_VARIABLES,
    OptimizationProblem,
    OptimizationResult,
)
from optimization.constraints import ConstraintChecker
from optimization.optimization_validator import OptimizationValidator


class IntegrationValidator:
    """Validate Module 6 integration inputs and outputs."""

    name = "integration_validator"

    REQUIRED_SCENARIO_FIELDS = (
        "scenario_id",
        "name",
        "horizon_hours",
        "operating_point",
    )

    REQUIRED_RECOMMENDATION_FIELDS = (
        "agent",
        "action",
        "priority",
        "setpoints",
    )

    def __init__(self) -> None:
        self.optimization_validator = OptimizationValidator()
        self.constraints = ConstraintChecker()

    # ==============================================================
    # MODULE 5 VALIDATION
    # ==============================================================

    def validate_best_scenario(
        self,
        best_scenario: Mapping[str, Any],
    ) -> list[str]:
        errors: list[str] = []

        if not isinstance(
            best_scenario,
            Mapping,
        ):
            return ["best_scenario must be an object"]

        for field in self.REQUIRED_SCENARIO_FIELDS:
            if field not in best_scenario:
                errors.append(
                    f"best_scenario missing {field}"
                )

        operating_point = best_scenario.get(
            "operating_point"
        )

        if not isinstance(
            operating_point,
            Mapping,
        ):
            errors.append(
                "operating_point must be an object"
            )
            return errors

        required_operating_values = (
            "production_load_kw",
            "compressor_power_kw",
            "hvac_power_kw",
            "renewable_generation_kw",
            "battery_charge_kw",
            "battery_discharge_kw",
            "grid_export_limit_kw",
            "boiler_fuel_m3_hr",
        )

        for name in required_operating_values:
            if name not in operating_point:
                errors.append(
                    f"operating_point missing {name}"
                )
                continue

            value = operating_point[name]

            if isinstance(value, bool):
                errors.append(
                    f"operating_point.{name} must be numeric"
                )
                continue

            try:
                numeric = float(value)
            except (TypeError, ValueError):
                errors.append(
                    f"operating_point.{name} must be numeric"
                )
                continue

            if not isfinite(numeric):
                errors.append(
                    f"operating_point.{name} must be finite"
                )

            if numeric < 0:
                errors.append(
                    f"operating_point.{name} must be non-negative"
                )

        return errors

    # ==============================================================
    # MODULE 4 VALIDATION
    # ==============================================================

    def validate_recommendations(
        self,
        recommendations: list[Mapping[str, Any]],
    ) -> list[str]:
        errors: list[str] = []

        if not recommendations:
            return [
                "Module 4 recommendations must not be empty"
            ]

        for index, recommendation in enumerate(
            recommendations
        ):
            label = f"recommendation[{index}]"

            if not isinstance(
                recommendation,
                Mapping,
            ):
                errors.append(
                    f"{label} must be an object"
                )
                continue

            for field in self.REQUIRED_RECOMMENDATION_FIELDS:
                if field not in recommendation:
                    errors.append(
                        f"{label} missing {field}"
                    )

            agent = recommendation.get("agent")

            if not isinstance(
                agent,
                str,
            ) or not agent.strip():
                errors.append(
                    f"{label}.agent must be non-empty"
                )

            setpoints = recommendation.get(
                "setpoints"
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
    # OPTIMIZATION PROBLEM
    # ==============================================================

    def validate_problem(
        self,
        problem: OptimizationProblem,
    ) -> list[str]:
        return self.optimization_validator.validate_problem(
            problem
        )

    # ==============================================================
    # OPTIMIZATION RESULT
    # ==============================================================

    def validate_result(
        self,
        result: OptimizationResult,
        problem: OptimizationProblem,
    ) -> list[str]:
        errors = self.optimization_validator.validate_result(
            result,
            problem,
        )

        for variable in DECISION_VARIABLES:
            if variable not in result.optimized_state:
                errors.append(
                    f"optimized_state missing {variable}"
                )

        if not result.feasible:
            errors.append(
                "optimization result is not feasible"
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
            "optimized_state",
            "recommendations",
            "report",
        )

        for name in required:
            if name not in output_files:
                errors.append(
                    f"missing output path: {name}"
                )
                continue

            path = Path(output_files[name])

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
        best_scenario: Mapping[str, Any],
        recommendations: list[Mapping[str, Any]],
        problem: OptimizationProblem,
        result: OptimizationResult,
        output_files: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        scenario_errors = self.validate_best_scenario(
            best_scenario
        )

        recommendation_errors = self.validate_recommendations(
            recommendations
        )

        problem_errors = self.validate_problem(
            problem
        )

        result_errors = self.validate_result(
            result,
            problem,
        )

        output_errors = []

        if output_files is not None:
            output_errors = self.validate_output_files(
                output_files
            )

        all_errors = (
            scenario_errors
            + recommendation_errors
            + problem_errors
            + result_errors
            + output_errors
        )

        return {
            "valid": not all_errors,
            "scenario_valid": not scenario_errors,
            "recommendations_valid": not recommendation_errors,
            "problem_valid": not problem_errors,
            "result_valid": not result_errors,
            "outputs_valid": not output_errors,
            "scenario_errors": scenario_errors,
            "recommendation_errors": recommendation_errors,
            "problem_errors": problem_errors,
            "result_errors": result_errors,
            "output_errors": output_errors,
        }

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