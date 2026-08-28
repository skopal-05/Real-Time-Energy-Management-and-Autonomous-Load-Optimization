"""Interface translations applied at module boundaries.

Kept in one place so every consumer of a module's artifact sees the same
translation, and so the complete list of places where the platform reshapes data
between modules is short enough to audit.

Nothing here edits a module or its artifacts on disk. A translation produces a
*view* of an artifact for one downstream consumer, and always records what it
changed and why.
"""

from __future__ import annotations

import json
from typing import Any


def adapt_forecast(forecast: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Translate a Module 3 forecast for its downstream consumers.

    The renewable-generation disagreement
    -------------------------------------
    Module 3's ``LoadForecast.renewable_generation()`` defines renewable
    generation as *solar + battery power*. Module 1 signs battery power positive
    while charging, so on any charging interval Module 3 emits a negative
    ``energy_forecast.renewable_generation_kw``.

    Both downstream consumers reject that:

    * Module 4's ``CostOptimizationAgent`` and ``EnergyAllocator`` require
      ``renewable_generation_kw`` / ``renewable_available_kw`` to be at least 0,
      and return an ``agent_execution_error`` recommendation otherwise - so two
      of the twelve agents go dark.
    * Module 5's ``IntegrationValidator`` requires the same field to be
      non-negative and rejects the entire forecast, halting the chain.

    Module 5 states the definition it means. Its ``ScenarioGenerator`` reads
    renewable generation from ``future_state.inverter_power_kw`` and comments:
    "Battery power is simulated separately and therefore must not be counted as
    renewable generation."

    So the translated view carries the solar-only figure - Module 3's own
    ``inverter_power_kw``. No value is invented, and Module 3's artifact on disk
    is left exactly as Module 3 wrote it.
    """

    adapted = json.loads(json.dumps(forecast))  # deep copy, JSON-safe
    notes: list[str] = []

    future_state = adapted.get("future_state")
    energy_forecast = adapted.get("energy_forecast")
    if not isinstance(future_state, dict) or not isinstance(energy_forecast, dict):
        return adapted, notes

    reported = energy_forecast.get("renewable_generation_kw")
    try:
        reported_value = float(reported)
    except (TypeError, ValueError):
        return adapted, notes

    if reported_value < 0:
        solar_only = float(future_state.get("inverter_power_kw", 0.0) or 0.0)
        solar_only = max(0.0, round(solar_only, 2))
        energy_forecast["renewable_generation_kw"] = solar_only
        notes.append(
            "energy_forecast.renewable_generation_kw translated from "
            f"{reported_value} (Module 3: solar + battery, negative while the "
            f"battery charges) to {solar_only} (solar only, from Module 3's own "
            "future_state.inverter_power_kw) because Modules 4 and 5 both "
            "require a non-negative value"
        )

    return adapted, notes


__all__ = ["adapt_forecast"]
