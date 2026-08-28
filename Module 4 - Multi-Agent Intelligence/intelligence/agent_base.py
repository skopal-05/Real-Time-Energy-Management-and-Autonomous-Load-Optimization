"""Base interface for Module 4 energy intelligence agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from contracts import AgentRecommendation


class BaseAgent(ABC):
    """Common interface for all Module 4 agents."""

    name: str = "base_agent"

    @abstractmethod
    def decide(self, state: Mapping[str, Any]) -> AgentRecommendation:
        """Generate a recommendation from the current system state."""
        raise NotImplementedError

    def validate_state(self, state: Mapping[str, Any]) -> None:
        """Validate the basic agent input."""

        if not isinstance(state, Mapping):
            raise TypeError("state must be a mapping")

    def run(self, state: Mapping[str, Any]) -> AgentRecommendation:
        """Validate input and execute the agent decision."""

        self.validate_state(state)
        recommendation = self.decide(state)

        if not isinstance(recommendation, AgentRecommendation):
            raise TypeError(
                f"{self.name} must return an AgentRecommendation"
            )

        return recommendation