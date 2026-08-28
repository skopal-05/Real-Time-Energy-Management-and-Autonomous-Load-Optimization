# Manual Verification - Persons 1 and 2

Run all commands from the repository root.

## Automated baseline

```bash
python3 -m unittest discover -s module2_digital_twin/tests -v
```

For the local workspace layout, prefix Python commands with `PYTHONPATH="Module 2"`.

Expected: eight tests finish with `OK`.

## Check Person 1

```bash
python3 - <<'PY'
from pathlib import Path
from module2_digital_twin.boiler import BoilerDigitalTwin
from module2_digital_twin.production_line_a import ProductionLineADigitalTwin
from module2_digital_twin.production_line_b import ProductionLineBDigitalTwin

data = Path("Module 1 - Data Acquisition/outputs")
systems = [
    (ProductionLineADigitalTwin(), "production_line_a_production.csv"),
    (ProductionLineBDigitalTwin(), "production_line_b_production.csv"),
    (BoilerDigitalTwin(), "boiler.csv"),
]
for twin, filename in systems:
    updates = twin.realtime_sync.sync_csv(data / filename)
    print(twin.name, len(updates), twin.simulation.run()["predicted_metrics"])
PY
```

Confirm each twin accepts rows and prints predicted metrics.

## Check Person 2

```bash
python3 - <<'PY'
from pathlib import Path
from module2_digital_twin.battery import BatteryDigitalTwin
from module2_digital_twin.grid import GridDigitalTwin
from module2_digital_twin.solar import SolarDigitalTwin

data = Path("Module 1 - Data Acquisition/outputs")
systems = [
    (SolarDigitalTwin(), "solar_plant.csv"),
    (BatteryDigitalTwin(), "battery_storage.csv"),
    (GridDigitalTwin(), "grid.csv"),
]
for twin, filename in systems:
    updates = twin.realtime_sync.sync_csv(data / filename)
    print(twin.name, len(updates), twin.simulation.run()["predicted_metrics"])
PY
```

Confirm solar reports conversion efficiency, battery reports state of charge and mode, and grid reports net power, cost, and stability.

## Check rejection of invalid telemetry

```bash
python3 - <<'PY'
from module2_digital_twin.production_line_a import ProductionLineADigitalTwin

state = {
    "timestamp": "2026-07-20 10:00:00",
    "units_per_hour": 40,
    "machine_load_kw": 50,
    "motor_temperature_c": 999,
    "vibration_mm_s": 1.2,
}
try:
    ProductionLineADigitalTwin().update(state)
except ValueError as error:
    print("PASSED:", error)
else:
    raise AssertionError("Invalid state was accepted")
PY
```

Expected: the invalid motor temperature is rejected.

## Check non-destructive simulation

```bash
python3 - <<'PY'
from module2_digital_twin.battery import BatteryDigitalTwin

twin = BatteryDigitalTwin()
twin.realtime_sync.sync_csv(
    "Module 1 - Data Acquisition/outputs/battery_storage.csv"
)
before = twin.state_manager.snapshot()
result = twin.simulation.run({"battery_power_kw": 50, "duration_hours": 1})
after = twin.state_manager.snapshot()
assert before == after
assert result["predicted_metrics"]["power_mode"] == "charging"
print("PASSED:", result["predicted_metrics"])
PY
```

Expected: the scenario reports charging and the synchronized live state remains unchanged.
