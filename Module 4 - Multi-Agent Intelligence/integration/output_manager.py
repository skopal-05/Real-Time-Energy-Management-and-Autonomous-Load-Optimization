"""Output management for Module 4 recommendations and reports."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from contracts import AgentRecommendation


class OutputManager:
    """Save Module 4 intelligence outputs to structured files."""

    def __init__(
        self,
        output_directory: str | Path | None = None,
    ) -> None:
        if output_directory is None:
            output_directory = (
                Path(__file__).resolve().parent.parent
                / "outputs"
            )

        self.output_directory = Path(output_directory)

        self.recommendations_directory = (
            self.output_directory / "recommendations"
        )

        self.optimized_states_directory = (
            self.output_directory / "optimized_states"
        )

        self.reports_directory = (
            self.output_directory / "reports"
        )

        self.logs_directory = (
            self.output_directory / "logs"
        )

        self._create_directories()

    def _create_directories(self) -> None:
        """Create all required output directories."""

        for directory in (
            self.recommendations_directory,
            self.optimized_states_directory,
            self.reports_directory,
            self.logs_directory,
        ):
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    def save_recommendations(
        self,
        recommendations: Iterable[AgentRecommendation],
        filename: str = "recommendations.json",
    ) -> Path:
        """Save agent recommendations as JSON."""

        items = list(recommendations)

        data = {
            "generated_at": datetime.now().isoformat(),
            "recommendation_count": len(items),
            "recommendations": [
                recommendation.as_dict()
                for recommendation in items
            ],
        }

        path = self.recommendations_directory / filename

        self._write_json(path, data)

        return path

    def save_optimized_state(
        self,
        state: dict[str, Any],
        recommendations: Iterable[AgentRecommendation],
        filename: str = "optimized_state.json",
    ) -> Path:
        """Save the forecast state together with recommended setpoints."""

        items = list(recommendations)

        optimized_state = dict(state)

        setpoints: dict[str, Any] = {}

        for recommendation in items:
            setpoints[recommendation.agent] = (
                recommendation.setpoints
            )

        data = {
            "generated_at": datetime.now().isoformat(),
            "base_state": state,
            "recommended_setpoints": setpoints,
            "recommendation_count": len(items),
        }

        path = (
            self.optimized_states_directory
            / filename
        )

        self._write_json(path, data)

        return path

    def save_report(
        self,
        summary: dict[str, Any],
        recommendations: Iterable[AgentRecommendation],
        filename: str = "intelligence_report.json",
    ) -> Path:
        """Save a summarized intelligence report."""

        items = list(recommendations)

        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "recommendations": [
                recommendation.as_dict()
                for recommendation in items
            ],
        }

        path = self.reports_directory / filename

        self._write_json(path, report)

        return path

    def save_log(
        self,
        message: str,
        filename: str = "integration.log",
    ) -> Path:
        """Append a message to the integration log."""

        path = self.logs_directory / filename

        timestamp = datetime.now().isoformat()

        with path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                f"[{timestamp}] {message}\n"
            )

        return path

    @staticmethod
    def _write_json(
        path: Path,
        data: dict[str, Any],
    ) -> None:
        """Write formatted JSON."""

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False,
            )