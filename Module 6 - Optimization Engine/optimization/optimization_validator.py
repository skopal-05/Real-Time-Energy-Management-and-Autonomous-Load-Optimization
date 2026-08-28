"""Input and output validation for the optimization layer."""

from __future__ import annotations

from math import isfinite
from typing import Any, Mapping

from contracts import DECISION_VARIABLES, OptimizationProblem, OptimizationResult
from optimization.constraints import ConstraintChecker


class OptimizationValidator:
    def validate_problem(self, problem: OptimizationProblem) -> list[str]:
        errors: list[str] = []
        for name in (*DECISION_VARIABLES, "renewable_generation_kw"):
            value = problem.baseline_state.get(name)
            if value is None:
                errors.append(f"baseline_state missing {name}")
            elif isinstance(value, bool) or not isfinite(float(value)) or float(value) < 0:
                errors.append(f"baseline_state {name} must be a finite non-negative number")
        missing_bounds = set(DECISION_VARIABLES) - set(problem.bounds)
        if missing_bounds:
            errors.append(f"missing bounds: {sorted(missing_bounds)}")
        if problem.horizon_hours <= 0:
            errors.append("horizon_hours must be positive")
        if problem.battery_capacity_kwh <= 0:
            errors.append("battery_capacity_kwh must be positive")
        if not 0 < problem.battery_efficiency <= 1:
            errors.append("battery_efficiency must be in (0, 1]")
        if not problem.minimum_soc_percent <= problem.state_of_charge_percent <= problem.maximum_soc_percent:
            errors.append("initial state_of_charge_percent is outside SOC limits")
        if set(problem.weights) != {"energy", "cost", "carbon"}:
            errors.append("weights must contain energy, cost, and carbon")
        elif any(value < 0 for value in problem.weights.values()) or abs(sum(problem.weights.values()) - 1) > 1e-6:
            errors.append("weights must be non-negative and sum to 1")
        return errors

    def validate_result(
        self, result: OptimizationResult, problem: OptimizationProblem
    ) -> list[str]:
        errors = ConstraintChecker().violations(result.optimized_state, problem)
        if result.feasible != (not errors):
            errors.append("result feasible flag does not match constraint validation")
        for group in ("energy", "cost", "carbon"):
            if group not in result.optimized_metrics:
                errors.append(f"optimized metrics missing {group}")
        return errors

    @staticmethod
    def require_valid(errors: list[str], label: str = "optimization data") -> None:
        if errors:
            raise ValueError(f"invalid {label}: " + "; ".join(errors))

