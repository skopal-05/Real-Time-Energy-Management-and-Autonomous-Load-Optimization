"""Driver: run the Module 4 multi-agent layer on the current Module 3 forecast.

Runs with ``Module 4 - Multi-Agent Intelligence`` as the working directory.
Module 4 ships no ``__main__``; its intended wiring is documented by
``integration/integration_test.py``, and this driver follows exactly that
sequence using the module's own ``AgentController``, ``AgentValidator`` and
``OutputManager``.

Before handing the forecast over it applies the shared Module 3 boundary
translation (see ``enertwin/adapters/boundary.py``). Without it, Module 4's
``CostOptimizationAgent`` and ``EnergyAllocator`` both reject the negative
renewable-generation figure Module 3 emits while the battery is charging, and
two of the twelve agents return ``agent_execution_error`` instead of a decision.

The outputs land in Module 4's own ``outputs/`` folder, which is where Modules 5,
6 and 7 already look for them by default.

Usage:
    python m4_agents.py <forecast_output.json> <adapted_forecast_out.json> \
        <detail_output.json>
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from enertwin.adapters.boundary import adapt_forecast

from integration.agent_controller import AgentController
from integration.agent_validator import AgentValidator
from integration.output_manager import OutputManager


def main() -> int:
    if len(sys.argv) < 4:
        print(
            "usage: m4_agents.py <forecast_output.json> "
            "<adapted_forecast_out.json> <detail_output.json>",
            file=sys.stderr,
        )
        return 2

    forecast_path = Path(sys.argv[1])
    adapted_path = Path(sys.argv[2])
    detail_destination = Path(sys.argv[3])

    forecast_document = json.loads(forecast_path.read_text(encoding="utf-8"))
    adapted, notes = adapt_forecast(forecast_document)
    adapted_path.parent.mkdir(parents=True, exist_ok=True)
    adapted_path.write_text(
        json.dumps(adapted, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    controller = AgentController()
    validator = AgentValidator()
    output_manager = OutputManager()

    registered = controller.registered_agents()
    agent_errors = validator.validate_agents(registered)
    if agent_errors:
        print(f"agent registration invalid: {agent_errors}", file=sys.stderr)
        return 1

    forecast = controller.load_forecast(adapted_path)
    state = controller.build_state(forecast)
    recommendations = controller.generate_recommendations(forecast)
    summary = controller.summarize(recommendations)

    recommendations_path = output_manager.save_recommendations(recommendations)
    optimized_state_path = output_manager.save_optimized_state(state, recommendations)
    report_path = output_manager.save_report(summary, recommendations)

    failed = [
        item.agent
        for item in recommendations
        if item.action == "agent_execution_error"
    ]

    # The deterministic rules the decision engine evaluates alongside the
    # agents. Captured so the UI can show the actual expression that fired
    # rather than a paraphrase.
    rules = [
        {
            "name": rule.name,
            "condition": rule.condition,
            "priority": rule.priority,
            "action": rule.action,
            "reason": rule.reason,
        }
        for rule in controller.decision_engine.rule_engine.rules
    ]

    detail: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "module": "Module 4 - Multi-Agent Intelligence",
        "boundary_translations": notes,
        "registered_agents": registered,
        "rules": rules,
        "failed_agents": failed,
        "agent_state": state,
        "summary": summary,
        "recommendation_count": len(recommendations),
        "recommendations": [item.as_dict() for item in recommendations],
        "output_files": {
            "recommendations": str(recommendations_path),
            "optimized_state": str(optimized_state_path),
            "report": str(report_path),
        },
    }

    detail_destination.parent.mkdir(parents=True, exist_ok=True)
    detail_destination.write_text(
        json.dumps(detail, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    for note in notes:
        print(f"boundary translation: {note}")
    if failed:
        print(f"agents reporting an execution error: {', '.join(failed)}")
    print(
        f"{len(recommendations)} recommendations from {len(registered)} agents "
        f"-> {recommendations_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
