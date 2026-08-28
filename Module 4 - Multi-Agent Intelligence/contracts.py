"""Shared contracts and validation helpers for Week 4 Person 1 and 2 agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Any, Mapping


PRIORITIES = {"low", "medium", "high", "critical"}


@dataclass(frozen=True)
class AgentRecommendation:
    """Serializable recommendation returned by every energy agent."""

    agent: str
    action: str
    priority: str
    reason: str
    setpoints: dict[str, Any] = field(default_factory=dict)
    expected_impact: dict[str, float] = field(default_factory=dict)
    constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.agent.strip():
            raise ValueError("agent must not be empty")
        if not self.action.strip():
            raise ValueError("action must not be empty")
        if self.priority not in PRIORITIES:
            raise ValueError(f"priority must be one of {sorted(PRIORITIES)}")

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        result = asdict(self)
        result["constraints"] = list(self.constraints)
        return result


def number(
    data: Mapping[str, Any],
    key: str,
    *,
    default: float | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    """Read and validate a finite numeric input."""

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
    if maximum is not None and value > maximum:
        raise ValueError(f"{key} must be at most {maximum}")
    return value


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a value to an inclusive interval."""

    return max(minimum, min(maximum, value))


def rounded(values: Mapping[str, float], digits: int = 2) -> dict[str, float]:
    """Round numeric output values consistently."""

    return {key: round(float(value), digits) for key, value in values.items()}
