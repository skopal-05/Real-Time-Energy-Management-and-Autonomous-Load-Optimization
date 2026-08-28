"""Dependency-free state, learning, synchronization, and simulation runtime."""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


def _convert_csv_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    value = value.strip()
    try:
        return float(value)
    except ValueError:
        return value


class StateManager:
    """Validate atomic state updates and retain an audit history."""

    def __init__(self, required_fields: Iterable[str], ranges: dict[str, tuple[float, float]]):
        self.required_fields = tuple(required_fields)
        self.ranges = dict(ranges)
        self._state: dict[str, Any] = {}
        self._history: list[dict[str, Any]] = []

    def update(self, state: dict[str, Any]) -> dict[str, Any]:
        candidate = {key: _convert_csv_value(value) for key, value in state.items()}
        missing = [field for field in self.required_fields if field not in candidate]
        if missing:
            raise ValueError(f"Missing required state fields: {', '.join(missing)}")

        for field, (minimum, maximum) in self.ranges.items():
            if field not in candidate:
                continue
            value = candidate[field]
            if not isinstance(value, (int, float)) or not minimum <= float(value) <= maximum:
                raise ValueError(
                    f"{field} must be between {minimum} and {maximum}; received {value!r}"
                )

        candidate["synchronized_at"] = datetime.now(timezone.utc).isoformat()
        self._state = candidate
        self._history.append(deepcopy(candidate))
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(self._state)

    @property
    def history(self) -> list[dict[str, Any]]:
        return deepcopy(self._history)


class BehaviorLearner:
    """Learn an online linear response from synchronized observations."""

    def __init__(self, features: Iterable[str], target: str, learning_rate: float = 0.01):
        self.features = tuple(features)
        self.target = target
        self.learning_rate = learning_rate
        self.intercept = 0.0
        self.weights = {feature: 0.0 for feature in self.features}
        self.samples_seen = 0

    def predict(self, state: dict[str, Any]) -> float:
        return self.intercept + sum(
            self.weights[field] * float(state[field]) for field in self.features
        )

    def observe(self, state: dict[str, Any]) -> float | None:
        if self.target not in state or any(field not in state for field in self.features):
            return None
        target = float(state[self.target])
        error = target - self.predict(state)
        scale = max(1.0, sum(abs(float(state[field])) for field in self.features))
        step = self.learning_rate / scale
        self.intercept += step * error
        for field in self.features:
            self.weights[field] += step * error * float(state[field]) / scale
        self.samples_seen += 1
        return error

    def parameters(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "features": list(self.features),
            "intercept": self.intercept,
            "weights": dict(self.weights),
            "samples_seen": self.samples_seen,
        }


class RealtimeSynchronizer:
    """Synchronize state dictionaries or CSV telemetry with a digital twin."""

    def __init__(self, update_callback: Callable[[dict[str, Any]], dict[str, Any]]):
        self.update_callback = update_callback
        self.last_source_timestamp: str | None = None

    def sync_state(self, state: dict[str, Any]) -> dict[str, Any]:
        result = self.update_callback(state)
        timestamp = str(state.get("timestamp", ""))
        self.last_source_timestamp = timestamp or self.last_source_timestamp
        return result

    def sync_csv(self, path: str | Path, only_new: bool = False) -> list[dict[str, Any]]:
        updates: list[dict[str, Any]] = []
        with Path(path).open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                timestamp = row.get("timestamp", "")
                if only_new and self.last_source_timestamp and timestamp <= self.last_source_timestamp:
                    continue
                updates.append(self.sync_state(row))
        return updates


class Simulator:
    """Run and optionally save a scenario without changing live twin state."""

    def __init__(self, snapshot: Callable[[], dict[str, Any]], model: Callable[[dict[str, Any]], dict[str, Any]]):
        self.snapshot = snapshot
        self.model = model

    def run(self, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        scenario = self.snapshot()
        if not scenario:
            raise RuntimeError("Synchronize the digital twin before running a simulation")
        scenario.update(overrides or {})
        return self.model(scenario)

    def save(self, result: dict[str, Any], path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return destination


class DigitalTwinBase:
    """Compose the four services required by every Week 2 twin."""

    def __init__(
        self,
        name: str,
        required_fields: Iterable[str],
        ranges: dict[str, tuple[float, float]],
        features: Iterable[str],
        target: str,
    ):
        self.name = name
        self.state_manager = StateManager(required_fields, ranges)
        self.behavior_learner = BehaviorLearner(features, target)
        self.realtime_sync = RealtimeSynchronizer(self.update)
        self.simulation = Simulator(self.state_manager.snapshot, self._simulate)

    def update(self, state: dict[str, Any]) -> dict[str, Any]:
        snapshot = self.state_manager.update(state)
        self.behavior_learner.observe(snapshot)
        return snapshot

    def predict_target(self, scenario: dict[str, Any]) -> float:
        """Anchor learned scenario changes to the latest measured target."""
        live = self.state_manager.snapshot()
        target = self.behavior_learner.target
        baseline = float(live.get(target, scenario.get(target, 0.0)))
        if not live or not self.behavior_learner.samples_seen:
            return baseline
        delta = self.behavior_learner.predict(scenario) - self.behavior_learner.predict(live)
        return baseline + delta

    def _simulate(self, state: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def _result(state: dict[str, Any], **metrics: Any) -> dict[str, Any]:
        return {"input_state": state, "predicted_metrics": metrics}
