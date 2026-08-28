"""Equipment health and reliability agent for Module 4."""

from __future__ import annotations

from typing import Any, Mapping

from contracts import AgentRecommendation, number, rounded


class EquipmentHealthAgent:
    """Assess equipment health and recommend maintenance actions."""

    name = "equipment_health_agent"

    def __init__(
        self,
        *,
        warning_health_score: float = 70.0,
        critical_health_score: float = 40.0,
        warning_anomaly_score: float = 0.50,
        critical_anomaly_score: float = 0.80,
    ) -> None:
        if not 0 <= critical_health_score < warning_health_score <= 100:
            raise ValueError(
                "health thresholds must satisfy "
                "0 <= critical < warning <= 100"
            )

        if not 0 <= warning_anomaly_score < critical_anomaly_score:
            raise ValueError(
                "anomaly thresholds must satisfy "
                "0 <= warning < critical"
            )

        self.warning_health_score = float(warning_health_score)
        self.critical_health_score = float(critical_health_score)
        self.warning_anomaly_score = float(warning_anomaly_score)
        self.critical_anomaly_score = float(critical_anomaly_score)

    def assess(self, state: Mapping[str, Any]) -> AgentRecommendation:
        """Assess equipment health using health and anomaly indicators."""

        equipment = str(state.get("equipment", "unknown_equipment")).strip()

        health_score = number(
            state,
            "health_score",
            minimum=0,
            maximum=100,
        )

        anomaly_score = number(
            state,
            "anomaly_score",
            default=0.0,
            minimum=0,
            maximum=1,
        )

        maintenance_due = bool(
            state.get("maintenance_due", False)
        )

        if (
            health_score <= self.critical_health_score
            or anomaly_score >= self.critical_anomaly_score
        ):
            action = "schedule_immediate_maintenance"
            priority = "critical"
            reason = (
                "Equipment health indicators show a critical condition "
                "requiring immediate maintenance attention."
            )

        elif (
            health_score < self.warning_health_score
            or anomaly_score >= self.warning_anomaly_score
            or maintenance_due
        ):
            action = "schedule_preventive_maintenance"
            priority = "high"
            reason = (
                "Equipment health indicators show a warning condition "
                "or maintenance is due."
            )

        else:
            action = "continue_normal_operation"
            priority = "low"
            reason = (
                "Equipment health indicators are within the normal "
                "operating range."
            )

        return AgentRecommendation(
            agent=self.name,
            action=action,
            priority=priority,
            reason=reason,
            setpoints=rounded(
                {
                    "health_score": health_score,
                    "anomaly_score": anomaly_score,
                }
            ),
            expected_impact={
                "health_score_percent": round(health_score, 2),
                "anomaly_score": round(anomaly_score, 2),
            },
            constraints=(
                f"warning_health_score={self.warning_health_score}",
                f"critical_health_score={self.critical_health_score}",
                f"warning_anomaly_score={self.warning_anomaly_score}",
                f"critical_anomaly_score={self.critical_anomaly_score}",
                f"equipment={equipment}",
            ),
        )

    decide = assess