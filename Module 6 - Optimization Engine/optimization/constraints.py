"""Equipment, battery, and system constraints for candidate operating states."""

from __future__ import annotations

from typing import Mapping

from contracts import DECISION_VARIABLES, OptimizationProblem


class ConstraintChecker:
    """Validate or repair an operating state against an OptimizationProblem."""

    TOLERANCE = 1e-6

    def violations(
        self, state: Mapping[str, float], problem: OptimizationProblem
    ) -> list[str]:
        violations: list[str] = []
        for name in DECISION_VARIABLES:
            if name not in state:
                violations.append(f"missing decision variable: {name}")
                continue
            value = float(state[name])
            bound = problem.bounds[name]
            if value < bound.minimum - self.TOLERANCE or value > bound.maximum + self.TOLERANCE:
                violations.append(
                    f"{name}={value:.4f} outside [{bound.minimum:.4f}, {bound.maximum:.4f}]"
                )

        charge = float(state.get("battery_charge_kw", 0.0))
        discharge = float(state.get("battery_discharge_kw", 0.0))
        if charge > self.TOLERANCE and discharge > self.TOLERANCE:
            violations.append("battery cannot charge and discharge simultaneously")

        next_soc = self.projected_soc(state, problem)
        if next_soc < problem.minimum_soc_percent - self.TOLERANCE:
            violations.append("projected battery SOC is below the minimum")
        if next_soc > problem.maximum_soc_percent + self.TOLERANCE:
            violations.append("projected battery SOC is above the maximum")

        balance = self.energy_balance(state, problem)
        if balance["grid_import_kw"] > problem.grid_import_limit_kw + self.TOLERANCE:
            violations.append("required grid import exceeds the grid import limit")
        return violations

    def is_feasible(self, state: Mapping[str, float], problem: OptimizationProblem) -> bool:
        return not self.violations(state, problem)

    def repair(self, state: Mapping[str, float], problem: OptimizationProblem) -> dict[str, float]:
        repaired = {
            name: problem.bounds[name].clamp(float(state.get(name, problem.baseline_state[name])))
            for name in DECISION_VARIABLES
        }
        charge = repaired["battery_charge_kw"]
        discharge = repaired["battery_discharge_kw"]
        if charge > 0 and discharge > 0:
            if charge >= discharge:
                repaired["battery_discharge_kw"] = 0.0
            else:
                repaired["battery_charge_kw"] = 0.0

        hours = problem.horizon_hours
        capacity = problem.battery_capacity_kwh
        efficiency = problem.battery_efficiency
        max_charge_for_soc = max(
            0.0,
            (problem.maximum_soc_percent - problem.state_of_charge_percent)
            * capacity
            / (100 * hours * efficiency),
        )
        max_discharge_for_soc = max(
            0.0,
            (problem.state_of_charge_percent - problem.minimum_soc_percent)
            * capacity
            * efficiency
            / (100 * hours),
        )
        repaired["battery_charge_kw"] = min(repaired["battery_charge_kw"], max_charge_for_soc)
        repaired["battery_discharge_kw"] = min(
            repaired["battery_discharge_kw"], max_discharge_for_soc
        )
        return repaired

    @staticmethod
    def projected_soc(state: Mapping[str, float], problem: OptimizationProblem) -> float:
        charged = (
            float(state.get("battery_charge_kw", 0.0))
            * problem.horizon_hours
            * problem.battery_efficiency
        )
        discharged = (
            float(state.get("battery_discharge_kw", 0.0))
            * problem.horizon_hours
            / problem.battery_efficiency
        )
        return problem.state_of_charge_percent + (charged - discharged) / problem.battery_capacity_kwh * 100

    def energy_balance(
        self, state: Mapping[str, float], problem: OptimizationProblem
    ) -> dict[str, float]:
        useful_load = sum(
            float(state.get(name, 0.0))
            for name in ("production_load_kw", "compressor_power_kw", "hvac_power_kw")
        )
        charge = float(state.get("battery_charge_kw", 0.0))
        discharge = float(state.get("battery_discharge_kw", 0.0))
        renewable = float(problem.baseline_state["renewable_generation_kw"])
        site_demand = useful_load + charge
        renewable_to_site = min(renewable, site_demand)
        remaining_demand = max(0.0, site_demand - renewable_to_site - discharge)
        surplus = max(0.0, renewable - renewable_to_site)
        export = min(surplus, float(state.get("grid_export_limit_kw", 0.0)))
        curtailed = max(0.0, surplus - export)
        return {
            "useful_load_kw": useful_load,
            "site_demand_kw": site_demand,
            "renewable_to_site_kw": renewable_to_site,
            "grid_import_kw": remaining_demand,
            "grid_export_kw": export,
            "curtailed_power_kw": curtailed,
        }

