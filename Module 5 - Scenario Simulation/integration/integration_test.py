"""Executable end-to-end validation for Modules 3, 4, and 5."""

from __future__ import annotations

import sys
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parent.parent

if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))


from integration.scenario_controller import ScenarioController


EXPECTED_SCENARIO_COUNT = 5

EXPECTED_SCENARIO_IDS = {
    "baseline",
    "agent_optimized",
    "renewable_first",
    "cost_saver",
    "resilience",
}


def run_integration_test() -> bool:
    print("=" * 64)
    print(
        "Module 5 - Generative Scenario Simulation "
        "Integration Test"
    )
    print("=" * 64)

    try:

        result = ScenarioController().run()

        scenarios = result["scenarios"]
        report = result["report"]
        best = result["best_scenario"]

        # ---------------------------------------------------------
        # Scenario count
        # ---------------------------------------------------------

        if len(scenarios) != EXPECTED_SCENARIO_COUNT:
            raise AssertionError(
                "expected "
                f"{EXPECTED_SCENARIO_COUNT} scenarios, "
                f"got {len(scenarios)}"
            )

        print(
            f"PASS scenario count: "
            f"{len(scenarios)}"
        )

        # ---------------------------------------------------------
        # Scenario IDs
        # ---------------------------------------------------------

        scenario_ids = {
            item["scenario_id"]
            for item in scenarios
        }

        if scenario_ids != EXPECTED_SCENARIO_IDS:
            raise AssertionError(
                "unexpected scenario identifiers: "
                f"{sorted(scenario_ids)}"
            )

        print(
            "PASS scenario identifiers: "
            f"{sorted(scenario_ids)}"
        )

        # ---------------------------------------------------------
        # Ranking
        # ---------------------------------------------------------

        ranks = [
            item["ranking"]["rank"]
            for item in scenarios
        ]

        if sorted(ranks) != list(
            range(1, EXPECTED_SCENARIO_COUNT + 1)
        ):
            raise AssertionError(
                f"invalid ranking sequence: {ranks}"
            )

        if best["ranking"]["rank"] != 1:
            raise AssertionError(
                "best scenario does not have rank 1"
            )

        print(
            f"PASS ranking: best = "
            f"{report['best_scenario_name']}"
        )

        # ---------------------------------------------------------
        # Baseline semantic check
        # ---------------------------------------------------------

        baseline = next(
            item
            for item in scenarios
            if item["scenario_id"] == "baseline"
        )

        baseline_load = baseline["metrics"]["energy"][
            "useful_electrical_load_kwh"
        ]

        # Current Module 3 electrical forecast:
        # compressor 60.84 + HVAC 7.86 = 68.70 kW
        expected_baseline_load = 68.70

        if abs(
            baseline_load - expected_baseline_load
        ) > 0.01:
            raise AssertionError(
                "baseline electrical load mismatch: "
                f"expected approximately "
                f"{expected_baseline_load}, "
                f"got {baseline_load}"
            )

        print(
            f"PASS baseline electrical load: "
            f"{baseline_load:.3f} kWh"
        )

        # ---------------------------------------------------------
        # Score validation
        # ---------------------------------------------------------

        for scenario in scenarios:

            score = scenario["ranking"]["score"]

            if not 0 <= score <= 100:
                raise AssertionError(
                    f"invalid score for "
                    f"{scenario['scenario_id']}: "
                    f"{score}"
                )

        print(
            "PASS ranking scores are within 0-100"
        )

        # ---------------------------------------------------------
        # Energy-flow validation
        # ---------------------------------------------------------

        for scenario in scenarios:

            energy = scenario["metrics"]["energy"]

            if energy["grid_import_kwh"] < 0:
                raise AssertionError(
                    f"negative grid import for "
                    f"{scenario['scenario_id']}"
                )

            if energy["grid_export_kwh"] < 0:
                raise AssertionError(
                    f"negative grid export for "
                    f"{scenario['scenario_id']}"
                )

            if (
                energy["battery_charge_kwh"] > 0
                and energy["battery_discharge_kwh"] > 0
            ):
                raise AssertionError(
                    f"battery both charging and "
                    f"discharging in "
                    f"{scenario['scenario_id']}"
                )

        print(
            "PASS energy-flow constraints"
        )

        # ---------------------------------------------------------
        # Output files
        # ---------------------------------------------------------

        output_files = result["output_files"]

        for key, path in output_files.items():

            output_path = Path(path)

            if not output_path.is_file():
                raise AssertionError(
                    f"missing output file: "
                    f"{output_path}"
                )

            print(
                f"PASS output {key}: "
                f"{output_path}"
            )

        # ---------------------------------------------------------
        # Final report
        # ---------------------------------------------------------

        print("-" * 64)
        print(
            f"Scenarios generated and ranked: "
            f"{report['scenario_count']}"
        )
        print(
            f"Best scenario: "
            f"{report['best_scenario_name']}"
        )
        print(
            f"Weighted score: "
            f"{report['best_score']:.2f}/100"
        )
        print("-" * 64)
        print(
            "INTEGRATION TEST PASSED"
        )

        return True

    except Exception as exc:

        print(
            f"FAILED: {exc}"
        )

        return False


if __name__ == "__main__":
    raise SystemExit(
        0 if run_integration_test()
        else 1
    )