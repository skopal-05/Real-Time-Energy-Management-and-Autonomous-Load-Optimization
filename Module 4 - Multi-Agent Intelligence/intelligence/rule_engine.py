"""Rule-based decision engine for Module 4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from contracts import AgentRecommendation


@dataclass(frozen=True)
class Rule:
    """A single condition-action rule."""

    name: str
    condition: str
    priority: str
    action: str
    reason: str


class RuleEngine:
    """Apply deterministic safety and energy-management rules."""

    name = "rule_engine"

    def __init__(self) -> None:
        self.rules = (
            Rule(
                name="critical_unserved_load",
                condition="unserved_load_kw > 0",
                priority="critical",
                action="reduce_non_critical_load",
                reason="Unserved load requires immediate load reduction.",
            ),
            Rule(
                name="equipment_health_critical",
                condition="health_score < 40 or anomaly_score >= 0.80",
                priority="critical",
                action="protect_equipment",
                reason="Equipment health indicators show a critical condition.",
            ),
            Rule(
                name="high_grid_tariff",
                condition="tariff_inr_kwh >= 8",
                priority="high",
                action="optimize_grid_usage",
                reason="High grid tariff requires energy-cost optimization.",
            ),
            Rule(
                name="renewable_surplus",
                condition="renewable_surplus_kw > 0",
                priority="medium",
                action="use_renewable_surplus",
                reason="Renewable surplus should be utilized before curtailment.",
            ),
        )

    def evaluate(
        self,
        state: Mapping[str, Any],
    ) -> list[AgentRecommendation]:
        """Evaluate all applicable rules against the current state."""

        recommendations: list[AgentRecommendation] = []

        unserved_load = self._number(
            state,
            "unserved_load_kw",
            default=0,
        )

        health_score = self._number(
            state,
            "health_score",
            default=100,
        )

        anomaly_score = self._number(
            state,
            "anomaly_score",
            default=0,
        )

        tariff = self._number(
            state,
            "tariff_inr_kwh",
            default=0,
        )

        renewable_surplus = self._number(
            state,
            "renewable_surplus_kw",
            default=0,
        )

        # Rule 1: critical unserved load
        if unserved_load > 0:
            recommendations.append(
                self._recommendation(
                    self.rules[0],
                    {
                        "unserved_load_kw": round(unserved_load, 2),
                    },
                )
            )

        # Rule 2: critical equipment health
        if health_score < 40 or anomaly_score >= 0.80:
            recommendations.append(
                self._recommendation(
                    self.rules[1],
                    {
                        "health_score": round(health_score, 2),
                        "anomaly_score": round(anomaly_score, 2),
                    },
                )
            )

        # Rule 3: high grid tariff
        if tariff >= 8:
            recommendations.append(
                self._recommendation(
                    self.rules[2],
                    {
                        "tariff_inr_kwh": round(tariff, 2),
                    },
                )
            )

        # Rule 4: renewable surplus
        if renewable_surplus > 0:
            recommendations.append(
                self._recommendation(
                    self.rules[3],
                    {
                        "renewable_surplus_kw": round(renewable_surplus, 2),
                    },
                )
            )

        return recommendations

    def _recommendation(
        self,
        rule: Rule,
        setpoints: dict[str, Any],
    ) -> AgentRecommendation:
        """Convert a rule match into a standard recommendation."""

        return AgentRecommendation(
            agent=self.name,
            action=rule.action,
            priority=rule.priority,
            reason=rule.reason,
            setpoints=setpoints,
            expected_impact={},
            constraints=(
                f"rule={rule.name}",
                f"condition={rule.condition}",
            ),
        )

    @staticmethod
    def _number(
        state: Mapping[str, Any],
        key: str,
        *,
        default: float,
    ) -> float:
        """Safely read a numeric rule input."""

        value = state.get(key, default)

        if isinstance(value, bool):
            return default

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def decide(
        self,
        state: Mapping[str, Any],
    ) -> list[AgentRecommendation]:
        """Alias for evaluate()."""

        return self.evaluate(state)