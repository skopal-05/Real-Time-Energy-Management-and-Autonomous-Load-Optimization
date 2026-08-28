"""High-level anomaly detector for structured industrial operating records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from anomaly_detection.anomaly_validator import AnomalyValidator
from anomaly_detection.isolation_forest import IsolationForestModel


class AnomalyDetector:
    def __init__(self, model: IsolationForestModel | None = None) -> None:
        self.model = model or IsolationForestModel()
        self.validator = AnomalyValidator()
        self.feature_names: tuple[str, ...] = ()

    def fit(
        self, records: Sequence[Mapping[str, Any]], feature_names: Sequence[str]
    ) -> "AnomalyDetector":
        self.feature_names = tuple(str(name) for name in feature_names)
        self.model.fit(self._matrix(records))
        return self

    def detect(self, records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        matrix = self._matrix(records)
        scored = self.model.score(matrix)
        output_records = []
        for record, score in zip(records, scored):
            output_records.append(
                {
                    **score,
                    "values": {
                        name: round(float(record[name]), 8) for name in self.feature_names
                    },
                }
            )
        output = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "method": "isolation_forest",
            "feature_names": list(self.feature_names),
            "record_count": len(output_records),
            "anomaly_count": sum(item["is_anomaly"] for item in output_records),
            "records": output_records,
        }
        self.validator.require_valid(output)
        return output

    def _matrix(self, records: Sequence[Mapping[str, Any]]) -> list[list[float]]:
        if not self.feature_names:
            raise ValueError("feature_names must be configured before detecting anomalies")
        matrix = []
        for row_index, record in enumerate(records):
            values = []
            for name in self.feature_names:
                if name not in record:
                    raise ValueError(f"record[{row_index}] missing feature: {name}")
                raw = record[name]
                if isinstance(raw, bool):
                    raise ValueError(f"record[{row_index}] {name} must be numeric")
                try:
                    values.append(float(raw))
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"record[{row_index}] {name} must be numeric") from exc
            matrix.append(values)
        return matrix

