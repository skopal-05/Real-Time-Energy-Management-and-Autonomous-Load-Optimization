"""Main optimizer for producing feasible industrial operating values."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from algorithms import GeneticAlgorithm
from contracts import (
    DECISION_VARIABLES,
    OptimizationProblem,
    OptimizationResult,
    VariableBound,
    finite_number,
)
from optimization.constraints import ConstraintChecker
from optimization.objective_function import ObjectiveFunction
from optimization.optimization_validator import OptimizationValidator


class Optimizer:
    """Build a problem from Module 4/5 data and optimize its operating state."""

    def __init__(
        self,
        *,
        algorithm: GeneticAlgorithm | None = None,
        objective: ObjectiveFunction | None = None,
    ) -> None:
        self.algorithm = algorithm or GeneticAlgorithm()
        self.objective = objective or ObjectiveFunction()
        self.constraints = ConstraintChecker()
        self.validator = OptimizationValidator()

    def build_problem(
        self,
        best_scenario: Mapping[str, Any],
        recommendations: Sequence[Mapping[str, Any]] | Mapping[str, Any],
        *,
        system_state: Mapping[str, Any] | None = None,
        weights: Mapping[str, float] | None = None,
    ) -> OptimizationProblem:
        scenario = best_scenario.get("best_scenario", best_scenario)
        operating = scenario.get("operating_point", {})
        if not isinstance(operating, Mapping):
            raise ValueError("best scenario must contain an operating_point object")
        recommendation_items = self._recommendation_items(recommendations)
        setpoints = self._setpoints_by_agent(recommendation_items)
        state = dict(system_state or {})

        production_target = self._first_number(
            setpoints,
            ("cost_optimization_agent", "production_load_target_kw"),
            ("load_balancing_agent", "total_power_target_kw"),
            default=finite_number(operating, "production_load_kw", default=0.0, minimum=0.0),
        )
        if production_target <= 0:
            raise ValueError(
                "production load is zero; provide Module 4 production_load_target_kw or total_power_target_kw"
            )

        compressor_min = self._first_number(
            setpoints,
            ("compressor_agent", "compressor_power_target_kw"),
            default=finite_number(operating, "compressor_power_kw", minimum=0.0),
        )
        hvac_min = self._first_number(
            setpoints,
            ("hvac_agent", "hvac_power_target_kw"),
            default=finite_number(operating, "hvac_power_kw", minimum=0.0),
        )
        boiler_min = self._first_number(
            setpoints,
            ("boiler_agent", "boiler_fuel_target_m3_hr"),
            default=finite_number(operating, "boiler_fuel_m3_hr", minimum=0.0),
        )
        charge_max = finite_number(state, "maximum_charge_kw", default=50.0, minimum=0.0)
        discharge_max = finite_number(state, "maximum_discharge_kw", default=50.0, minimum=0.0)
        export_max = finite_number(
            state,
            "grid_export_limit_kw",
            default=finite_number(operating, "grid_export_limit_kw", default=100.0, minimum=0.0),
            minimum=0.0,
        )
        baseline = {
            "production_load_kw": production_target,
            "compressor_power_kw": max(
                compressor_min, finite_number(operating, "compressor_power_kw", minimum=0.0)
            ),
            "hvac_power_kw": max(hvac_min, finite_number(operating, "hvac_power_kw", minimum=0.0)),
            "battery_charge_kw": finite_number(operating, "battery_charge_kw", default=0.0, minimum=0.0),
            "battery_discharge_kw": finite_number(
                operating, "battery_discharge_kw", default=0.0, minimum=0.0
            ),
            "grid_export_limit_kw": finite_number(
                operating, "grid_export_limit_kw", default=export_max, minimum=0.0
            ),
            "boiler_fuel_m3_hr": max(
                boiler_min, finite_number(operating, "boiler_fuel_m3_hr", minimum=0.0)
            ),
            "renewable_generation_kw": finite_number(
                operating,
                "renewable_generation_kw",
                default=finite_number(state, "renewable_generation_kw", default=0.0, minimum=0.0),
                minimum=0.0,
            ),
        }
        bounds = {
            "production_load_kw": VariableBound(production_target, production_target),
            "compressor_power_kw": VariableBound(
                compressor_min,
                finite_number(state, "maximum_compressor_power_kw", default=max(100.0, compressor_min)),
            ),
            "hvac_power_kw": VariableBound(
                hvac_min, finite_number(state, "maximum_hvac_power_kw", default=max(100.0, hvac_min))
            ),
            "battery_charge_kw": VariableBound(0.0, charge_max),
            "battery_discharge_kw": VariableBound(0.0, discharge_max),
            "grid_export_limit_kw": VariableBound(0.0, export_max),
            "boiler_fuel_m3_hr": VariableBound(
                boiler_min,
                finite_number(state, "maximum_fuel_flow_m3_hr", default=max(200.0, boiler_min)),
            ),
        }
        selected_weights = dict(weights or {"energy": 0.35, "cost": 0.35, "carbon": 0.30})
        total_weight = sum(float(value) for value in selected_weights.values())
        if total_weight <= 0:
            raise ValueError("optimization weights must have a positive total")
        selected_weights = {name: float(value) / total_weight for name, value in selected_weights.items()}
        problem = OptimizationProblem(
            baseline_state=baseline,
            bounds=bounds,
            horizon_hours=finite_number(scenario, "horizon_hours", default=1.0, minimum=0.000001),
            state_of_charge_percent=finite_number(state, "state_of_charge_percent", default=50.0),
            battery_capacity_kwh=finite_number(state, "capacity_kwh", default=100.0, minimum=0.000001),
            minimum_soc_percent=finite_number(state, "minimum_soc_percent", default=20.0),
            maximum_soc_percent=finite_number(state, "maximum_soc_percent", default=90.0),
            grid_import_limit_kw=finite_number(state, "grid_import_limit_kw", default=500.0, minimum=0.0),
            weights=selected_weights,
        )
        self.validator.require_valid(self.validator.validate_problem(problem), "optimization problem")
        return problem

    def optimize(self, problem: OptimizationProblem) -> OptimizationResult:
        self.validator.require_valid(self.validator.validate_problem(problem), "optimization problem")
        baseline_state = self.constraints.repair(problem.baseline_state, problem)
        baseline_metrics = self.objective.metrics(baseline_state, problem)

        def fitness(candidate: Mapping[str, float]) -> float:
            repaired = self.constraints.repair(candidate, problem)
            return self.objective.score(repaired, problem, baseline_metrics)[0]

        ga_result = self.algorithm.minimize(
            fitness,
            {name: (bound.minimum, bound.maximum) for name, bound in problem.bounds.items()},
            initial_values=baseline_state,
        )
        ga_candidate = self.constraints.repair(ga_result.values, problem)
        dispatch_candidate = self._balanced_renewable_dispatch(ga_candidate, problem)
        candidates = [ga_candidate, dispatch_candidate, baseline_state]
        optimized_state = min(
            candidates,
            key=lambda candidate: self.objective.score(candidate, problem, baseline_metrics)[0],
        )
        optimized_metrics = self.objective.metrics(optimized_state, problem)
        _, objective = self.objective.score(optimized_state, problem, baseline_metrics)
        violations = tuple(self.constraints.violations(optimized_state, problem))
        rounded_state = {name: round(value, 3) for name, value in optimized_state.items()}
        rounded_state["renewable_generation_kw"] = round(
            problem.baseline_state["renewable_generation_kw"], 3
        )
        rounded_state["projected_soc_percent"] = round(
            optimized_metrics["battery"]["projected_soc_percent"], 3
        )
        result = OptimizationResult(
            baseline_state={name: round(value, 3) for name, value in baseline_state.items()},
            optimized_state=rounded_state,
            baseline_metrics=baseline_metrics,
            optimized_metrics=optimized_metrics,
            objective=objective,
            feasible=not violations,
            violations=violations,
            algorithm={
                "name": "real_valued_genetic_algorithm",
                "generations": ga_result.generations,
                "population_size": self.algorithm.population_size,
                "evaluations": ga_result.evaluations,
                "seed": self.algorithm.seed,
                "best_fitness": objective["total"],
            },
        )
        self.validator.require_valid(self.validator.validate_result(result, problem), "optimization result")
        return result

    def _balanced_renewable_dispatch(
        self, state: Mapping[str, float], problem: OptimizationProblem
    ) -> dict[str, float]:
        """Polish a GA candidate at the export/charging boundary.

        A real-valued GA normally converges very close to this boundary but not
        exactly onto it. This deterministic pass avoids reporting tiny amounts
        of renewable curtailment caused only by floating-point search noise.
        """

        candidate = dict(state)
        candidate["grid_export_limit_kw"] = problem.bounds["grid_export_limit_kw"].maximum
        candidate["battery_discharge_kw"] = 0.0
        useful_load = sum(
            candidate[name]
            for name in ("production_load_kw", "compressor_power_kw", "hvac_power_kw")
        )
        renewable_surplus = max(
            0.0, problem.baseline_state["renewable_generation_kw"] - useful_load
        )
        required_charge = max(
            0.0, renewable_surplus - candidate["grid_export_limit_kw"]
        )
        candidate["battery_charge_kw"] = problem.bounds["battery_charge_kw"].clamp(
            required_charge
        )
        return self.constraints.repair(candidate, problem)

    @staticmethod
    def _recommendation_items(
        recommendations: Sequence[Mapping[str, Any]] | Mapping[str, Any]
    ) -> Sequence[Mapping[str, Any]]:
        if isinstance(recommendations, Mapping):
            items = recommendations.get("recommendations", [])
        else:
            items = recommendations
        if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
            raise ValueError("recommendations must be a list")
        return items

    @staticmethod
    def _setpoints_by_agent(
        recommendations: Sequence[Mapping[str, Any]],
    ) -> dict[str, Mapping[str, Any]]:
        result = {}
        for item in recommendations:
            if isinstance(item, Mapping) and isinstance(item.get("setpoints"), Mapping):
                result[str(item.get("agent", ""))] = item["setpoints"]
        return result

    @staticmethod
    def _first_number(
        setpoints: Mapping[str, Mapping[str, Any]],
        *paths: tuple[str, str],
        default: float,
    ) -> float:
        for agent, key in paths:
            if agent in setpoints and key in setpoints[agent]:
                return finite_number(setpoints[agent], key, minimum=0.0)
        return float(default)
