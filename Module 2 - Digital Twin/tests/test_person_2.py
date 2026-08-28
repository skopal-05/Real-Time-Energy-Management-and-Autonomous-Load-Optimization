import unittest
from pathlib import Path

from module2_digital_twin.battery import BatteryDigitalTwin
from module2_digital_twin.grid import GridDigitalTwin
from module2_digital_twin.solar import SolarDigitalTwin


def find_data_directory():
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "Module 1 - Data Acquisition" / "outputs"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("Could not locate Module 1 telemetry outputs")


DATA = find_data_directory()


class Person2DigitalTwinTests(unittest.TestCase):
    def exercise_twin(self, twin, filename):
        updates = twin.realtime_sync.sync_csv(DATA / filename)
        self.assertGreater(len(updates), 0)
        self.assertGreater(twin.behavior_learner.samples_seen, 0)
        self.assertIn("predicted_metrics", twin.simulation.run())

    def test_solar(self):
        self.exercise_twin(SolarDigitalTwin(), "solar_plant.csv")

    def test_battery(self):
        twin = BatteryDigitalTwin()
        self.exercise_twin(twin, "battery_storage.csv")
        result = twin.simulation.run({"battery_power_kw": 50.0, "duration_hours": 1.0})
        self.assertEqual(result["predicted_metrics"]["power_mode"], "charging")

    def test_grid(self):
        twin = GridDigitalTwin()
        self.exercise_twin(twin, "grid.csv")
        stable = twin.simulation.run()["predicted_metrics"]["grid_stable"]
        self.assertIsInstance(stable, bool)

    def test_duplicate_rows_are_skipped(self):
        twin = SolarDigitalTwin()
        first = twin.realtime_sync.sync_csv(DATA / "solar_plant.csv")
        repeated = twin.realtime_sync.sync_csv(DATA / "solar_plant.csv", only_new=True)
        self.assertGreater(len(first), 0)
        self.assertEqual(repeated, [])


if __name__ == "__main__":
    unittest.main()
