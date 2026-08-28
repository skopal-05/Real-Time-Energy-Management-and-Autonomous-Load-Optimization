"""Driver: advance the Module 2 digital twins and export their state.

Runs with ``Module 2 - Digital Twin`` as the working directory, so it imports
the module exactly the way ``run_realtime.py`` does. It uses only the module's
public surface - the eight ``*DigitalTwin`` classes, ``CSVLoader``,
``SystemSync``, ``state_manager``, ``behavior_learner`` and ``simulation`` - and
modifies nothing inside the module.

Two things ``run_realtime.py`` does that a request-driven backend cannot
------------------------------------------------------------------------
1. It loops forever. This driver performs a bounded number of the same
   ``sync_once()`` steps instead.

2. It lets a single rejected sensor reading terminate the process. The twins
   validate every reading against their declared operating ranges and raise on
   anything outside them - correct behaviour, and this driver does not weaken
   it. Instead it catches the rejection per asset, keeps that twin's last valid
   state, records a data-quality event, and carries on. The platform surfaces
   those events rather than crashing on them.

Which Module 1 dataset feeds the twins
--------------------------------------
``SystemSync`` reads Module 1's *raw* ``outputs/`` folder. Measured against the
twins' own declared ranges, that dataset does not satisfy them: 9,059 of 10,000
raw ``grid.csv`` rows carry a ``grid_export_kw`` above the grid twin's 10,000 kW
limit (peaking at 400,003 kW), so ``run_realtime.py`` halts on row 6.

Module 1's *cleaned* output - the validated product of its own
validate -> clean -> feature-engineer pipeline - satisfies every twin's ranges
for every row of every asset. So ``cleaned`` is the default source here. Pass
``--source raw`` to drive the twins through ``SystemSync`` verbatim instead;
rejections are then reported as data-quality events.

Neither module is changed by this choice: the cleaned path composes Module 2's
own twin classes and ``CSVLoader`` in exactly the order ``SystemSync.sync_once()``
uses them.

Usage:
    python m2_sync.py <output.json> [steps] [--source cleaned|raw]
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common.config import MODULE1_OUTPUT_DIRECTORY
from common.csv_loader import CSVLoader

from battery import BatteryDigitalTwin
from boiler import BoilerDigitalTwin
from compressor import CompressorDigitalTwin
from grid import GridDigitalTwin
from hvac import HVACDigitalTwin
from production_line_a import ProductionLineADigitalTwin
from production_line_b import ProductionLineBDigitalTwin
from solar import SolarDigitalTwin

#: Asset order and CSV filenames, mirroring ``SystemSync.__init__``.
ASSET_SPEC: tuple[tuple[str, type, str], ...] = (
    ("production_line_a", ProductionLineADigitalTwin, "production_line_a_production.csv"),
    ("production_line_b", ProductionLineBDigitalTwin, "production_line_b_production.csv"),
    ("boiler", BoilerDigitalTwin, "boiler.csv"),
    ("compressor", CompressorDigitalTwin, "compressor.csv"),
    ("hvac", HVACDigitalTwin, "hvac.csv"),
    ("solar", SolarDigitalTwin, "solar_plant.csv"),
    ("battery", BatteryDigitalTwin, "battery_storage.csv"),
    ("grid", GridDigitalTwin, "grid.csv"),
)

ASSET_KEYS = tuple(name for name, _cls, _file in ASSET_SPEC)


class TwinFleet:
    """Module 2's eight twins driven from a chosen Module 1 dataset."""

    def __init__(self, data_directory: Path) -> None:
        self.data_directory = data_directory
        self.twins: dict[str, Any] = {}
        self.loaders: dict[str, CSVLoader] = {}
        self.rejections: list[dict[str, Any]] = []

        for name, twin_class, filename in ASSET_SPEC:
            self.twins[name] = twin_class()
            self.loaders[name] = CSVLoader(data_directory / filename)

    def sync_once(self, step: int) -> dict[str, Any]:
        """One synchronization round across all eight twins."""

        states: dict[str, Any] = {}
        for name in ASSET_KEYS:
            twin = self.twins[name]
            row = self.loaders[name].get_next_row()
            try:
                twin.update(row)
            except (ValueError, KeyError, TypeError) as error:
                # The twin rejected the reading. Keep its previous valid state
                # and record why, rather than stopping the pipeline.
                self.rejections.append(
                    {
                        "step": step,
                        "asset": name,
                        "timestamp": row.get("timestamp"),
                        "reason": str(error),
                    }
                )
            states[name] = twin.state_manager.snapshot()
        return states


