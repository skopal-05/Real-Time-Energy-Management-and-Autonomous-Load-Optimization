"""End-to-end controller tests using the real Module 3 and 4 outputs."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parent.parent
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from integration.scenario_controller import ScenarioController


class ControllerIntegrationTests(unittest.TestCase):
    def test_real_inputs_generate_all_required_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = ScenarioController(output_directory=directory).run()
            self.assertGreaterEqual(result["report"]["scenario_count"], 4)
            self.assertEqual(result["best_scenario"]["ranking"]["rank"], 1)
            self.assertEqual(result["report"]["status"], "completed")
            for output_path in result["output_files"].values():
                path = Path(output_path)
                self.assertTrue(path.is_file())
                with path.open(encoding="utf-8") as handle:
                    self.assertIsInstance(json.load(handle), dict)


if __name__ == "__main__":
    unittest.main()
