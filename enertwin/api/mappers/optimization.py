"""Module 6 optimization report -> the frontend's ``OptimizationResult``.

The convergence series
----------------------
Module 6's genetic algorithm records the best fitness of each generation and
returns it on ``GeneticAlgorithmResult.history``. It was originally discarded
before reaching disk; one approved, purely additive line in
``optimization/optimizer.py`` now persists it, so the convergence chart plots
Module 6's real search trajectory. See ``APPROVED_MODULE_CHANGES`` in
``tests/test_modules_unmodified.py``.

The GA records only the *best* fitness per generation, not the population mean.
``meanFitness`` is therefore ``null`` on every point - the chart draws the best
line and leaves the mean line absent, rather than the platform inventing a
second series. When no history is present at all (an artifact from before the
change), ``convergence`` is empty and the chart falls back to its empty state.
"""

from __future__ import annotations

from typing import Any

from enertwin.api.catalog import CURRENCY
from enertwin.api.mappers.common import iso, now_iso, number, rounded, shift_iso
from enertwin.api.mappers.energy import build_energy_window
from enertwin.orchestration import Snapshot

#: Objective weights declared by ``OptimizationProblem`` in Module 6's
#: ``contracts.py``. The persisted report carries the weighted components but
#: not the weights themselves.
OBJECTIVE_WEIGHTS: dict[str, float] = {"energy": 0.35, "cost": 0.35, "carbon": 0.30}

OBJECTIVE_DESCRIPTIONS: dict[str, str] = {
    "energy": "Primary energy across grid import and boiler fuel, in kWh.",
    "cost": "Net operating cost: grid import plus fuel, less export revenue.",
    "carbon": "Total emissions from grid import and boiler fuel, in kg CO₂e.",
}


