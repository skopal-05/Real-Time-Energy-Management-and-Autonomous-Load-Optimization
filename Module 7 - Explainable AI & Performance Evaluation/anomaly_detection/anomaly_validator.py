"""Validation for structured anomaly outputs."""

from __future__ import annotations

from typing import Any, Mapping


class AnomalyValidator:
    def validate(self, output: Mapping[str, Any]) -> list[str]:
        errors = []
        required = {"feature_names", "record_count", "anomaly_count", "records"}
        missing = required - set(output)
        if missing:
            errors.append(f"missing anomaly fields: {sorted(missing)}")
            return errors
        records = output.get("records")
        if not isinstance(records, list):
            errors.append("records must be a list")
            return errors
        if output.get("record_count") != len(records):
            errors.append("record_count does not match records")
        actual_anomalies = sum(bool(item.get("is_anomaly")) for item in records)
        if output.get("anomaly_count") != actual_anomalies:
            errors.append("anomaly_count does not match record labels")
        for index, item in enumerate(records):
            if item.get("label") not in {"normal", "anomaly"}:
                errors.append(f"record[{index}] has invalid label")
            score = item.get("anomaly_score")
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 1:
                errors.append(f"record[{index}] anomaly_score must be in [0, 1]")
        return errors

    def require_valid(self, output: Mapping[str, Any]) -> None:
        errors = self.validate(output)
        if errors:
            raise ValueError("invalid anomaly output: " + "; ".join(errors))

