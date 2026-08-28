"""Shared contracts for the Module 6 optimization and recommendation layers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Any, Mapping


DECISION_VARIABLES = (
    "production_load_kw",
    "compressor_power_kw",
    "hvac_power_kw",
    "battery_charge_kw",
    "battery_discharge_kw",
    "grid_export_limit_kw",
    "boiler_fuel_m3_hr",
)


def finite_number(
    data: Mapping[str, Any],
    key: str,
    *,
    default: float | None = None,
    minimum: float | None = None,
) -> float:
    """Read a finite numeric value while rejecting booleans and invalid ranges."""

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
class VariableBound:
    """Inclusive lower and upper bound for an optimization variable."""

    minimum: float
    maximum: float

    def __post_init__(self) -> None:
        if not isfinite(self.minimum) or not isfinite(self.maximum):
            raise ValueError("variable bounds must be finite")
        if self.minimum > self.maximum:
            raise ValueError("minimum bound cannot exceed maximum bound")

    def clamp(self, value: float) -> float:
        return max(self.minimum, min(self.maximum, float(value)))


@dataclass(frozen=True)
class OptimizationProblem:
    """Validated inputs needed by the optimization algorithm."""

    baseline_state: dict[str, float]
    bounds: dict[str, VariableBound]
    horizon_hours: float = 1.0
    state_of_charge_percent: float = 50.0
    battery_capacity_kwh: float = 100.0
    minimum_soc_percent: float = 20.0
    maximum_soc_percent: float = 90.0
    battery_efficiency: float = 0.95
    grid_import_limit_kw: float = 500.0
    weights: dict[str, float] = field(
        default_factory=lambda: {"energy": 0.35, "cost": 0.35, "carbon": 0.30}
    )


@dataclass(frozen=True)
class OptimizationResult:
    """Serializable result produced by the optimizer."""

    baseline_state: dict[str, float]
    optimized_state: dict[str, float]
    baseline_metrics: dict[str, dict[str, float]]
    optimized_metrics: dict[str, dict[str, float]]
    objective: dict[str, float]
    feasible: bool
    violations: tuple[str, ...]
    algorithm: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["violations"] = list(self.violations)
        return result

