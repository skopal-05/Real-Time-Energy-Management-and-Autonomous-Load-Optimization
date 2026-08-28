"""The guard rail: the seven modules must never be modified.

This is the test that matters most in this repository. Everything else can be
rewritten; the modules cannot. It fails if any tracked file inside a module
folder differs from HEAD, with one deliberate exception: the ``outputs/``
folders, which the modules themselves rewrite every time they run.

Run it after any change to the integration layer, and in CI.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODULE_FOLDERS = [
    "Module 1 - Data Acquisition",
    "Module 2 - Digital Twin",
    "Module 3 - Forecasting",
    "Module 4 - Multi-Agent Intelligence",
    "Module 5 - Scenario Simulation",
    "Module 6 - Optimization Engine",
    "Module 7 - Explainable AI & Performance Evaluation",
]

#: Module changes the project owner has explicitly approved, with the reason.
#:
#: This list exists so an authorised change stays visible and auditable instead
#: of the guard being weakened. Adding an entry requires the owner's approval;
#: it is not a developer's decision. Every module file not listed here is still
#: protected exactly as before.
APPROVED_MODULE_CHANGES: dict[str, str] = {
    "Module 6 - Optimization Engine/optimization/optimizer.py": (
        "Approved 2026-08-28. Adds one key, "
        '`"history": list(ga_result.history)`, to the algorithm dictionary '
        "Optimizer.optimize() persists. The genetic algorithm already computed "
        "and returned the per-generation best-fitness series; it was being "
        "discarded before it reached optimization_report.json, leaving the "
        "convergence chart with no data. Purely additive: no algorithm, "
        "calculation or existing output value changes. Verified that Module 6's "
        "OptimizationValidator does not inspect this dictionary, that "
        "recommendation_engine.py passes it through verbatim, that Module 6's "
        "integration_test.py reads only the 'best_fitness' and 'evaluations' "
        "keys, and that Module 7 never reads it."
    ),
}


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"git unavailable or not a repository: {result.stderr.strip()}")
    return result.stdout


def _changed_paths() -> list[str]:
    """Tracked files that differ from HEAD, staged or not."""

    paths = set()
    for args in (("diff", "--name-only"), ("diff", "--name-only", "--cached")):
        paths.update(line for line in _git(*args).splitlines() if line.strip())
    return sorted(paths)


def _in_module(path: str) -> str | None:
    for folder in MODULE_FOLDERS:
        if path.startswith(f"{folder}/"):
            return folder
    return None


def test_no_module_source_file_is_modified() -> None:
    """No file inside a module folder may change, except its own outputs."""

    offenders = []
    for path in _changed_paths():
        folder = _in_module(path)
        if folder is None:
            continue
        relative = path[len(folder) + 1 :]
        # Modules rewrite their own outputs/ every run - that is them working,
        # not the platform editing them.
        if relative.startswith("outputs/"):
            continue
        if path in APPROVED_MODULE_CHANGES:
            continue
        offenders.append(path)

    assert not offenders, (
        "The integration layer must never modify a module. These module files "
        "differ from HEAD without approval:\n  " + "\n  ".join(offenders)
    )


def test_no_unapproved_python_file_in_a_module_is_modified() -> None:
    """No module .py file may differ from HEAD unless it is on the list."""

    offenders = [
        path
        for path in _changed_paths()
        if path.endswith(".py")
        and _in_module(path) is not None
        and path not in APPROVED_MODULE_CHANGES
    ]

    assert not offenders, (
        "Unapproved module source code changed:\n  " + "\n  ".join(offenders)
    )


def test_every_approved_change_is_real_and_documented() -> None:
    """The allowlist may not accumulate stale or unexplained entries."""

    for path, reason in APPROVED_MODULE_CHANGES.items():
        assert _in_module(path), f"{path} is not inside a module folder"
        assert (PROJECT_ROOT / path).is_file(), f"approved path does not exist: {path}"
        assert len(reason) > 80, f"approval for {path} needs a real explanation"


def test_the_approved_change_is_the_only_one() -> None:
    """A tripwire on scope: exactly one module change has been approved."""

    assert len(APPROVED_MODULE_CHANGES) == 1, (
        "The number of approved module changes has grown. Each one needs the "
        f"project owner's explicit approval. Currently listed: "
        f"{sorted(APPROVED_MODULE_CHANGES)}"
    )


def test_integration_layer_lives_outside_the_modules() -> None:
    """Every platform file sits outside all seven module folders."""

    platform_files = [
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in (PROJECT_ROOT / "enertwin").rglob("*.py")
    ]
    assert platform_files, "the integration layer should contain Python files"

    inside = [path for path in platform_files if _in_module(path) is not None]
    assert not inside, (
        "Integration code must not live inside a module folder:\n  "
        + "\n  ".join(inside)
    )


def test_all_module_folders_are_present() -> None:
    for folder in MODULE_FOLDERS:
        assert (PROJECT_ROOT / folder).is_dir(), f"missing module folder: {folder}"
