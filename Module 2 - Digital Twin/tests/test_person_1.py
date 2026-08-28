import csv
import unittest
from pathlib import Path

from module2_digital_twin.boiler import BoilerDigitalTwin
from module2_digital_twin.production_line_a import ProductionLineADigitalTwin
from module2_digital_twin.production_line_b import ProductionLineBDigitalTwin


def find_data_directory():
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "Module 1 - Data Acquisition" / "outputs"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("Could not locate Module 1 telemetry outputs")


DATA = find_data_directory()


class Person1DigitalTwinTests(unittest.TestCase):
    def exercise_twin(self, twin, filename):
        updates = twin.realtime_sync.sync_csv(DATA / filename)
        self.assertGreater(len(updates), 0)
        self.assertEqual(len(updates), len(twin.state_manager.history))
        self.assertGreater(twin.behavior_learner.samples_seen, 0)
        self.assertIn("predicted_metrics", twin.simulation.run())

    def test_production_line_a(self):
        self.exercise_twin(ProductionLineADigitalTwin(), "production_line_a_production.csv")

    def test_production_line_b(self):
        self.exercise_twin(ProductionLineBDigitalTwin(), "production_line_b_production.csv")

    def test_boiler(self):
        self.exercise_twin(BoilerDigitalTwin(), "boiler.csv")

    def test_out_of_range_state_is_rejected(self):
        with (DATA / "production_line_a_production.csv").open(newline="", encoding="utf-8") as stream:
            state = next(csv.DictReader(stream))
        state["motor_temperature_c"] = "999"
        with self.assertRaises(ValueError):
            ProductionLineADigitalTwin().update(state)


if __name__ == "__main__":
    unittest.main()
