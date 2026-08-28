"""Validation rules for actionable Module 6 recommendations."""

from __future__ import annotations

from math import isfinite
from typing import Any, Mapping, Sequence


class RecommendationValidator:
    REQUIRED_FIELDS = {
        "recommendation_id",
        "equipment",
        "action",
        "priority",
        "reason",
        "current_value",
        "recommended_value",
        "unit",
        "expected_impact",
    }
    PRIORITIES = {"low", "medium", "high", "critical"}

    def validate(self, recommendations: Sequence[Mapping[str, Any]]) -> list[str]:
        errors: list[str] = []
        identifiers: set[str] = set()
        if not recommendations:
            errors.append("at least one recommendation is required")
            return errors
        for index, item in enumerate(recommendations):
            label = f"recommendation[{index}]"
            missing = self.REQUIRED_FIELDS - set(item)
            if missing:
                errors.append(f"{label} missing fields: {sorted(missing)}")
                continue
            identifier = str(item["recommendation_id"]).strip()
            if not identifier:
                errors.append(f"{label} recommendation_id must not be empty")
            elif identifier in identifiers:
                errors.append(f"duplicate recommendation_id: {identifier}")
            identifiers.add(identifier)
            if item["priority"] not in self.PRIORITIES:
                errors.append(f"{label} has invalid priority")
            for key in ("current_value", "recommended_value"):
                value = item[key]
                if isinstance(value, bool):
                    errors.append(f"{label} {key} must be numeric")
                else:
                    try:
                        valid = isfinite(float(value))
                    except (TypeError, ValueError):
                        valid = False
                    if not valid:
                        errors.append(f"{label} {key} must be finite")
            if not isinstance(item["expected_impact"], Mapping):
                errors.append(f"{label} expected_impact must be an object")
        return errors

    def require_valid(self, recommendations: Sequence[Mapping[str, Any]]) -> None:
        errors = self.validate(recommendations)
        if errors:
            raise ValueError("invalid recommendations: " + "; ".join(errors))

