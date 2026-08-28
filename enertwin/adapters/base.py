"""The integration interface every module adapter implements.

An adapter is the translation layer between one frozen module's native
interface and the platform's uniform ``run(context) -> StageResult`` contract.
Adapters may:

* execute a module's own entry point,
* execute a platform driver inside the module's working directory,
* translate data at a module boundary before handing it on.

Adapters may never edit, import-patch or monkey-patch a module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from enertwin.config import MODULE_TITLES, RUNS_DIR
from enertwin.runner import ProcessResult


@dataclass
class RunContext:
    """Everything an adapter needs to know about the run it belongs to."""

    run_id: str
    #: Platform-owned scratch directory for this run. Never inside a module.
    workspace: Path
    #: How many Module 1 rows the digital twin should advance through.
    twin_steps: int = 48
    #: ``cleaned`` or ``raw`` Module 1 dataset for the twins.
    twin_source: str = "cleaned"
    #: Scenario horizon handed to Module 5.
    horizon_hours: float = 1.0
    #: Re-run Module 1's synthetic data generation before the rest.
    regenerate_data: bool = False

    def path(self, name: str) -> Path:
        """A platform-owned file path inside this run's workspace."""

        self.workspace.mkdir(parents=True, exist_ok=True)
        return self.workspace / name

    @classmethod
    def create(cls, **kwargs: Any) -> RunContext:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return cls(run_id=run_id, workspace=RUNS_DIR / run_id, **kwargs)


@dataclass
class StageResult:
    """Outcome of running one module through its adapter."""

    module_key: str
    ok: bool
    detail: str = ""
    duration_seconds: float = 0.0
    #: The stage completed, but something in it needs an operator's attention -
    #: readings rejected, an agent erroring, an infeasible optimum. Interface
    #: translations alone are design decisions, not degradations, and do not
    #: set this.
    degraded: bool = False
    #: Notes about interface translations performed at this module's boundary.
    translations: list[str] = field(default_factory=list)
    #: Artifacts this stage produced, by logical name.
    artifacts: dict[str, str] = field(default_factory=dict)
    process: dict[str, Any] | None = None

    @property
    def title(self) -> str:
        return MODULE_TITLES[self.module_key]

    def as_dict(self) -> dict[str, Any]:
        return {
            "module": self.module_key,
            "title": self.title,
            "ok": self.ok,
            "degraded": self.degraded,
            "detail": self.detail,
            "duration_seconds": round(self.duration_seconds, 3),
            "translations": list(self.translations),
            "artifacts": dict(self.artifacts),
            "process": self.process,
        }

    @classmethod
    def from_process(
        cls,
        module_key: str,
        result: ProcessResult,
        *,
        translations: list[str] | None = None,
        artifacts: dict[str, str] | None = None,
        detail: str | None = None,
        degraded: bool = False,
    ) -> StageResult:
        """Wrap a process outcome.

        ``detail`` is a short operator-facing summary the adapter derives from
        the module's artifacts. Without one the process's last stdout line is
        used, which is a fallback rather than a display string. A failure always
        reports the failure reason instead.
        """

        if not result.ok:
            detail = result.failure_reason()
        elif detail is None:
            lines = result.stdout.strip().splitlines()
            detail = lines[-1][:300] if lines else "completed"
        return cls(
            module_key=module_key,
            ok=result.ok,
            detail=detail,
            degraded=degraded and result.ok,
            duration_seconds=result.duration_seconds,
            translations=translations or [],
            artifacts=artifacts or {},
            process=result.as_dict(),
        )


class ModuleAdapter(Protocol):
    """The uniform interface the orchestrator drives."""

    module_key: str

    def run(self, context: RunContext) -> StageResult:  # pragma: no cover - protocol
        ...


#: Directory holding the platform drivers executed inside module folders.
DRIVERS = Path(__file__).resolve().parent / "drivers"
