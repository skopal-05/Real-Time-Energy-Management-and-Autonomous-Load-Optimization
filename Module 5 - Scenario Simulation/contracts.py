"""Shared data contracts for Module 5 scenario simulation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Any, Mapping


def finite_number(
    data: Mapping[str, Any],
    key: str,
    *,
    default: float | None = None,
    minimum: float | None = None,
) -> float:
    """Read a finite numeric value from a mapping."""

    if key not in data:
        if default is None:
            raise ValueError(f"missing required value: {key}")
        value = default
    else:
        raw = data[key]
        if isinstance(raw, bool):
            raise ValueError(f"{key} must be numeric")
        try:
            value = float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be numeric") from exc
    if not isfinite(value):
        raise ValueError(f"{key} must be finite")
    if minimum is not None and value < minimum:
        raise ValueError(f"{key} must be at least {minimum}")
    return value


@dataclass(frozen=True)
class Scenario:
    """A validated operating scenario before metric simulation."""

    scenario_id: str
    name: str
    description: str
    horizon_hours: float
    operating_point: dict[str, float]
    applied_recommendations: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["applied_recommendations"] = list(self.applied_recommendations)
        result["assumptions"] = list(self.assumptions)
        return result


@dataclass(frozen=True)
class ScenarioResult:
    """A scenario enriched with comparable simulation metrics."""

    scenario: Scenario
    energy: dict[str, float]
    cost: dict[str, float]
    carbon: dict[str, float]
    score: float = 0.0
    rank: int = 0
    component_scores: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.scenario.as_dict(),
            "metrics": {
                "energy": self.energy,
                "cost": self.cost,
                "carbon": self.carbon,
            },
            "ranking": {
                "score": self.score,
                "rank": self.rank,
                "component_scores": self.component_scores,
            },
        }
