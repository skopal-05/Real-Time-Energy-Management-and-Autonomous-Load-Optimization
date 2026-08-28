"""Driver: run Module 3 against live Module 2 twin state.

Runs with ``Module 3 - Forecasting`` as the working directory and uses the
module's own public classes: ``FutureStateGenerator`` (its per-asset forecast
methods) and ``LoadForecast``. No Module 3 file is read for anything other than
import, and none is modified.

Why the per-asset methods rather than ``FutureStateGenerator.generate()``
------------------------------------------------------------------------
``generate()`` hands one flat state dictionary to all seven models, which is how
``integration/run_forecasting.py`` demonstrates the module with a hand-written
example. Real plant telemetry cannot be flattened that way: ``motor_temperature_c``
belongs to both the production line and the compressor, ``efficiency_percent`` to
the boiler, compressor and HVAC, ``voltage_v`` to both the battery and the grid.
Flattening would silently feed one asset's sensor reading to another asset's
model.

So this driver calls the same public methods ``generate()`` calls -
``production_forecast()``, ``boiler_forecast()``, and so on - once per asset,
each with that asset's own twin state. The merged result is byte-compatible with
what ``generate()`` returns, because every model's ``postprocess`` emits a single
uniquely-named key.

Usage:
    python m3_forecast.py <twin_export.json> <series_output.json>
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from integration.future_state_generator import FutureStateGenerator
from integration.load_forecast import LoadForecast

#: Where Module 3 writes its own artifact, relative to the module root.
#: Identical to ``integration/run_forecasting.py``.
FORECAST_OUTPUT = Path("outputs") / "forecast_output.json"

#: Twin asset -> (forecast method name, key the model emits, measured field to
#: compare that prediction against). The measured field is the model's training
#: target as declared in ``common/config.py``.
ASSET_MODELS: dict[str, tuple[str, str, str]] = {
    "production_line_a": ("production_forecast", "units_per_hour", "units_per_hour"),
    "production_line_b": ("production_forecast", "units_per_hour", "units_per_hour"),
    "boiler": ("boiler_forecast", "fuel_flow_m3_hr", "fuel_flow_m3_hr"),
    "compressor": ("compressor_forecast", "compressor_power_kw", "power_kw"),
    "hvac": ("hvac_forecast", "hvac_power_kw", "power_kw"),
    "battery": ("battery_forecast", "battery_power_kw", "battery_power_kw"),
    "grid": ("grid_forecast", "grid_import_kw", "grid_import_kw"),
    "solar": ("solar_forecast", "inverter_power_kw", "inverter_power_kw"),
}

#: Assets whose forecast lands directly in the canonical ``future_state``.
#: Production is handled separately because the site has two lines and Module 3
#: emits a single ``units_per_hour`` key.
CANONICAL_ASSETS = ("boiler", "compressor", "hvac", "battery", "grid", "solar")


def _method(generator: FutureStateGenerator, name: str) -> Callable[..., dict[str, Any]]:
    return getattr(generator, name)


def _forecast_step(
    generator: FutureStateGenerator, states: dict[str, Any]
) -> dict[str, Any]:
    """Forecast one synchronized moment across every asset."""

    per_asset: dict[str, dict[str, Any]] = {}
    for asset, (method_name, _emitted, _measured) in ASSET_MODELS.items():
        state = states.get(asset)
        if not isinstance(state, dict):
            continue
        per_asset[asset] = _method(generator, method_name)(state)

    future_state: dict[str, Any] = {}

    line_a = per_asset.get("production_line_a", {}).get("units_per_hour", 0.0)
    line_b = per_asset.get("production_line_b", {}).get("units_per_hour", 0.0)
    future_state["units_per_hour"] = round(float(line_a) + float(line_b), 2)
    future_state["production_line_a_units_per_hour"] = line_a
    future_state["production_line_b_units_per_hour"] = line_b

    for asset in CANONICAL_ASSETS:
        future_state.update(per_asset.get(asset, {}))

    return {"future_state": future_state, "per_asset": per_asset}


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "usage: m3_forecast.py <twin_export.json> <series_output.json>",
            file=sys.stderr,
        )
        return 2

    twin_export = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    series_destination = Path(sys.argv[2])

    history: list[dict[str, Any]] = twin_export.get("history", [])
    if not history:
        print("twin export contains no history", file=sys.stderr)
        return 1

    generator = FutureStateGenerator()
    load_forecast = LoadForecast()

    steps: list[dict[str, Any]] = []
    for states in history:
        step = _forecast_step(generator, states)
        future_state = step["future_state"]
        steps.append(
            {
                "timestamp": _timestamp_of(states),
                "future_state": future_state,
                "energy_forecast": load_forecast.forecast(future_state),
                "measured": _measured_values(states),
                "predicted": _predicted_values(step["per_asset"]),
            }
        )

    # The final step is the canonical current forecast. Written exactly where
    # Module 3 writes it, in the same shape integration/run_forecasting.py uses,
    # so Modules 4-7 pick it up through their existing default paths.
    latest = steps[-1]
    forecast_document = {
        "future_state": latest["future_state"],
        "energy_forecast": latest["energy_forecast"],
    }
    FORECAST_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    FORECAST_OUTPUT.write_text(
        json.dumps(forecast_document, indent=4), encoding="utf-8"
    )

    series_document = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "module": "Module 3 - Forecasting",
        "algorithm": "RandomForestRegressor",
        "step_count": len(steps),
        "models": {
            asset: {"emits": emitted, "measures": measured}
            for asset, (_method_name, emitted, measured) in ASSET_MODELS.items()
        },
        "steps": steps,
        "latest": forecast_document,
    }
    series_destination.parent.mkdir(parents=True, exist_ok=True)
    series_destination.write_text(
        json.dumps(series_document, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(
        f"forecast generated for {len(steps)} steps -> "
        f"{FORECAST_OUTPUT} and {series_destination}"
    )
    return 0


def _timestamp_of(states: dict[str, Any]) -> str | None:
    for state in states.values():
        if isinstance(state, dict) and state.get("timestamp"):
            return str(state["timestamp"])
    return None


def _measured_values(states: dict[str, Any]) -> dict[str, float | None]:
    measured: dict[str, float | None] = {}
    for asset, (_method_name, _emitted, field) in ASSET_MODELS.items():
        state = states.get(asset)
        value = state.get(field) if isinstance(state, dict) else None
        try:
            measured[asset] = float(value) if value is not None else None
        except (TypeError, ValueError):
            measured[asset] = None
    return measured


def _predicted_values(per_asset: dict[str, dict[str, Any]]) -> dict[str, float | None]:
    predicted: dict[str, float | None] = {}
    for asset, (_method_name, emitted, _measured) in ASSET_MODELS.items():
        value = per_asset.get(asset, {}).get(emitted)
        try:
            predicted[asset] = float(value) if value is not None else None
        except (TypeError, ValueError):
            predicted[asset] = None
    return predicted


if __name__ == "__main__":
    raise SystemExit(main())
