"""Multi-objective energy, cost, and carbon evaluation."""

from __future__ import annotations

from typing import Mapping

from contracts import OptimizationProblem
from optimization.constraints import ConstraintChecker


class ObjectiveFunction:
    """Evaluate candidates and minimize normalized energy, cost, and carbon impact."""

    def __init__(
        self,
        *,
        import_tariff_inr_kwh: float = 8.0,
        export_price_inr_kwh: float = 4.0,
        fuel_price_inr_m3: float = 48.0,
        battery_degradation_inr_kwh: float = 1.5,
        grid_carbon_kg_kwh: float = 0.716,
        fuel_carbon_kg_m3: float = 2.0,
        fuel_energy_kwh_m3: float = 10.55,
        constraint_penalty: float = 1_000.0,
    ) -> None:
        self.import_tariff = import_tariff_inr_kwh
        self.export_price = export_price_inr_kwh
        self.fuel_price = fuel_price_inr_m3
        self.battery_degradation = battery_degradation_inr_kwh
        self.grid_carbon = grid_carbon_kg_kwh
        self.fuel_carbon = fuel_carbon_kg_m3
        self.fuel_energy = fuel_energy_kwh_m3
        self.constraint_penalty = constraint_penalty
        self.constraints = ConstraintChecker()

    def metrics(
        self, state: Mapping[str, float], problem: OptimizationProblem
    ) -> dict[str, dict[str, float]]:
        balance = self.constraints.energy_balance(state, problem)
        hours = problem.horizon_hours
        grid_import = balance["grid_import_kw"] * hours
        grid_export = balance["grid_export_kw"] * hours
        curtailed = balance["curtailed_power_kw"] * hours
        site_demand = balance["site_demand_kw"] * hours
        boiler_fuel = float(state["boiler_fuel_m3_hr"]) * hours
        charge = float(state["battery_charge_kw"]) * hours
        discharge = float(state["battery_discharge_kw"]) * hours
        gross_cost = (
            grid_import * self.import_tariff
            + boiler_fuel * self.fuel_price
            + (charge + discharge) * self.battery_degradation
        )
        export_revenue = grid_export * self.export_price
        total_carbon = grid_import * self.grid_carbon + boiler_fuel * self.fuel_carbon
        useful_electrical_energy = balance["useful_load_kw"] * hours
        primary_energy = useful_electrical_energy + boiler_fuel * self.fuel_energy
        energy_objective = primary_energy + curtailed
        return {
            "energy": {
                "energy_objective_kwh": round(energy_objective, 6),
                "primary_energy_kwh": round(primary_energy, 6),
                "useful_electrical_energy_kwh": round(useful_electrical_energy, 6),
                "site_consumption_kwh": round(site_demand, 6),
                "grid_import_kwh": round(grid_import, 6),
                "grid_export_kwh": round(grid_export, 6),
                "curtailed_energy_kwh": round(curtailed, 6),
                "boiler_fuel_m3": round(boiler_fuel, 6),
            },
            "cost": {
                "gross_operating_cost_inr": round(gross_cost, 6),
                "export_revenue_inr": round(export_revenue, 6),
                "net_operating_cost_inr": round(gross_cost - export_revenue, 6),
            },
            "carbon": {
                "grid_emissions_kg_co2e": round(grid_import * self.grid_carbon, 6),
                "fuel_emissions_kg_co2e": round(boiler_fuel * self.fuel_carbon, 6),
                "total_emissions_kg_co2e": round(total_carbon, 6),
            },
            "battery": {
                "projected_soc_percent": round(self.constraints.projected_soc(state, problem), 6)
            },
        }

    def score(
        self,
        state: Mapping[str, float],
        problem: OptimizationProblem,
        baseline_metrics: Mapping[str, Mapping[str, float]],
    ) -> tuple[float, dict[str, float]]:
        metrics = self.metrics(state, problem)
        values = {
            "energy": metrics["energy"]["energy_objective_kwh"],
            "cost": metrics["cost"]["net_operating_cost_inr"],
            "carbon": metrics["carbon"]["total_emissions_kg_co2e"],
        }
        denominators = {
            "energy": max(abs(float(baseline_metrics["energy"]["energy_objective_kwh"])), 1.0),
            "cost": max(abs(float(baseline_metrics["cost"]["net_operating_cost_inr"])), 1.0),
            "carbon": max(abs(float(baseline_metrics["carbon"]["total_emissions_kg_co2e"])), 1.0),
        }
        components = {name: values[name] / denominators[name] for name in values}
        weighted = sum(problem.weights[name] * components[name] for name in components)
        violations = self.constraints.violations(state, problem)
        total = weighted + self.constraint_penalty * len(violations)
        return total, {
            "total": round(total, 8),
            "energy_component": round(components["energy"], 8),
            "cost_component": round(components["cost"], 8),
            "carbon_component": round(components["carbon"], 8),
        }
