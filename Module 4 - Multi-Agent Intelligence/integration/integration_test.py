"""End-to-end integration test for Module 3 and Module 4."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow execution with:
# py -m integration.integration_test
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from integration.agent_controller import AgentController
from integration.agent_validator import AgentValidator
from integration.output_manager import OutputManager


# ------------------------------------------------------------------
# Module 3 forecast location
# ------------------------------------------------------------------

FORECAST_PATH = (
    PROJECT_ROOT.parent
    / "Module 3 - Forecasting"
    / "outputs"
    / "forecast_output.json"
)


def run_integration_test() -> bool:
    """Run and validate the complete Module 3 → Module 4 pipeline."""

    print("=" * 60)
    print("Module 4 - Multi-Agent Intelligence")
    print("End-to-End Integration Test")
    print("=" * 60)

    # --------------------------------------------------------------
    # 1. Check Module 3 forecast
    # --------------------------------------------------------------

    print("\n[1/7] Checking Module 3 forecast...")

    if not FORECAST_PATH.exists():
        print("✗ Forecast file not found:")
        print(f"  {FORECAST_PATH}")
        return False

    print("✓ Module 3 forecast file found")
    print(f"  {FORECAST_PATH}")

    # --------------------------------------------------------------
    # 2. Initialize components
    # --------------------------------------------------------------

    print("\n[2/7] Initializing Module 4 components...")

    controller = AgentController()
    validator = AgentValidator()
    output_manager = OutputManager()

    print("✓ Agent Controller initialized")
    print("✓ Agent Validator initialized")
    print("✓ Output Manager initialized")

    # --------------------------------------------------------------
    # 3. Validate registered agents
    # --------------------------------------------------------------

    print("\n[3/7] Checking registered agents...")

    registered_agents = controller.registered_agents()

    agent_errors = validator.validate_agents(
        registered_agents
    )

    if agent_errors:
        print("✗ Agent registration validation failed")

        for error in agent_errors:
            print(f"  - {error}")

        return False

    print(
        f"✓ All {len(registered_agents)} expected agents registered"
    )

    for agent in registered_agents:
        print(f"  ✓ {agent}")

    # --------------------------------------------------------------
    # 4. Load and validate Module 3 forecast
    # --------------------------------------------------------------

    print("\n[4/7] Validating Module 3 forecast...")

    try:
        forecast = controller.load_forecast(
            FORECAST_PATH
        )
    except Exception as exc:
        print("✗ Failed to load forecast")
        print(f"  Error: {exc}")
        return False

    forecast_errors = validator.validate_forecast(
        forecast
    )

    if forecast_errors:
        print("✗ Forecast validation failed")

        for error in forecast_errors:
            print(f"  - {error}")

        return False

    print("✓ Module 3 forecast structure is valid")

    # --------------------------------------------------------------
    # 5. Run complete Module 4 pipeline
    # --------------------------------------------------------------

    print("\n[5/7] Running Module 4 agent pipeline...")

    try:
        state = controller.build_state(
            forecast
        )

        recommendations = controller.generate_recommendations(
            forecast,
            include_rules=True,
        )
    except Exception as exc:
        print("✗ Agent pipeline execution failed")
        print(f"  Error: {exc}")
        return False

    recommendation_errors = (
        validator.validate_recommendations(
            recommendations
        )
    )

    if recommendation_errors:
        print("✗ Recommendation validation failed")

        for error in recommendation_errors:
            print(f"  - {error}")

        return False

    print(
        f"✓ Generated {len(recommendations)} recommendations"
    )

    print("\nRecommendations:")

    for recommendation in recommendations:
        print(
            f"  [{recommendation.priority.upper():8}] "
            f"{recommendation.agent:30} "
            f"→ {recommendation.action}"
        )

    # --------------------------------------------------------------
    # 6. Validate and save outputs
    # --------------------------------------------------------------

    print("\n[6/7] Validating and saving outputs...")

    validation = validator.validate_complete_pipeline(
        forecast=forecast,
        registered_agents=registered_agents,
        recommendations=recommendations,
    )

    if not validation["valid"]:
        print("✗ Complete pipeline validation failed")

        for error in (
            validation["forecast_errors"]
            + validation["agent_errors"]
            + validation["recommendation_errors"]
        ):
            print(f"  - {error}")

        return False

    summary = controller.summarize(
        recommendations
    )

    try:
        recommendations_path = (
            output_manager.save_recommendations(
                recommendations
            )
        )

        optimized_state_path = (
            output_manager.save_optimized_state(
                state,
                recommendations,
            )
        )

        report_path = (
            output_manager.save_report(
                summary,
                recommendations,
            )
        )

        log_path = output_manager.save_log(
            "Module 3 to Module 4 integration completed successfully."
        )

    except Exception as exc:
        print("✗ Failed to save output files")
        print(f"  Error: {exc}")
        return False

    print("✓ Forecast validation passed")
    print("✓ Agent validation passed")
    print("✓ Recommendation validation passed")

    print("\nGenerated output files:")

    print(
        f"  ✓ Recommendations : "
        f"{recommendations_path}"
    )

    print(
        f"  ✓ Optimized state : "
        f"{optimized_state_path}"
    )

    print(
        f"  ✓ Report          : "
        f"{report_path}"
    )

    print(
        f"  ✓ Log             : "
        f"{log_path}"
    )

    # --------------------------------------------------------------
    # 7. Final summary
    # --------------------------------------------------------------

    print("\n[7/7] Final integration summary...")

    print("\nPipeline Summary:")

    print(
        f"  Registered agents       : "
        f"{len(registered_agents)}"
    )

    print(
        f"  Recommendations         : "
        f"{summary['total_recommendations']}"
    )

    print(
        f"  Critical                : "
        f"{summary['priority_counts']['critical']}"
    )

    print(
        f"  High                    : "
        f"{summary['priority_counts']['high']}"
    )

    print(
        f"  Medium                  : "
        f"{summary['priority_counts']['medium']}"
    )

    print(
        f"  Low                     : "
        f"{summary['priority_counts']['low']}"
    )

    print(
        f"  Highest priority        : "
        f"{summary['highest_priority']}"
    )

    print(
        f"  Highest-priority agent  : "
        f"{summary['highest_priority_agent']}"
    )

    print(
        f"  Highest-priority action : "
        f"{summary['highest_priority_action']}"
    )

    print("\nValidation Status:")

    print("  ✓ Forecast validation")
    print("  ✓ Agent registration validation")
    print("  ✓ Recommendation validation")
    print("  ✓ Output generation")

    print("\n" + "=" * 60)
    print("✓ INTEGRATION TEST PASSED")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = run_integration_test()

    raise SystemExit(
        0 if success else 1
    )