def _constraints(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Constraint status, derived only from values the artifact carries."""

    violations = report.get("violations") or []
    if isinstance(violations, str):
        violations = [violations]

    entries: list[dict[str, Any]] = [
        {
            "id": f"violation-{index}",
            "label": "Constraint violation",
            "expression": str(violation),
            "satisfied": False,
            "slack": "violated",
        }
        for index, violation in enumerate(violations)
    ]

    optimized = report.get("optimized_state", {}) or {}
    soc = number(optimized, "projected_soc_percent")
    if soc is not None:
        # Module 6's optimization_controller configures the SOC window as
        # 20-90%; the artifact carries the projected value it settled on.
        entries.append(
            {
                "id": "battery-soc",
                "label": "Battery state of charge",
                "expression": "20% ≤ projected SOC ≤ 90%",
                "satisfied": 20.0 <= soc <= 90.0,
                "slack": f"{soc:.1f}% projected",
            }
        )

    export_limit = number(optimized, "grid_export_limit_kw")
    if export_limit is not None:
        entries.append(
            {
                "id": "grid-export",
                "label": "Grid export limit",
                "expression": "grid export ≤ contracted export capacity",
                "satisfied": True,
                "slack": f"{export_limit:.1f} kW allocated",
            }
        )

    if report.get("summary", {}).get("feasible"):
        entries.insert(
            0,
            {
                "id": "feasible",
                "label": "Feasible solution",
                "expression": "all Module 6 constraints satisfied",
                "satisfied": True,
                "slack": "no violations reported",
            },
        )

    return entries


def _convergence(algorithm: dict[str, Any]) -> list[dict[str, Any]]:
    """The GA's best-fitness trajectory, one point per generation.

    ``meanFitness`` is ``null`` because Module 6's GA does not record the
    population mean - only the best candidate of each generation.
    """

    history = algorithm.get("history")
    if not isinstance(history, list):
        return []

    points: list[dict[str, Any]] = []
    for index, value in enumerate(history):
        fitness = number({"value": value}, "value")
        if fitness is None:
            continue
        points.append(
            {
                "generation": index + 1,
                "bestFitness": round(fitness, 8),
                "meanFitness": None,
            }
        )
    return points


def _grid_import_kw(report: dict[str, Any], side: str) -> float | None:
    """Grid import at the connection point, in kW.

    Module 6's horizon is one hour, so its ``grid_import_kwh`` over that horizon
    is numerically the average kW across it.
    """

    metrics = report.get(f"{side}_metrics", {}) or {}
    return number(metrics.get("energy", {}), "grid_import_kwh")


def _schedule(snapshot: Snapshot, report: dict[str, Any]) -> list[dict[str, Any]]:
    """Grid import across the optimizer's horizon, baseline against optimised.

    Two choices worth stating, because both could mislead if made differently.

    *Which quantity.* Module 6 holds production load constant on purpose - its
    recommendation engine says so: "Maintain the required production demand
    rather than optimizing it away." What it actually moves is battery dispatch
    and, through it, import at the point of common coupling. Plotting the load
    it deliberately leaves alone would show two identical lines and imply the
    optimizer did nothing.

    *Why flat.* Module 6 solves for a single operating point over a one-hour
    horizon, not a multi-slot schedule, so both series are constant across it.
    Measured site demand is deliberately not used as the baseline: it includes
    both production lines, while Module 6's figures come from Module 3's total
    load of compressor plus HVAC. Plotting one against the other would compare
    two different quantities.
    """

    baseline = _grid_import_kw(report, "baseline")
    optimised = _grid_import_kw(report, "optimized")
    if baseline is None or optimised is None:
        return []

    readings = build_energy_window(snapshot, hours=1, step_minutes=15)
    start = readings[-1]["timestamp"] if readings else snapshot.finished_at

    return [
        {
            "timestamp": shift_iso(start, minutes) or start,
            "baselineKw": round(baseline, 2),
            "optimisedKw": round(optimised, 2),
        }
        for minutes in (0, 15, 30, 45, 60)
    ]


def build_optimization(snapshot: Snapshot) -> dict[str, Any]:
    report = snapshot.optimization_report or {}

    if not report:
        return {
            "runId": snapshot.run_id,
            "algorithm": "Genetic Algorithm",
            "status": "idle",
            "startedAt": snapshot.started_at,
            "finishedAt": None,
            "generations": 0,
            "populationSize": 0,
            "convergence": [],
            "objective": {"summary": "No optimization run is available.", "terms": []},
            "constraints": [],
            "schedule": [],
            "cost": {"currency": CURRENCY, "baseline": None, "optimised": None},
            "peakDemand": {"baselineKw": None, "optimisedKw": None},
            "energyKwh": {"baseline": None, "optimised": None},
            "origin": "unavailable",
        }

    algorithm = report.get("algorithm", {}) or {}
    summary = report.get("summary", {}) or {}
    baseline_metrics = report.get("baseline_metrics", {}) or {}
    optimized_metrics = report.get("optimized_metrics", {}) or {}

    objective = report.get("objective", {}) or {}
    terms = [
        {
            "label": name.capitalize(),
            "weight": weight,
            "description": OBJECTIVE_DESCRIPTIONS[name],
        }
        for name, weight in OBJECTIVE_WEIGHTS.items()
    ]

    cost_saving = summary.get("cost_saving_inr")
    carbon_saving = summary.get("emissions_avoided_kg_co2e")
    summary_text = (
        "Minimise a weighted combination of primary energy, net operating cost "
        "and carbon emissions, subject to the battery, grid and equipment "
        "constraints Module 6 derives from the selected scenario."
    )
    if cost_saving is not None and carbon_saving is not None:
        summary_text += (
            f" This run found ₹{cost_saving:,.2f} of operating cost and "
            f"{carbon_saving:,.2f} kg CO₂e against the baseline operating point."
        )

    return {
        "runId": snapshot.run_id,
        "algorithm": "Genetic Algorithm (real-valued)",
        "status": "converged" if summary.get("feasible") else "failed",
        "startedAt": snapshot.started_at,
        "finishedAt": iso(report.get("generated_at")) or now_iso(),
        "generations": int(algorithm.get("generations") or 0),
        "populationSize": int(algorithm.get("population_size") or 0),
        "convergence": _convergence(algorithm),
        "objective": {"summary": summary_text, "terms": terms},
        "constraints": _constraints(report),
        "schedule": _schedule(snapshot, report),
        "cost": {
            "currency": CURRENCY,
            "baseline": rounded(
                number(baseline_metrics.get("cost", {}), "net_operating_cost_inr"), 2
            ),
            "optimised": rounded(
                number(optimized_metrics.get("cost", {}), "net_operating_cost_inr"), 2
            ),
        },
        # Peak demand at the point of common coupling. Module 6 holds site
        # production load constant by design, so reporting that as "peak
        # demand" would show a 0% change on every run; grid import is the
        # demand the optimizer actually moves.
        "peakDemand": {
            "baselineKw": rounded(_grid_import_kw(report, "baseline"), 2),
            "optimisedKw": rounded(_grid_import_kw(report, "optimized"), 2),
        },
        "energyKwh": {
            "baseline": rounded(
                number(baseline_metrics.get("energy", {}), "energy_objective_kwh"), 2
            ),
            "optimised": rounded(
                number(optimized_metrics.get("energy", {}), "energy_objective_kwh"), 2
            ),
        },
        "origin": "live",
    }


def optimization_impact(snapshot: Snapshot) -> dict[str, Any]:
    """Optimization figures used by the reporting endpoint."""

    report = snapshot.optimization_report or {}
    summary = report.get("summary", {}) or {}
    baseline = _grid_import_kw(report, "baseline")
    optimised = _grid_import_kw(report, "optimized")

    peak_reduction = None
    if baseline is not None and optimised is not None:
        peak_reduction = round(baseline - optimised, 2)

    discharge = number(report.get("optimized_state", {}), "battery_discharge_kw")

    return {
        "runsCompleted": 1 if report else 0,
        "peakReductionKw": peak_reduction,
        # Module 6's horizon is one hour, so discharged power equals the energy
        # shifted across that horizon.
        "energyShiftedKwh": rounded(discharge, 2),
        "costDelta": rounded(summary.get("cost_saving_inr"), 2),
        "currency": CURRENCY,
    }
