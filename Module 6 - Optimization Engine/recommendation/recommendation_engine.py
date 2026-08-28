"""Convert optimized values into validated, actionable recommendations and outputs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from contracts import OptimizationResult
from recommendation.recommendation_validator import RecommendationValidator


VARIABLE_METADATA = {
    "production_load_kw": ("production", "kW"),
    "compressor_power_kw": ("compressor", "kW"),
    "hvac_power_kw": ("hvac", "kW"),
    "battery_charge_kw": ("battery", "kW"),
    "battery_discharge_kw": ("battery", "kW"),
    "grid_export_limit_kw": ("grid", "kW"),
    "boiler_fuel_m3_hr": ("boiler", "m3/hr"),
}


class RecommendationEngine:
    """Explain optimized setpoint changes and persist Person 2 deliverables."""

    def __init__(self, *, change_tolerance: float = 0.01) -> None:
        self.change_tolerance = change_tolerance
        self.validator = RecommendationValidator()

    def generate(self, result: OptimizationResult) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []
        for variable, (equipment, unit) in VARIABLE_METADATA.items():
            current = float(result.baseline_state[variable])
            optimized = float(result.optimized_state[variable])
            change = optimized - current
            if abs(change) <= self.change_tolerance:
                continue
            direction = "increase" if change > 0 else "decrease"
            percent = abs(change) / max(abs(current), 1e-9) * 100
            priority = self._priority(variable, percent)
            recommendations.append(
                {
                    "recommendation_id": f"optimize_{variable}",
                    "equipment": equipment,
                    "action": f"{direction}_{variable}",
                    "priority": priority,
                    "reason": self._reason(variable, direction),
                    "current_value": round(current, 3),
                    "recommended_value": round(optimized, 3),
                    "change_percent": round(percent, 2),
                    "unit": unit,
                    "expected_impact": self._expected_impact(result),
                    "constraints_respected": result.feasible,
                }
            )
        if not recommendations:
            recommendations.append(
                {
                    "recommendation_id": "maintain_optimized_state",
                    "equipment": "plant",
                    "action": "maintain_current_setpoints",
                    "priority": "low",
                    "reason": "The supplied operating state is already optimal within the configured constraints.",
                    "current_value": 1.0,
                    "recommended_value": 1.0,
                    "change_percent": 0.0,
                    "unit": "state",
                    "expected_impact": self._expected_impact(result),
                    "constraints_respected": result.feasible,
                }
            )
        self.validator.require_valid(recommendations)
        return recommendations

    def build_documents(self, result: OptimizationResult) -> dict[str, dict[str, Any]]:
        recommendations = self.generate(result)
        generated_at = datetime.now(timezone.utc).isoformat()
        baseline_cost = result.baseline_metrics["cost"]["net_operating_cost_inr"]
        optimized_cost = result.optimized_metrics["cost"]["net_operating_cost_inr"]
        baseline_carbon = result.baseline_metrics["carbon"]["total_emissions_kg_co2e"]
        optimized_carbon = result.optimized_metrics["carbon"]["total_emissions_kg_co2e"]
        baseline_energy = result.baseline_metrics["energy"]["energy_objective_kwh"]
        optimized_energy = result.optimized_metrics["energy"]["energy_objective_kwh"]
        return {
            "optimized_state": {
                "generated_at": generated_at,
                "status": "feasible" if result.feasible else "infeasible",
                "optimized_state": result.optimized_state,
                "objective": result.objective,
                "algorithm": result.algorithm,
                "violations": list(result.violations),
            },
            "recommendations": {
                "generated_at": generated_at,
                "recommendation_count": len(recommendations),
                "recommendations": recommendations,
            },
            "report": {
                "generated_at": generated_at,
                "summary": {
                    "feasible": result.feasible,
                    "recommendation_count": len(recommendations),
                    "energy_saving_kwh": self._difference(baseline_energy, optimized_energy),
                    "cost_saving_inr": self._difference(baseline_cost, optimized_cost),
                    "emissions_avoided_kg_co2e": self._difference(
                        baseline_carbon, optimized_carbon
                    ),
                },
                "baseline_state": result.baseline_state,
                "optimized_state": result.optimized_state,
                "baseline_metrics": result.baseline_metrics,
                "optimized_metrics": result.optimized_metrics,
                "objective": result.objective,
                "algorithm": result.algorithm,
            },
        }

    def write_outputs(self, result: OptimizationResult, output_root: str | Path) -> dict[str, Path]:
        root = Path(output_root)
        paths = {
            "optimized_state": root / "optimized_states" / "optimized_state.json",
            "recommendations": root / "recommendations" / "recommendations.json",
            "report": root / "reports" / "optimization_report.json",
        }
        documents = self.build_documents(result)
        for name, path in paths.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(documents[name], indent=2), encoding="utf-8")
        return paths

    @staticmethod
    def _priority(variable: str, percent: float) -> str:
        if variable in {"boiler_fuel_m3_hr", "compressor_power_kw"} or percent >= 20:
            return "high"
        if percent >= 5:
            return "medium"
        return "low"

    @staticmethod
    def _reason(variable: str, direction: str) -> str:
        if variable == "compressor_power_kw":
            return (
                "Reduce compressor energy while preserving its required operating target."
                if direction == "decrease"
                else "Increase compressor power only to the feasible value selected by the objective and constraints."
            )
        if variable == "hvac_power_kw":
            return (
                "Use a lower feasible HVAC setpoint while maintaining the temperature requirement."
                if direction == "decrease"
                else "Increase HVAC power only to the feasible value required by the operating constraints."
            )
        reasons = {
            "battery_charge_kw": "Adjust battery charging to improve renewable utilization and operating cost.",
            "battery_discharge_kw": "Adjust battery discharge while preserving the configured SOC reserve.",
            "grid_export_limit_kw": "Use available export capacity before renewable energy is curtailed.",
            "boiler_fuel_m3_hr": "Use the lowest feasible boiler fuel flow that maintains required efficiency.",
            "production_load_kw": "Maintain the required production demand rather than optimizing it away.",
        }
        return reasons.get(variable, f"{direction.title()} this setpoint to improve the objective value.")

    @staticmethod
    def _expected_impact(result: OptimizationResult) -> dict[str, float]:
        return {
            "energy_saving_kwh": RecommendationEngine._difference(
                result.baseline_metrics["energy"]["energy_objective_kwh"],
                result.optimized_metrics["energy"]["energy_objective_kwh"],
            ),
            "cost_saving_inr": RecommendationEngine._difference(
                result.baseline_metrics["cost"]["net_operating_cost_inr"],
                result.optimized_metrics["cost"]["net_operating_cost_inr"],
            ),
            "emissions_avoided_kg_co2e": RecommendationEngine._difference(
                result.baseline_metrics["carbon"]["total_emissions_kg_co2e"],
                result.optimized_metrics["carbon"]["total_emissions_kg_co2e"],
            ),
        }

    @staticmethod
    def _difference(first: float, second: float) -> float:
        value = round(float(first) - float(second), 3)
        return 0.0 if abs(value) < 0.0005 else value
