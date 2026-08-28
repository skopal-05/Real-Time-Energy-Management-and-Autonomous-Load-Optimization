"""Validation for monitoring and retraining outputs."""

from __future__ import annotations

from typing import Any, Mapping


class RetrainingValidator:
    def validate_monitoring(self, report: Mapping[str, Any]) -> list[str]:
        errors = []
        required = {"model", "status", "retraining_required", "reasons", "current_metrics"}
        missing = required - set(report)
        if missing:
            errors.append(f"monitoring report missing fields: {sorted(missing)}")
        if report.get("status") not in {"healthy", "degraded"}:
            errors.append("monitoring status must be healthy or degraded")
        if not isinstance(report.get("retraining_required"), bool):
            errors.append("retraining_required must be boolean")
        if report.get("status") == "degraded" and not report.get("reasons"):
            errors.append("degraded monitoring report requires reasons")
        return errors

    def validate_retraining(self, report: Mapping[str, Any]) -> list[str]:
        errors = []
        required = {
            "model",
            "triggered",
            "status",
            "promoted",
            "current_metrics",
            "candidate_metrics",
        }
        missing = required - set(report)
        if missing:
            errors.append(f"retraining report missing fields: {sorted(missing)}")
        if report.get("status") not in {"not_required", "candidate_rejected", "candidate_accepted"}:
            errors.append("invalid retraining status")
        if report.get("promoted") and report.get("status") != "candidate_accepted":
            errors.append("only an accepted candidate may be promoted")
        if report.get("triggered") and not isinstance(report.get("candidate_metrics"), Mapping):
            errors.append("triggered retraining requires candidate_metrics")
        return errors

    @staticmethod
    def require_valid(errors: list[str], label: str) -> None:
        if errors:
            raise ValueError(f"invalid {label}: " + "; ".join(errors))

