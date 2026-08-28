"""Multi-objective scenario ranking."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Mapping

from contracts import ScenarioResult


class ScenarioRanker:
    """Rank scenarios using normalized lower-is-better objective values."""

    DEFAULT_WEIGHTS = {"energy": 0.35, "cost": 0.35, "carbon": 0.30}

    def __init__(self, weights: Mapping[str, float] | None = None) -> None:
        selected = dict(weights or self.DEFAULT_WEIGHTS)
        if set(selected) != {"energy", "cost", "carbon"}:
            raise ValueError("weights must contain energy, cost, and carbon")
        if any(value < 0 for value in selected.values()) or sum(selected.values()) <= 0:
            raise ValueError("weights must be non-negative with a positive sum")
        total = sum(selected.values())
        self.weights = {key: value / total for key, value in selected.items()}

    @staticmethod
    def _score(value: float, values: list[float]) -> float:
        low, high = min(values), max(values)
        if high == low:
            return 100.0
        return 100.0 * (high - value) / (high - low)

    def rank(self, results: Iterable[ScenarioResult]) -> list[ScenarioResult]:
        items = list(results)
        if not items:
            raise ValueError("at least one evaluated scenario is required")
        energy_values = [item.energy["useful_electrical_load_kwh"] for item in items]
        cost_values = [item.cost["net_operating_cost_inr"] for item in items]
        carbon_values = [item.carbon["total_emissions_kg_co2e"] for item in items]
        scored: list[ScenarioResult] = []
        for item in items:
            components = {
                "energy": round(
                    self._score(item.energy["useful_electrical_load_kwh"], energy_values),
                    2,
                ),
                "cost": round(self._score(item.cost["net_operating_cost_inr"], cost_values), 2),
                "carbon": round(
                    self._score(item.carbon["total_emissions_kg_co2e"], carbon_values), 2
                ),
            }
            total = sum(components[key] * self.weights[key] for key in self.weights)
            scored.append(replace(item, score=round(total, 2), component_scores=components))
        scored.sort(
            key=lambda item: (
                -item.score,
                item.cost["net_operating_cost_inr"],
                item.scenario.scenario_id,
            )
        )
        return [replace(item, rank=index) for index, item in enumerate(scored, 1)]
