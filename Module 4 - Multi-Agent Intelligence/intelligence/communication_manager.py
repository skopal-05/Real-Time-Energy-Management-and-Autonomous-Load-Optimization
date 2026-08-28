"""Agent communication manager for Module 4."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from contracts import AgentRecommendation


class CommunicationManager:
    """Collect, route, and summarize recommendations between agents."""

    name = "communication_manager"

    def __init__(self) -> None:
        self._messages: list[AgentRecommendation] = []

    def publish(self, recommendation: AgentRecommendation) -> None:
        """Publish one agent recommendation."""

        if not isinstance(recommendation, AgentRecommendation):
            raise TypeError(
                "recommendation must be an AgentRecommendation"
            )

        self._messages.append(recommendation)

    def publish_many(
        self,
        recommendations: Iterable[AgentRecommendation],
    ) -> None:
        """Publish multiple agent recommendations."""

        for recommendation in recommendations:
            self.publish(recommendation)

    def get_messages(self) -> list[AgentRecommendation]:
        """Return all published recommendations."""

        return list(self._messages)

    def get_by_agent(
        self,
        agent_name: str,
    ) -> list[AgentRecommendation]:
        """Return recommendations produced by a specific agent."""

        return [
            recommendation
            for recommendation in self._messages
            if recommendation.agent == agent_name
        ]

    def get_by_priority(
        self,
        priority: str,
    ) -> list[AgentRecommendation]:
        """Return recommendations with a specific priority."""

        return [
            recommendation
            for recommendation in self._messages
            if recommendation.priority == priority
        ]

    def group_by_agent(
        self,
    ) -> dict[str, list[AgentRecommendation]]:
        """Group all recommendations by their originating agent."""

        grouped: dict[str, list[AgentRecommendation]] = defaultdict(list)

        for recommendation in self._messages:
            grouped[recommendation.agent].append(recommendation)

        return dict(grouped)

    def group_by_priority(
        self,
    ) -> dict[str, list[AgentRecommendation]]:
        """Group recommendations by priority."""

        grouped: dict[str, list[AgentRecommendation]] = defaultdict(list)

        for recommendation in self._messages:
            grouped[recommendation.priority].append(recommendation)

        return dict(grouped)

    def latest(self) -> AgentRecommendation | None:
        """Return the most recently published recommendation."""

        if not self._messages:
            return None

        return self._messages[-1]

    def clear(self) -> None:
        """Clear the communication buffer."""

        self._messages.clear()

    def count(self) -> int:
        """Return the number of published recommendations."""

        return len(self._messages)