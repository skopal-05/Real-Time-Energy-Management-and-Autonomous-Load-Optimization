"""Priority management for Module 4 agent recommendations."""

from __future__ import annotations

from collections.abc import Iterable

from contracts import AgentRecommendation


class PriorityManager:
    """Rank and select agent recommendations by priority."""

    name = "priority_manager"

    PRIORITY_ORDER = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    def sort(
        self,
        recommendations: Iterable[AgentRecommendation],
    ) -> list[AgentRecommendation]:
        """Return recommendations from highest to lowest priority."""

        items = list(recommendations)

        for recommendation in items:
            if not isinstance(recommendation, AgentRecommendation):
                raise TypeError(
                    "all items must be AgentRecommendation instances"
                )

        return sorted(
            items,
            key=lambda recommendation: self.PRIORITY_ORDER[
                recommendation.priority
            ],
            reverse=True,
        )

    def highest(
        self,
        recommendations: Iterable[AgentRecommendation],
    ) -> AgentRecommendation | None:
        """Return the highest-priority recommendation."""

        ordered = self.sort(recommendations)
        return ordered[0] if ordered else None

    def filter_by_priority(
        self,
        recommendations: Iterable[AgentRecommendation],
        priority: str,
    ) -> list[AgentRecommendation]:
        """Return recommendations matching a specific priority."""

        if priority not in self.PRIORITY_ORDER:
            raise ValueError(
                f"priority must be one of {list(self.PRIORITY_ORDER)}"
            )

        return [
            recommendation
            for recommendation in recommendations
            if recommendation.priority == priority
        ]

    def has_critical(
        self,
        recommendations: Iterable[AgentRecommendation],
    ) -> bool:
        """Check whether any critical recommendation exists."""

        return any(
            recommendation.priority == "critical"
            for recommendation in recommendations
        )

    def prioritize(
        self,
        recommendations: Iterable[AgentRecommendation],
    ) -> list[AgentRecommendation]:
        """Alias for sort()."""

        return self.sort(recommendations)