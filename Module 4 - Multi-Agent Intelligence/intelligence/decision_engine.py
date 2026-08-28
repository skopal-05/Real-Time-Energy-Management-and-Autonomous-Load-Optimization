"""Decision engine for coordinating Module 4 energy agents."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from contracts import AgentRecommendation
from intelligence.communication_manager import CommunicationManager
from intelligence.priority_manager import PriorityManager
from intelligence.rule_engine import RuleEngine


AgentCallable = Callable[[Mapping[str, Any]], AgentRecommendation]


class DecisionEngine:
    """Coordinate agent recommendations and generate prioritized decisions."""

    name = "decision_engine"

    def __init__(
        self,
        *,
        rule_engine: RuleEngine | None = None,
        priority_manager: PriorityManager | None = None,
        communication_manager: CommunicationManager | None = None,
    ) -> None:
        self.rule_engine = rule_engine or RuleEngine()
        self.priority_manager = priority_manager or PriorityManager()
        self.communication_manager = (
            communication_manager or CommunicationManager()
        )

        self._agents: dict[str, AgentCallable] = {}

    def register_agent(
        self,
        name: str,
        agent: AgentCallable,
    ) -> None:
        """Register an agent decision function."""

        if not name.strip():
            raise ValueError("agent name must not be empty")

        if not callable(agent):
            raise TypeError("agent must be callable")

        self._agents[name] = agent

    def register_agents(
        self,
        agents: Mapping[str, AgentCallable],
    ) -> None:
        """Register multiple agents."""

        for name, agent in agents.items():
            self.register_agent(name, agent)

    def run_agents(
        self,
        state: Mapping[str, Any],
    ) -> list[AgentRecommendation]:
        """Run all registered agents against the current state."""

        recommendations: list[AgentRecommendation] = []

        for name, agent in self._agents.items():
            try:
                recommendation = agent(state)
            except Exception as exc:
                # One failed agent should not stop the complete
                # multi-agent decision process.
                recommendation = AgentRecommendation(
                    agent=name,
                    action="agent_execution_error",
                    priority="high",
                    reason=f"Agent execution failed: {exc}",
                    constraints=("agent execution error",),
                )

            if not isinstance(recommendation, AgentRecommendation):
                raise TypeError(
                    f"Agent '{name}' must return AgentRecommendation"
                )

            recommendations.append(recommendation)

        return recommendations

    def evaluate_rules(
        self,
        state: Mapping[str, Any],
    ) -> list[AgentRecommendation]:
        """Evaluate deterministic system-level rules."""

        return self.rule_engine.evaluate(state)

    def decide(
        self,
        state: Mapping[str, Any],
        *,
        include_rules: bool = True,
    ) -> list[AgentRecommendation]:
        """Generate and prioritize all available recommendations."""

        recommendations = self.run_agents(state)

        if include_rules:
            recommendations.extend(
                self.evaluate_rules(state)
            )

        # Send recommendations through the communication layer.
        self.communication_manager.clear()
        self.communication_manager.publish_many(recommendations)

        # Critical/high-priority recommendations appear first.
        return self.priority_manager.sort(recommendations)

    def highest_priority(
        self,
        state: Mapping[str, Any],
        *,
        include_rules: bool = True,
    ) -> AgentRecommendation | None:
        """Return the highest-priority decision."""

        recommendations = self.decide(
            state,
            include_rules=include_rules,
        )

        return self.priority_manager.highest(recommendations)

    def summarize(
        self,
        recommendations: Iterable[AgentRecommendation],
    ) -> dict[str, Any]:
        """Create a compact summary of agent decisions."""

        items = list(recommendations)

        priority_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for recommendation in items:
            priority_counts[recommendation.priority] += 1

        highest = self.priority_manager.highest(items)

        return {
            "total_recommendations": len(items),
            "priority_counts": priority_counts,
            "highest_priority": (
                highest.priority if highest else None
            ),
            "highest_priority_agent": (
                highest.agent if highest else None
            ),
            "highest_priority_action": (
                highest.action if highest else None
            ),
        }

    def get_communication_manager(self) -> CommunicationManager:
        """Return the communication manager."""

        return self.communication_manager

    def get_registered_agents(self) -> list[str]:
        """Return the names of all registered agents."""

        return list(self._agents.keys())