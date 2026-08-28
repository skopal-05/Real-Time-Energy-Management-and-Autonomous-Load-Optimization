"""Driver: run Module 5 scenario simulation on the current forecast.

Runs with ``Module 5 - Scenario Simulation`` as the working directory and calls
the module's own ``ScenarioController.run()``. The only thing this driver adds
is the Module 3 -> Module 5 boundary translation described below.

Before running it applies the shared Module 3 boundary translation (see
``enertwin/adapters/boundary.py``). Without it Module 5's
``IntegrationValidator`` rejects the whole forecast whenever the battery is
charging, halting the chain. Module 3's artifact on disk is left exactly as
Module 3 wrote it, and the translation is recorded in this driver's output so it
stays visible.

Usage:
    python m5_scenarios.py <forecast.json> <recommendations.json> \
        <adapted_forecast_out.json> <detail_out.json> [horizon_hours]
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from enertwin.adapters.boundary import adapt_forecast

from integration.scenario_controller import ScenarioController


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: m5_scenarios.py <forecast.json> <recommendations.json> "
            "<adapted_forecast_out.json> <detail_out.json> [horizon_hours]",
            file=sys.stderr,
        )
        return 2

    forecast_path = Path(sys.argv[1])
    recommendations_path = Path(sys.argv[2])
    adapted_path = Path(sys.argv[3])
    detail_path = Path(sys.argv[4])
    horizon_hours = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0

    forecast = json.loads(forecast_path.read_text(encoding="utf-8"))
    adapted, notes = adapt_forecast(forecast)

    adapted_path.parent.mkdir(parents=True, exist_ok=True)
    adapted_path.write_text(
        json.dumps(adapted, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    controller = ScenarioController()
    result = controller.run(
        forecast_path=adapted_path,
        recommendations_path=recommendations_path,
        horizon_hours=horizon_hours,
        save_outputs=True,
    )

    detail = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "module": "Module 5 - Scenario Simulation",
        "horizon_hours": horizon_hours,
        "boundary_translations": notes,
        "source_forecast": str(forecast_path),
        "adapted_forecast": str(adapted_path),
        "result": result,
    }
    detail_path.parent.mkdir(parents=True, exist_ok=True)
    detail_path.write_text(
        json.dumps(detail, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    report = result["report"]
    for note in notes:
        print(f"boundary translation: {note}")
    print(
        f"{report['scenario_count']} scenarios evaluated; "
        f"best = {report['best_scenario_name']} "
        f"({report['best_score']:.2f}/100)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
