"""Command line entry point for the integration layer.

    python -m enertwin run      # run Modules 1-7 once and print a summary
    python -m enertwin serve    # start the API (runs the pipeline on start-up)
    python -m enertwin check    # verify the environment before either
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from enertwin import __version__
from enertwin.config import (
    ARTIFACTS,
    MODULE_ROOTS,
    MODULE_TITLES,
    PLATFORM_DATA_DIR,
    TWIN_SYNC_STEPS,
    module_python,
)


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )


def command_check(args: argparse.Namespace) -> int:
    """Verify the modules and their dependencies are where we expect."""

    ok = True
    print(f"EnerTwin integration layer {__version__}")
    print(f"interpreter: {module_python()}")
    print(f"platform data: {PLATFORM_DATA_DIR}")
    print()

    print("modules:")
    for key, root in MODULE_ROOTS.items():
        present = root.is_dir()
        ok &= present
        print(f"  [{'ok' if present else '!!'}] {MODULE_TITLES[key]:44s} {root.name}")

    print()
    print("third-party packages the modules import:")
    for package in ("numpy", "pandas", "sklearn", "joblib"):
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "?")
            print(f"  [ok] {package:10s} {version}")
        except ImportError:
            ok = False
            print(f"  [!!] {package:10s} MISSING")

    print()
    models = MODULE_ROOTS["module3"] / "models"
    joblibs = sorted(models.glob("*.joblib")) if models.is_dir() else []
    print(f"trained models: {len(joblibs)} found in {models.name}/")
    if len(joblibs) < 12:
        ok = False
        print("  [!!] expected 7 models and 5 encoders")

    cleaned = ARTIFACTS.cleaned_data_dir
    csvs = sorted(cleaned.glob("*.csv")) if cleaned.is_dir() else []
    print(f"cleaned dataset: {len(csvs)} CSV files")
    if not csvs:
        ok = False
        print("  [!!] Module 1 has produced no cleaned data")

    print()
    print("READY" if ok else "NOT READY - see the items marked [!!] above")
    return 0 if ok else 1


def command_run(args: argparse.Namespace) -> int:
    """Run the seven modules end to end."""

    from enertwin.orchestration import run_pipeline

    snapshot = run_pipeline(
        twin_steps=args.twin_steps,
        twin_source=args.twin_source,
        horizon_hours=args.horizon_hours,
        regenerate_data=args.regenerate_data,
    )

    print()
    print("=" * 72)
    for stage in snapshot.stages:
        status = "ok" if stage["ok"] else "FAILED"
        if stage["ok"] and stage.get("degraded"):
            status = "degraded"
        print(f"{stage['title']:44s} {status:9s} {stage['duration_seconds']:7.2f}s")
        print(f"    {stage['detail']}")
    print("=" * 72)

    if snapshot.translations:
        print("\nboundary translations applied:")
        for note in snapshot.translations:
            print(f"  - {note}")

    if args.json:
        Path(args.json).write_text(
            json.dumps(snapshot.as_dict(), indent=2), encoding="utf-8"
        )
        print(f"\nrun summary written to {args.json}")

    print(f"\nrun {snapshot.run_id}: {'complete' if snapshot.ok else 'INCOMPLETE'}")
    return 0 if snapshot.ok else 1


def command_serve(args: argparse.Namespace) -> int:
    """Start the API server."""

    import uvicorn

    print(f"EnerTwin API on http://{args.host}:{args.port}")
    print(f"point the frontend at http://localhost:{args.port}/api")
    uvicorn.run(
        "enertwin.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m enertwin",
        description="Integration layer for the Generative Digital Twin platform.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="verify the environment")
    check.set_defaults(handler=command_check)

    run = subparsers.add_parser("run", help="run Modules 1-7 once")
    run.add_argument(
        "--twin-steps",
        type=int,
        default=TWIN_SYNC_STEPS,
        help="intervals of Module 1 data to synchronize (default: %(default)s)",
    )
    run.add_argument(
        "--twin-source",
        choices=("cleaned", "raw"),
        default="cleaned",
        help="which Module 1 dataset feeds the twins (default: %(default)s)",
    )
    run.add_argument("--horizon-hours", type=float, default=1.0)
    run.add_argument(
        "--regenerate-data",
        action="store_true",
        help="re-run Module 1's synthetic data generation (rewrites tracked files)",
    )
    run.add_argument("--json", help="write the run summary to this path")
    run.set_defaults(handler=command_run)

    serve = subparsers.add_parser("serve", help="start the API server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8010)
    serve.add_argument("--reload", action="store_true")
    serve.set_defaults(handler=command_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _configure_logging(args.verbose)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
