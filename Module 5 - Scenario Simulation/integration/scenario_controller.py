"""End-to-end controller for Module 5 scenario simulation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ranking import ScenarioEvaluator, ScenarioRanker
from scenario_generator import ScenarioGenerator
from integration.scenario_validator import IntegrationValidator


MODULE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = MODULE_ROOT.parent
DEFAULT_FORECAST_PATH = (
    PROJECT_ROOT / "Module 3 - Forecasting" / "outputs" / "forecast_output.json"
)
DEFAULT_RECOMMENDATIONS_PATH = (
    PROJECT_ROOT
    / "Module 4 - Multi-Agent Intelligence"
    / "outputs"
    / "recommendations"
    / "recommendations.json"
)


class ScenarioController:
    """Load upstream outputs, execute Module 5, and persist its artifacts."""

    def __init__(
        self,
        output_directory: str | Path | None = None,
        *,
        generator: ScenarioGenerator | None = None,
        evaluator: ScenarioEvaluator | None = None,
        ranker: ScenarioRanker | None = None,
        validator: IntegrationValidator | None = None,
    ) -> None:
        self.output_directory = Path(output_directory or MODULE_ROOT / "outputs")
        self.generator = generator or ScenarioGenerator()
        self.evaluator = evaluator or ScenarioEvaluator()
        self.ranker = ranker or ScenarioRanker()
        self.validator = validator or IntegrationValidator()

    @staticmethod
    def _load_json(path: str | Path) -> Any:
        source = Path(path)
        if not source.is_file():
            raise FileNotFoundError(f"input file not found: {source}")
        with source.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def run(
        self,
        forecast_path: str | Path = DEFAULT_FORECAST_PATH,
        recommendations_path: str | Path = DEFAULT_RECOMMENDATIONS_PATH,
        *,
        horizon_hours: float = 1.0,
        save_outputs: bool = True,
    ) -> dict[str, Any]:
        forecast = self._load_json(forecast_path)
        recommendation_document = self._load_json(recommendations_path)
        if not isinstance(forecast, Mapping):
            raise ValueError("forecast JSON must contain an object")
        if not isinstance(recommendation_document, Mapping):
            raise ValueError("recommendations JSON must contain an object")
        recommendations = recommendation_document.get("recommendations", [])
        if not isinstance(recommendations, list):
            raise ValueError("recommendations must be an array")
        self.validator.require_valid(
            self.validator.validate_forecast(forecast), "forecast"
        )
        self.validator.require_valid(
            self.validator.validate_recommendations(recommendations), "recommendations"
        )

        scenarios = self.generator.generate(
            forecast, recommendations, horizon_hours=horizon_hours
        )
        ranked = self.ranker.rank(self.evaluator.evaluate(scenarios))
        self.validator.require_valid(self.validator.validate_results(ranked), "results")
        generated_at = datetime.now(timezone.utc).isoformat()
        best = ranked[0]
        report = {
            "generated_at": generated_at,
            "module": "Module 5 - Generative Scenario Simulation",
            "horizon_hours": horizon_hours,
            "input_summary": {
                "forecast_path": str(Path(forecast_path).resolve()),
                "recommendations_path": str(Path(recommendations_path).resolve()),
                "recommendation_count": len(recommendations),
            },
            "ranking_weights": self.ranker.weights,
            "scenario_count": len(ranked),
            "best_scenario_id": best.scenario.scenario_id,
            "best_scenario_name": best.scenario.name,
            "best_score": best.score,
            "baseline_comparison": {
                "energy_saving_kwh": best.energy["energy_saving_kwh"],
                "cost_saving_inr": best.cost["cost_saving_inr"],
                "emissions_avoided_kg_co2e": best.carbon[
                    "emissions_avoided_kg_co2e"
                ],
            },
            "status": "completed",
        }
        result = {
            "generated_at": generated_at,
            "scenarios": [item.as_dict() for item in ranked],
            "best_scenario": best.as_dict(),
            "report": report,
        }
        if save_outputs:
            result["output_files"] = self._save(result)
        return result

    def _save(self, result: Mapping[str, Any]) -> dict[str, str]:
        locations = {
            "scenarios": self.output_directory / "scenarios" / "generated_scenarios.json",
            "comparisons": self.output_directory / "comparisons" / "scenario_comparison.json",
            "best_scenario": self.output_directory / "best_scenario" / "best_scenario.json",
            "report": self.output_directory / "reports" / "simulation_report.json",
        }
        documents = {
            "scenarios": {
                "generated_at": result["generated_at"],
                "scenario_count": len(result["scenarios"]),
                "scenarios": result["scenarios"],
            },
            "comparisons": {
                "generated_at": result["generated_at"],
                "ranking_weights": result["report"]["ranking_weights"],
                "ranked_scenarios": result["scenarios"],
            },
            "best_scenario": {
                "generated_at": result["generated_at"],
                "best_scenario": result["best_scenario"],
            },
            "report": result["report"],
        }
        for key, path in locations.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as handle:
                json.dump(documents[key], handle, indent=4, ensure_ascii=False)
        return {key: str(path) for key, path in locations.items()}


def main() -> int:
    result = ScenarioController().run()
    report = result["report"]
    print("Module 5 scenario simulation completed")
    print(f"Scenarios evaluated: {report['scenario_count']}")
    print(f"Best scenario: {report['best_scenario_name']}")
    print(f"Weighted score: {report['best_score']:.2f}/100")
    for label, path in result["output_files"].items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
