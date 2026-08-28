"""End-to-end controller for Module 4/5 to Module 6 optimization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from optimization.optimizer import Optimizer
from recommendation.recommendation_engine import RecommendationEngine
from contracts import OptimizationResult


MODULE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = MODULE_ROOT.parent

DEFAULT_BEST_SCENARIO_PATH = (
    PROJECT_ROOT
    / "Module 5 - Scenario Simulation"
    / "outputs"
    / "best_scenario"
    / "best_scenario.json"
)

DEFAULT_RECOMMENDATIONS_PATH = (
    PROJECT_ROOT
    / "Module 4 - Multi-Agent Intelligence"
    / "outputs"
    / "recommendations"
    / "recommendations.json"
)

DEFAULT_OUTPUT_DIRECTORY = MODULE_ROOT / "outputs"


class OptimizationController:
    """Connect Module 4 and Module 5 outputs with Module 6."""

    name = "optimization_controller"

    def __init__(
        self,
        output_directory: str | Path | None = None,
        *,
        optimizer: Optimizer | None = None,
        recommendation_engine: RecommendationEngine | None = None,
        validator: Any | None = None,
    ) -> None:
        self.output_directory = Path(
            output_directory or DEFAULT_OUTPUT_DIRECTORY
        )

        self.optimizer = optimizer or Optimizer()
        self.recommendation_engine = (
            recommendation_engine or RecommendationEngine()
        )
        self.validator = validator

    # ==============================================================
    # JSON LOADING
    # ==============================================================

    @staticmethod
    def _load_json(path: str | Path) -> Any:
        source = Path(path)

        if not source.is_file():
            raise FileNotFoundError(
                f"input file not found: {source}"
            )

        with source.open(
            "r",
            encoding="utf-8",
        ) as handle:
            return json.load(handle)

    # ==============================================================
    # INPUT VALIDATION
    # ==============================================================

    @staticmethod
    def _extract_recommendations(
        recommendation_document: Mapping[str, Any],
    ) -> list[Mapping[str, Any]]:
        recommendations = recommendation_document.get(
            "recommendations",
            [],
        )

        if not isinstance(recommendations, list):
            raise ValueError(
                "recommendations JSON must contain a list"
            )

        return recommendations

    @staticmethod
    def _extract_best_scenario(
        best_scenario_document: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        best_scenario = best_scenario_document.get(
            "best_scenario"
        )

        if not isinstance(best_scenario, Mapping):
            raise ValueError(
                "best scenario JSON must contain "
                "a best_scenario object"
            )

        return best_scenario

    # ==============================================================
    # SYSTEM STATE
    # ==============================================================

    @staticmethod
    def _build_system_state(
        best_scenario: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Build Module 6 system-state inputs from Module 5 data."""

        operating_point = best_scenario.get(
            "operating_point",
            {},
        )

        if not isinstance(
            operating_point,
            Mapping,
        ):
            raise ValueError(
                "best scenario operating_point must be an object"
            )

        return {
            "renewable_generation_kw": float(
                operating_point.get(
                    "renewable_generation_kw",
                    0.0,
                )
            ),
            "state_of_charge_percent": 50.0,
            "capacity_kwh": 100.0,
            "minimum_soc_percent": 20.0,
            "maximum_soc_percent": 90.0,
            "maximum_charge_kw": 50.0,
            "maximum_discharge_kw": 50.0,
            "grid_import_limit_kw": 500.0,
            "grid_export_limit_kw": float(
                operating_point.get(
                    "grid_export_limit_kw",
                    100.0,
                )
            ),
            "maximum_compressor_power_kw": max(
                100.0,
                float(
                    operating_point.get(
                        "compressor_power_kw",
                        0.0,
                    )
                ),
            ),
            "maximum_hvac_power_kw": max(
                100.0,
                float(
                    operating_point.get(
                        "hvac_power_kw",
                        0.0,
                    )
                ),
            ),
            "maximum_fuel_flow_m3_hr": max(
                200.0,
                float(
                    operating_point.get(
                        "boiler_fuel_m3_hr",
                        0.0,
                    )
                ),
            ),
        }

    # ==============================================================
    # COMPLETE PIPELINE
    # ==============================================================

    def run(
        self,
        best_scenario_path: str | Path = DEFAULT_BEST_SCENARIO_PATH,
        recommendations_path: str | Path = DEFAULT_RECOMMENDATIONS_PATH,
        *,
        save_outputs: bool = True,
    ) -> dict[str, Any]:
        """Run the complete Module 5 → Module 6 pipeline."""

        best_scenario_document = self._load_json(
            best_scenario_path
        )

        recommendation_document = self._load_json(
            recommendations_path
        )

        if not isinstance(
            best_scenario_document,
            Mapping,
        ):
            raise ValueError(
                "best scenario JSON must contain an object"
            )

        if not isinstance(
            recommendation_document,
            Mapping,
        ):
            raise ValueError(
                "recommendations JSON must contain an object"
            )

        best_scenario = self._extract_best_scenario(
            best_scenario_document
        )

        recommendations = self._extract_recommendations(
            recommendation_document
        )

        if not recommendations:
            raise ValueError(
                "Module 4 recommendations must not be empty"
            )

        system_state = self._build_system_state(
            best_scenario
        )

        # ----------------------------------------------------------
        # Build optimization problem
        # ----------------------------------------------------------

        problem = self.optimizer.build_problem(
            best_scenario,
            recommendations,
            system_state=system_state,
        )

        # ----------------------------------------------------------
        # Run optimization
        # ----------------------------------------------------------

        result: OptimizationResult = self.optimizer.optimize(
            problem
        )

        # ----------------------------------------------------------
        # Generate recommendations
        # ----------------------------------------------------------

        documents = (
            self.recommendation_engine.build_documents(
                result
            )
        )

        output_files: dict[str, str] = {}

        if save_outputs:
            paths = self.recommendation_engine.write_outputs(
                result,
                self.output_directory,
            )

            output_files = {
                name: str(path)
                for name, path in paths.items()
            }

        return {
            "module": "Module 6 - Optimization Engine",
            "best_scenario": best_scenario,
            "input_summary": {
                "best_scenario_path": str(
                    Path(best_scenario_path).resolve()
                ),
                "recommendations_path": str(
                    Path(recommendations_path).resolve()
                ),
                "recommendation_count": len(
                    recommendations
                ),
            },
            "optimization_problem": problem,
            "optimization_result": result,
            "optimized_state": documents["optimized_state"],
            "recommendations": documents["recommendations"],
            "report": documents["report"],
            "output_files": output_files,
        }


def main() -> int:
    controller = OptimizationController()

    result = controller.run()

    report = result["report"]

    print("=" * 64)
    print("Module 6 - Optimization Engine")
    print("Module 4/5 → Module 6 Integration")
    print("=" * 64)

    print(
        f"Best scenario: "
        f"{result['best_scenario']['name']}"
    )

    print(
        f"Optimization feasible: "
        f"{report['summary']['feasible']}"
    )

    print(
        f"Recommendations generated: "
        f"{report['summary']['recommendation_count']}"
    )

    print("\nOutput files:")

    for name, path in result["output_files"].items():
        print(f"  {name}: {path}")

    print("=" * 64)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())