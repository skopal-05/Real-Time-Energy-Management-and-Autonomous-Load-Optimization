"""
End-to-end integration test for Modules 3–7.

Pipeline:
Module 3 → Module 4 → Module 5 → Module 6 → Module 7
"""

from __future__ import annotations

import sys
from pathlib import Path


MODULE_ROOT = Path(
    __file__
).resolve().parent.parent

if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(MODULE_ROOT),
    )


from integration.final_controller import (
    FinalIntegrationController,
)
from integration.integration_validator import (
    FinalIntegrationValidator,
)


def run_integration_test() -> bool:

    print("=" * 72)
    print(
        "MODULE 7 - FINAL END-TO-END INTEGRATION TEST"
    )
    print(
        "Module 3 → Module 4 → Module 5 → Module 6 → Module 7"
    )
    print("=" * 72)

    try:

        # ----------------------------------------------------------
        # 1. Initialize
        # ----------------------------------------------------------

        print(
            "\n[1/7] Initializing Module 7 integration..."
        )

        controller = (
            FinalIntegrationController()
        )

        validator = (
            FinalIntegrationValidator()
        )

        print(
            "PASS Final Integration Controller initialized"
        )

        print(
            "PASS Final Integration Validator initialized"
        )

        # ----------------------------------------------------------
        # 2. Check upstream files
        # ----------------------------------------------------------

        print(
            "\n[2/7] Checking Modules 3–6 outputs..."
        )

        input_files = {
            "Module 3 forecast":
                controller.DEFAULT_FORECAST_PATH
                if hasattr(
                    controller,
                    "DEFAULT_FORECAST_PATH",
                )
                else None,
            "Module 4 recommendations":
                controller.DEFAULT_RECOMMENDATIONS_PATH
                if hasattr(
                    controller,
                    "DEFAULT_RECOMMENDATIONS_PATH",
                )
                else None,
            "Module 5 best scenario":
                controller.DEFAULT_BEST_SCENARIO_PATH
                if hasattr(
                    controller,
                    "DEFAULT_BEST_SCENARIO_PATH",
                )
                else None,
            "Module 5 scenario comparison":
                controller.DEFAULT_SCENARIO_COMPARISON_PATH
                if hasattr(
                    controller,
                    "DEFAULT_SCENARIO_COMPARISON_PATH",
                )
                else None,
            "Module 6 optimization report":
                controller.DEFAULT_OPTIMIZATION_REPORT_PATH
                if hasattr(
                    controller,
                    "DEFAULT_OPTIMIZATION_REPORT_PATH",
                )
                else None,
            "Module 6 optimized state":
                controller.DEFAULT_OPTIMIZED_STATE_PATH
                if hasattr(
                    controller,
                    "DEFAULT_OPTIMIZED_STATE_PATH",
                )
                else None,
        }

        # The defaults are module-level constants in the controller.
        if input_files["Module 3 forecast"] is None:
            from integration.final_controller import (
                DEFAULT_FORECAST_PATH,
            )

            input_files[
                "Module 3 forecast"
            ] = DEFAULT_FORECAST_PATH

        if input_files["Module 4 recommendations"] is None:
            from integration.final_controller import (
                DEFAULT_RECOMMENDATIONS_PATH,
            )

            input_files[
                "Module 4 recommendations"
            ] = DEFAULT_RECOMMENDATIONS_PATH

        if input_files["Module 5 best scenario"] is None:
            from integration.final_controller import (
                DEFAULT_BEST_SCENARIO_PATH,
            )

            input_files[
                "Module 5 best scenario"
            ] = DEFAULT_BEST_SCENARIO_PATH

        if input_files["Module 5 scenario comparison"] is None:
            from integration.final_controller import (
                DEFAULT_SCENARIO_COMPARISON_PATH,
            )

            input_files[
                "Module 5 scenario comparison"
            ] = DEFAULT_SCENARIO_COMPARISON_PATH

        if input_files["Module 6 optimization report"] is None:
            from integration.final_controller import (
                DEFAULT_OPTIMIZATION_REPORT_PATH,
            )

            input_files[
                "Module 6 optimization report"
            ] = DEFAULT_OPTIMIZATION_REPORT_PATH

        if input_files["Module 6 optimized state"] is None:
            from integration.final_controller import (
                DEFAULT_OPTIMIZED_STATE_PATH,
            )

            input_files[
                "Module 6 optimized state"
            ] = DEFAULT_OPTIMIZED_STATE_PATH

        for label, path in input_files.items():

            path = Path(path)

            if not path.is_file():
                raise FileNotFoundError(
                    f"{label} not found: {path}"
                )

            print(
                f"PASS {label}"
            )
            print(
                f"     {path}"
            )

        # ----------------------------------------------------------
        # 3. Load upstream artifacts
        # ----------------------------------------------------------

        print(
            "\n[3/7] Loading Modules 3–6 artifacts..."
        )

        forecast = controller._require_mapping(
            controller._load_json(
                input_files[
                    "Module 3 forecast"
                ]
            ),
            "Module 3 forecast",
        )

        recommendation_document = (
            controller._require_mapping(
                controller._load_json(
                    input_files[
                        "Module 4 recommendations"
                    ]
                ),
                "Module 4 recommendations",
            )
        )

        best_scenario_document = (
            controller._require_mapping(
                controller._load_json(
                    input_files[
                        "Module 5 best scenario"
                    ]
                ),
                "Module 5 best scenario",
            )
        )

        scenario_comparison = (
            controller._require_mapping(
                controller._load_json(
                    input_files[
                        "Module 5 scenario comparison"
                    ]
                ),
                "Module 5 scenario comparison",
            )
        )

        optimization_report = (
            controller._require_mapping(
                controller._load_json(
                    input_files[
                        "Module 6 optimization report"
                    ]
                ),
                "Module 6 optimization report",
            )
        )

        optimized_state_document = (
            controller._require_mapping(
                controller._load_json(
                    input_files[
                        "Module 6 optimized state"
                    ]
                ),
                "Module 6 optimized state",
            )
        )

        optimized_state = optimized_state_document.get(
            "optimized_state"
        )

        if not isinstance(
            optimized_state,
            dict,
        ):
            raise ValueError(
                "Module 6 optimized state JSON must contain "
                "an optimized_state object"
            )

        recommendations = (
            controller._extract_recommendations(
                recommendation_document
            )
        )

        scenarios = (
            controller._extract_ranked_scenarios(
                scenario_comparison
            )
        )

        print(
            f"PASS forecast loaded"
        )

        print(
            f"PASS recommendations loaded: "
            f"{len(recommendations)}"
        )

        print(
            f"PASS scenarios loaded: "
            f"{len(scenarios)}"
        )

        print(
            "PASS optimization report loaded"
        )

        # ----------------------------------------------------------
        # 4. Validate upstream contracts
        # ----------------------------------------------------------

        print(
            "\n[4/7] Validating Modules 3–6 contracts..."
        )

        validation = validator.validate_pipeline(
            forecast=forecast,
            recommendations=recommendations,
            scenarios=scenarios,
            optimization_report=optimization_report,
            optimized_state=optimized_state,
        )

        if not validation["valid"]:

            print(
                "FAIL upstream validation"
            )

            for key in (
                "forecast_errors",
                "recommendation_errors",
                "scenario_errors",
                "optimization_errors",
                "optimized_state_errors",
            ):
                for error in validation[key]:
                    print(
                        f"  - {error}"
                    )

            return False

        print(
            "PASS Module 3 forecast contract"
        )

        print(
            "PASS Module 4 recommendation contract"
        )

        print(
            "PASS Module 5 scenario contract"
        )

        print(
            "PASS Module 6 optimization contract"
        )

        print(
            "PASS Module 6 optimized-state contract"
        )

        # ----------------------------------------------------------
        # 5. Run Module 7 final controller
        # ----------------------------------------------------------

        print(
            "\n[5/7] Running final Module 7 controller..."
        )

        result = controller.run(
            forecast_path=input_files[
                "Module 3 forecast"
            ],
            recommendations_path=input_files[
                "Module 4 recommendations"
            ],
            best_scenario_path=input_files[
                "Module 5 best scenario"
            ],
            scenario_comparison_path=input_files[
                "Module 5 scenario comparison"
            ],
            optimization_report_path=input_files[
                "Module 6 optimization report"
            ],
            optimized_state_path=input_files[
                "Module 6 optimized state"
            ],
            save_outputs=True,
        )

        print(
            "PASS final controller executed"
        )

        # ----------------------------------------------------------
        # 6. Validate Module 7 outputs
        # ----------------------------------------------------------

        print(
            "\n[6/7] Validating Module 7 outputs..."
        )

        final_validation = (
            validator.validate_pipeline(
                forecast=forecast,
                recommendations=recommendations,
                scenarios=scenarios,
                optimization_report=optimization_report,
                optimized_state=optimized_state,
                final_output=result,
                output_files=result.get(
                    "output_files"
                ),
            )
        )

        if not final_validation["valid"]:

            print(
                "FAIL Module 7 validation"
            )

            for key in (
                "forecast_errors",
                "recommendation_errors",
                "scenario_errors",
                "optimization_errors",
                "optimized_state_errors",
                "final_output_errors",
                "output_errors",
            ):
                for error in final_validation[key]:
                    print(
                        f"  - {error}"
                    )

            return False

        print(
            "PASS final pipeline validation"
        )

        print(
            "PASS Module 7 performance output"
        )

        print(
            "PASS Module 7 monitoring output"
        )

        print(
            "PASS Module 7 explainability status output"
        )

        print(
            "PASS Module 7 anomaly status output"
        )

        # ----------------------------------------------------------
        # 7. Final summary
        # ----------------------------------------------------------

        print(
            "\n[7/7] Final integration summary..."
        )

        performance = result[
            "performance"
        ]

        decision = performance[
            "decision_pipeline"
        ]

        benchmark = performance[
            "optimization_benchmark"
        ]

        benchmark_summary = benchmark[
            "summary"
        ]

        print(
            "\nPipeline:"
        )

        print(
            "  Module 3 → Forecasting       : PASS"
        )

        print(
            "  Module 4 → Multi-Agent       : PASS"
        )

        print(
            "  Module 5 → Scenario          : PASS"
        )

        print(
            "  Module 6 → Optimization      : PASS"
        )

        print(
            "  Module 7 → Evaluation        : PASS"
        )

        print(
            "\nResults:"
        )

        print(
            f"  Recommendations              : "
            f"{decision['recommendation_count']}"
        )

        print(
            f"  Scenarios evaluated          : "
            f"{decision['scenario_count']}"
        )

        print(
            f"  Best scenario                : "
            f"{decision['best_scenario_id']}"
        )

        print(
            f"  Best scenario score          : "
            f"{decision['best_scenario_score']}"
        )

        print(
            f"  Optimization feasible        : "
            f"{decision['optimization_feasible']}"
        )

        print(
            f"  Benchmark improved           : "
            f"{benchmark_summary['improved']}"
        )

        print(
            f"  Benchmark regressed          : "
            f"{benchmark_summary['regressed']}"
        )

        print(
            f"  Benchmark unchanged          : "
            f"{benchmark_summary['unchanged']}"
        )

        print(
            "\nOptional components:"
        )

        print(
            "  Model monitoring             : "
            f"{result['monitoring']['status']}"
        )

        print(
            "  Explainability               : "
            f"{result['explainability']['status']}"
        )

        print(
            "  Anomaly detection            : "
            f"{result['anomaly_detection']['status']}"
        )

        print(
            "\nGenerated outputs:"
        )

        for name, path in result[
            "output_files"
        ].items():
            print(
                f"  {name:20} : {path}"
            )

        print("\n" + "=" * 72)
        print(
            "✓ MODULE 7 END-TO-END INTEGRATION TEST PASSED"
        )
        print("=" * 72)

        return True

    except Exception as exc:

        print("\n" + "=" * 72)
        print(
            f"✗ INTEGRATION TEST FAILED: {exc}"
        )
        print("=" * 72)

        return False


if __name__ == "__main__":
    raise SystemExit(
        0
        if run_integration_test()
        else 1
    )