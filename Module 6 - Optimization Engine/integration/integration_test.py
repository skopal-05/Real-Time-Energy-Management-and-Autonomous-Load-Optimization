"""End-to-end integration test for Modules 4, 5, and 6."""

from __future__ import annotations

import sys
from pathlib import Path


# Allow execution with:
# py -m integration.integration_test
MODULE_ROOT = Path(__file__).resolve().parent.parent

if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))


from integration.optimization_controller import (
    OptimizationController,
)
from integration.integration_validator import (
    IntegrationValidator,
)


def run_integration_test() -> bool:
    """Run and validate the complete Module 4/5 → Module 6 pipeline."""

    print("=" * 68)
    print("Module 6 - Optimization Engine")
    print("Module 4 + Module 5 → Module 6 Integration Test")
    print("=" * 68)

    try:

        # ----------------------------------------------------------
        # 1. Initialize components
        # ----------------------------------------------------------

        print("\n[1/6] Initializing Module 6 components...")

        controller = OptimizationController()
        validator = IntegrationValidator()

        print("PASS Optimization Controller initialized")
        print("PASS Integration Validator initialized")

        # ----------------------------------------------------------
        # 2. Check upstream input files
        # ----------------------------------------------------------

        print("\n[2/6] Checking Module 4 and Module 5 inputs...")

        best_scenario_path = (
            controller.DEFAULT_BEST_SCENARIO_PATH
            if hasattr(
                controller,
                "DEFAULT_BEST_SCENARIO_PATH",
            )
            else None
        )

        recommendations_path = (
            controller.DEFAULT_RECOMMENDATIONS_PATH
            if hasattr(
                controller,
                "DEFAULT_RECOMMENDATIONS_PATH",
            )
            else None
        )

        # Use module-level defaults from the controller.
        if best_scenario_path is None:
            from integration.optimization_controller import (
                DEFAULT_BEST_SCENARIO_PATH,
            )

            best_scenario_path = DEFAULT_BEST_SCENARIO_PATH

        if recommendations_path is None:
            from integration.optimization_controller import (
                DEFAULT_RECOMMENDATIONS_PATH,
            )

            recommendations_path = DEFAULT_RECOMMENDATIONS_PATH

        if not Path(best_scenario_path).is_file():
            raise FileNotFoundError(
                f"Module 5 best scenario not found: "
                f"{best_scenario_path}"
            )

        if not Path(recommendations_path).is_file():
            raise FileNotFoundError(
                f"Module 4 recommendations not found: "
                f"{recommendations_path}"
            )

        print("PASS Module 5 best scenario found")
        print(f"  {best_scenario_path}")

        print("PASS Module 4 recommendations found")
        print(f"  {recommendations_path}")

        # ----------------------------------------------------------
        # 3. Load and validate upstream data
        # ----------------------------------------------------------

        print("\n[3/6] Validating Module 4 and Module 5 inputs...")

        best_scenario_document = controller._load_json(
            best_scenario_path
        )

        recommendation_document = controller._load_json(
            recommendations_path
        )

        if not isinstance(
            best_scenario_document,
            dict,
        ):
            raise ValueError(
                "Module 5 best scenario must be a JSON object"
            )

        if not isinstance(
            recommendation_document,
            dict,
        ):
            raise ValueError(
                "Module 4 recommendations must be a JSON object"
            )

        best_scenario = controller._extract_best_scenario(
            best_scenario_document
        )

        recommendations = controller._extract_recommendations(
            recommendation_document
        )

        scenario_errors = validator.validate_best_scenario(
            best_scenario
        )

        if scenario_errors:
            raise ValueError(
                "Module 5 validation failed: "
                + "; ".join(scenario_errors)
            )

        recommendation_errors = (
            validator.validate_recommendations(
                recommendations
            )
        )

        if recommendation_errors:
            raise ValueError(
                "Module 4 validation failed: "
                + "; ".join(recommendation_errors)
            )

        print(
            "PASS Module 5 best scenario validation"
        )

        print(
            "PASS Module 4 recommendations validation"
        )

        print(
            f"  Recommendations received: "
            f"{len(recommendations)}"
        )

        # ----------------------------------------------------------
        # 4. Run optimization pipeline
        # ----------------------------------------------------------

        print(
            "\n[4/6] Running Module 4/5 → Module 6 optimization..."
        )

        result = controller.run(
            best_scenario_path=best_scenario_path,
            recommendations_path=recommendations_path,
            save_outputs=True,
        )

        problem = result["optimization_problem"]
        optimization_result = result["optimization_result"]

        print("PASS optimization problem created")

        print(
            f"  Decision variables: "
            f"{len(problem.bounds)}"
        )

        print("PASS genetic optimization completed")

        # ----------------------------------------------------------
        # 5. Validate optimization result
        # ----------------------------------------------------------

        print(
            "\n[5/6] Validating optimized operating state..."
        )

        result_errors = validator.validate_result(
            optimization_result,
            problem,
        )

        if result_errors:
            raise ValueError(
                "optimization result validation failed: "
                + "; ".join(result_errors)
            )

        if not optimization_result.feasible:
            raise ValueError(
                "optimized operating state is not feasible"
            )

        print("PASS optimized state is feasible")

        print(
            f"  Best fitness: "
            f"{optimization_result.algorithm['best_fitness']}"
        )

        print(
            f"  GA evaluations: "
            f"{optimization_result.algorithm['evaluations']}"
        )

        print(
            f"  Projected SOC: "
            f"{optimization_result.optimized_state.get('projected_soc_percent')}"
        )

        # ----------------------------------------------------------
        # 6. Validate generated outputs
        # ----------------------------------------------------------

        print(
            "\n[6/6] Checking Module 6 outputs..."
        )

        output_errors = validator.validate_output_files(
            result["output_files"]
        )

        if output_errors:
            raise ValueError(
                "output validation failed: "
                + "; ".join(output_errors)
            )

        print("PASS optimized state output")
        print(
            f"  {result['output_files']['optimized_state']}"
        )

        print("PASS recommendation output")
        print(
            f"  {result['output_files']['recommendations']}"
        )

        print("PASS optimization report")
        print(
            f"  {result['output_files']['report']}"
        )

        # ----------------------------------------------------------
        # Final summary
        # ----------------------------------------------------------

        report = result["report"]
        summary = report["summary"]

        print("\n" + "-" * 68)
        print("MODULE 6 OPTIMIZATION SUMMARY")
        print("-" * 68)

        print(
            f"Best scenario          : "
            f"{best_scenario['name']}"
        )

        print(
            f"Scenario ID            : "
            f"{best_scenario['scenario_id']}"
        )

        print(
            f"Optimization feasible  : "
            f"{summary['feasible']}"
        )

        print(
            f"Recommendations        : "
            f"{summary['recommendation_count']}"
        )

        print(
            f"Energy saving (kWh)    : "
            f"{summary['energy_saving_kwh']}"
        )

        print(
            f"Cost saving (INR)      : "
            f"{summary['cost_saving_inr']}"
        )

        print(
            f"Emissions avoided      : "
            f"{summary['emissions_avoided_kg_co2e']}"
        )

        print("-" * 68)
        print("INTEGRATION TEST PASSED")
        print("-" * 68)

        return True

    except Exception as exc:

        print("\n" + "-" * 68)
        print(
            f"INTEGRATION TEST FAILED: {exc}"
        )
        print("-" * 68)

        return False


if __name__ == "__main__":
    raise SystemExit(
        0 if run_integration_test()
        else 1
    )