def resolve_data_directory(source: str) -> Path:
    """Locate the Module 1 dataset for the requested source."""

    if source == "raw":
        return Path(MODULE1_OUTPUT_DIRECTORY)
    return Path(MODULE1_OUTPUT_DIRECTORY) / "cleaned_data"


def collect(steps: int, source: str) -> dict[str, Any]:
    data_directory = resolve_data_directory(source)
    fleet = TwinFleet(data_directory)

    history: list[dict[str, Any]] = []
    for step in range(max(1, steps)):
        states = fleet.sync_once(step)
        # Only publish rounds in which every twin holds a valid state; a twin
        # with no accepted reading yet has an empty snapshot.
        if all(states[name] for name in ASSET_KEYS):
            history.append(states)

    if not history:
        raise RuntimeError(
            f"no complete twin state after {steps} steps from {data_directory}; "
            f"{len(fleet.rejections)} readings were rejected"
        )

    simulations: dict[str, Any] = {}
    learning: dict[str, Any] = {}
    for name, twin in fleet.twins.items():
        learning[name] = twin.behavior_learner.parameters()
        try:
            simulations[name] = twin.simulation.run()
        except Exception as error:  # a twin may refuse an unsupported scenario
            simulations[name] = {"error": f"{type(error).__name__}: {error}"}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "module": "Module 2 - Digital Twin",
        "source": source,
        "data_directory": str(data_directory),
        "steps_requested": steps,
        "steps_published": len(history),
        "assets": list(ASSET_KEYS),
        "states": history[-1],
        "history": history,
        "simulations": simulations,
        "learning": learning,
        "rejected_readings": fleet.rejections,
        "rejected_reading_count": len(fleet.rejections),
    }


def collect_via_system_sync(steps: int) -> dict[str, Any]:
    """Drive the twins through Module 2's own ``SystemSync``, unmodified.

    Used for ``--source raw``. ``SystemSync`` hardwires the raw dataset and does
    not guard against rejections, so a rejection ends the run; whatever was
    synchronized before it is still returned.
    """

    from integration.system_sync import SystemSync

    system = SystemSync()
    history: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []

    for step in range(max(1, steps)):
        try:
            history.append(system.sync_once())
        except (ValueError, KeyError, TypeError) as error:
            rejections.append({"step": step, "asset": None, "reason": str(error)})
            break

    if not history:
        raise RuntimeError(
            f"SystemSync produced no state: {rejections[0]['reason'] if rejections else 'unknown'}"
        )

    twins = {key: getattr(system, key) for key in ASSET_KEYS}
    simulations: dict[str, Any] = {}
    learning: dict[str, Any] = {}
    for name, twin in twins.items():
        learning[name] = twin.behavior_learner.parameters()
        try:
            simulations[name] = twin.simulation.run()
        except Exception as error:
            simulations[name] = {"error": f"{type(error).__name__}: {error}"}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "module": "Module 2 - Digital Twin",
        "source": "raw",
        "data_directory": str(MODULE1_OUTPUT_DIRECTORY),
        "steps_requested": steps,
        "steps_published": len(history),
        "assets": list(ASSET_KEYS),
        "states": history[-1],
        "history": history,
        "simulations": simulations,
        "learning": learning,
        "rejected_readings": rejections,
        "rejected_reading_count": len(rejections),
    }


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]

    if not args:
        print(
            "usage: m2_sync.py <output.json> [steps] [--source cleaned|raw]",
            file=sys.stderr,
        )
        return 2

    destination = Path(args[0])
    steps = int(args[1]) if len(args) > 1 else 48

    source = "cleaned"
    for flag in flags:
        if flag.startswith("--source"):
            source = flag.split("=", 1)[1] if "=" in flag else "cleaned"
    if source not in {"cleaned", "raw"}:
        print(f"unknown source: {source}", file=sys.stderr)
        return 2

    document = (
        collect_via_system_sync(steps) if source == "raw" else collect(steps, source)
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(
        f"digital twin synchronized: {document['steps_published']} steps "
        f"from {document['source']} data "
        f"({document['rejected_reading_count']} readings rejected) -> {destination}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
