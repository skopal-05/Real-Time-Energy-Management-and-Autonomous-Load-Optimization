"""Holds the current snapshot and runs the pipeline in the background.

The API never blocks on a pipeline run: requests are served from the snapshot in
memory, and a run replaces it atomically when it finishes.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable

from enertwin.orchestration.pipeline import run_pipeline
from enertwin.orchestration.snapshot import Snapshot, now_iso

logger = logging.getLogger("enertwin.store")


class SnapshotStore:
    """Thread-safe holder for the latest completed pipeline run."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._snapshot: Snapshot | None = None
        self._running = False
        self._last_error: str | None = None
        self._run_started_at: str | None = None
        self._listeners: list[Callable[[Snapshot], None]] = []

    # -- state ---------------------------------------------------------

    @property
    def snapshot(self) -> Snapshot | None:
        with self._lock:
            return self._snapshot

    def require_snapshot(self) -> Snapshot:
        snapshot = self.snapshot
        if snapshot is None:
            raise SnapshotUnavailable(
                "No pipeline run has completed yet. "
                "POST /api/pipeline/run to start one."
            )
        return snapshot

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def status(self) -> dict[str, Any]:
        with self._lock:
            snapshot = self._snapshot
            return {
                "running": self._running,
                "run_started_at": self._run_started_at,
                "last_error": self._last_error,
                "run": snapshot.as_dict() if snapshot else None,
            }

    def subscribe(self, listener: Callable[[Snapshot], None]) -> Callable[[], None]:
        """Register a callback fired after each completed run."""

        with self._lock:
            self._listeners.append(listener)

        def unsubscribe() -> None:
            with self._lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)

        return unsubscribe

    # -- running -------------------------------------------------------

    def run_now(self, **kwargs: Any) -> Snapshot:
        """Run the pipeline synchronously and publish the result."""

        with self._lock:
            if self._running:
                raise PipelineBusy("A pipeline run is already in progress.")
            self._running = True
            self._run_started_at = now_iso()
            self._last_error = None

        try:
            snapshot = run_pipeline(**kwargs)
        except Exception as error:
            with self._lock:
                self._running = False
                self._last_error = f"{type(error).__name__}: {error}"
            logger.exception("pipeline run failed")
            raise
        else:
            with self._lock:
                self._snapshot = snapshot
                self._running = False
                if not snapshot.ok:
                    failed = [s for s in snapshot.stages if not s.get("ok")]
                    self._last_error = (
                        failed[-1].get("detail") if failed else "run incomplete"
                    )
                listeners = list(self._listeners)
            for listener in listeners:
                try:
                    listener(snapshot)
                except Exception:  # a listener must never break a run
                    logger.exception("snapshot listener failed")
            return snapshot

    def run_in_background(self, **kwargs: Any) -> bool:
        """Start a run on a worker thread. Returns False when one is active."""

        with self._lock:
            if self._running:
                return False

        def worker() -> None:
            try:
                self.run_now(**kwargs)
            except Exception:
                pass  # already recorded in _last_error

        threading.Thread(target=worker, name="enertwin-pipeline", daemon=True).start()
        return True


class SnapshotUnavailable(RuntimeError):
    """Raised when the API is asked for data before any run has completed."""


class PipelineBusy(RuntimeError):
    """Raised when a second concurrent pipeline run is requested."""


class PipelineScheduler:
    """Re-runs the pipeline on a fixed interval."""

    def __init__(self, store: SnapshotStore, interval_seconds: int, **run_kwargs: Any):
        self.store = store
        self.interval_seconds = interval_seconds
        self.run_kwargs = run_kwargs
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self.interval_seconds <= 0 or self._thread is not None:
            return

        def loop() -> None:
            while not self._stop.wait(self.interval_seconds):
                started = self.store.run_in_background(**self.run_kwargs)
                if not started:
                    logger.info("scheduled run skipped: pipeline still busy")

        self._thread = threading.Thread(
            target=loop, name="enertwin-scheduler", daemon=True
        )
        self._thread.start()
        logger.info("scheduler started: every %ss", self.interval_seconds)

    def stop(self) -> None:
        self._stop.set()
        self._thread = None


#: Process-wide store used by the API.
store = SnapshotStore()
