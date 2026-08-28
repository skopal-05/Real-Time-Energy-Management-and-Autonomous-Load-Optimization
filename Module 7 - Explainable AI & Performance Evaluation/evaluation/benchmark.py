"""Baseline-versus-optimized benchmark calculations."""

from __future__ import annotations

from math import isfinite
from typing import Any, Mapping


class Benchmark:
    """Compare matching numeric leaves in baseline and candidate mappings."""

    def compare(
        self,
        baseline: Mapping[str, Any],
        candidate: Mapping[str, Any],
        *,
        higher_is_better: set[str] | None = None,
        tolerance: float = 1e-9,
    ) -> dict[str, Any]:
        baseline_values = self._flatten(baseline)
        candidate_values = self._flatten(candidate)
        common = sorted(set(baseline_values) & set(candidate_values))
        if not common:
            raise ValueError("baseline and candidate have no matching numeric metrics")
        higher = higher_is_better or set()
        comparisons = []
        improved = regressed = unchanged = 0
        for metric in common:
            before = baseline_values[metric]
            after = candidate_values[metric]
            absolute_change = after - before
            relative_change = absolute_change / max(abs(before), 1e-12) * 100
            signed_improvement = absolute_change if metric in higher else -absolute_change
            if signed_improvement > tolerance:
                status = "improved"
                improved += 1
            elif signed_improvement < -tolerance:
                status = "regressed"
                regressed += 1
            else:
                status = "unchanged"
                unchanged += 1
            comparisons.append(
                {
                    "metric": metric,
                    "baseline": round(before, 8),
                    "candidate": round(after, 8),
                    "absolute_change": round(absolute_change, 8),
                    "relative_change_percent": round(relative_change, 4),
                    "direction": "higher_is_better" if metric in higher else "lower_is_better",
                    "status": status,
                }
            )
        return {
            "metric_count": len(comparisons),
            "summary": {"improved": improved, "regressed": regressed, "unchanged": unchanged},
            "comparisons": comparisons,
        }

    def compare_optimization_report(self, report: Mapping[str, Any]) -> dict[str, Any]:
        baseline = report.get("baseline_metrics")
        optimized = report.get("optimized_metrics")
        if not isinstance(baseline, Mapping) or not isinstance(optimized, Mapping):
            raise ValueError("optimization report requires baseline_metrics and optimized_metrics")
        baseline_kpis = {
            "energy": {
                key: baseline.get("energy", {}).get(key)
                for key in (
                    "energy_objective_kwh",
                    "site_consumption_kwh",
                    "grid_import_kwh",
                    "grid_export_kwh",
                    "curtailed_energy_kwh",
                )
            },
            "cost": {
                "net_operating_cost_inr": baseline.get("cost", {}).get(
                    "net_operating_cost_inr"
                )
            },
            "carbon": {
                "total_emissions_kg_co2e": baseline.get("carbon", {}).get(
                    "total_emissions_kg_co2e"
                )
            },
        }
        optimized_kpis = {
            "energy": {
                key: optimized.get("energy", {}).get(key)
                for key in baseline_kpis["energy"]
            },
            "cost": {
                "net_operating_cost_inr": optimized.get("cost", {}).get(
                    "net_operating_cost_inr"
                )
            },
            "carbon": {
                "total_emissions_kg_co2e": optimized.get("carbon", {}).get(
                    "total_emissions_kg_co2e"
                )
            },
        }
        return self.compare(
            baseline_kpis,
            optimized_kpis,
            higher_is_better={
                "energy.grid_export_kwh",
            },
            tolerance=0.001,
        )

    def _flatten(self, data: Mapping[str, Any], prefix: str = "") -> dict[str, float]:
        result: dict[str, float] = {}
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, Mapping):
                result.update(self._flatten(value, path))
            elif isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(float(value)):
                result[path] = float(value)
        return result
