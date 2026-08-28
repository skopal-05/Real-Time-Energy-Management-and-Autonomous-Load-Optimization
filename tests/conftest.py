"""Shared fixtures.

The end-to-end pipeline runs the seven modules as subprocesses and takes about
20 seconds, so it runs once per test session and every test that needs module
output shares the resulting snapshot.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from enertwin.orchestration import Snapshot, run_pipeline  # noqa: E402


@pytest.fixture(scope="session")
def snapshot() -> Snapshot:
    """One end-to-end run of Modules 1-7."""

    return run_pipeline(twin_steps=96)


@pytest.fixture(scope="session")
def client(snapshot: Snapshot):
    """A TestClient whose store already holds the session snapshot.

    The app's own start-up would launch another pipeline run; seeding the store
    first means the API is exercised against the same artifacts every other test
    sees.
    """

    from fastapi.testclient import TestClient

    from enertwin.api.app import app
    from enertwin.orchestration import store

    store._snapshot = snapshot  # noqa: SLF001 - deliberate test seam

    with TestClient(app) as test_client:
        yield test_client
