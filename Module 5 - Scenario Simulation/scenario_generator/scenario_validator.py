"""Validation for generated scenario objects."""

from __future__ import annotations

from math import isfinite

from contracts import Scenario


class ScenarioValidator:
    """Validate scenario identity, horizon, and operating values."""

    REQUIRED_VALUES = {
        "production_load_kw",
        "compressor_power_kw",
        "hvac_power_kw",
        "renewable_generation_kw",
        "battery_charge_kw",
        "battery_discharge_kw",
        "grid_export_limit_kw",
        "boiler_fuel_m3_hr",
    }

    def validate(self, scenario: Scenario) -> list[str]:
        errors: list[str] = []
        if not scenario.scenario_id.strip():
            errors.append("scenario_id must not be empty")
        if scenario.horizon_hours <= 0 or not isfinite(scenario.horizon_hours):
            errors.append("horizon_hours must be finite and greater than zero")
        missing = sorted(self.REQUIRED_VALUES - scenario.operating_point.keys())
        if missing:
            errors.append(f"missing operating values: {', '.join(missing)}")
        for key, value in scenario.operating_point.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                errors.append(f"{key} must be numeric")
            elif not isfinite(float(value)) or value < 0:
                errors.append(f"{key} must be finite and non-negative")
        if (
            scenario.operating_point.get("battery_charge_kw", 0) > 0
            and scenario.operating_point.get("battery_discharge_kw", 0) > 0
        ):
            errors.append("battery cannot charge and discharge simultaneously")
        return errors

    def require_valid(self, scenario: Scenario) -> None:
        errors = self.validate(scenario)
        if errors:
            raise ValueError("invalid scenario: " + "; ".join(errors))
