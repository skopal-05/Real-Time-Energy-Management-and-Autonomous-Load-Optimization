"""Execute a module without importing it into the platform process.

Why subprocesses
----------------
The seven modules were each written to run with their own folder as the working
directory: they import top-level packages such as ``common``, ``integration``,
``contracts`` and ``intelligence``. Several of those names are reused by more
than one module with different contents — ``Module 2/common`` and
``Module 3/common`` are unrelated packages that share a name, and modules 4, 5
and 6 each ship a different ``contracts``.

Importing them side by side in one interpreter would therefore require renaming
packages inside the modules, which is exactly what must not happen. Running each
module in its own process, with its own folder on ``sys.path``, reproduces the
environment each module was developed and tested in, byte for byte.
"""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from enertwin.config import (
    MODULE_ROOTS,
    MODULE_TIMEOUT_SECONDS,
    PROJECT_ROOT,
    module_python,
)


@dataclass(frozen=True)
class ProcessResult:
    """Outcome of one module execution."""

    module: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out

    def failure_reason(self) -> str:
        if self.timed_out:
            return f"timed out after {MODULE_TIMEOUT_SECONDS}s"
        tail = (self.stderr or self.stdout or "").strip().splitlines()
        if not tail:
            return f"exited with code {self.returncode}"
        return tail[-1][:400]

    def as_dict(self) -> dict[str, object]:
        return {
            "module": self.module,
            "command": self.command,
            "returncode": self.returncode,
            "duration_seconds": round(self.duration_seconds, 3),
            "timed_out": self.timed_out,
            "stdout_tail": _tail(self.stdout),
            "stderr_tail": _tail(self.stderr),
        }


@dataclass
class ModuleProcessError(RuntimeError):
    """Raised when a module subprocess fails."""

    result: ProcessResult
    message: str = field(default="")

    def __post_init__(self) -> None:
        self.message = (
            f"{self.result.module} failed: {self.result.failure_reason()}"
        )
        super().__init__(self.message)


def _tail(text: str, lines: int = 25) -> str:
    if not text:
        return ""
    return "\n".join(text.strip().splitlines()[-lines:])


def run_module(
    module_key: str,
    script: str | Path,
    *,
    args: Sequence[str] = (),
    env: dict[str, str] | None = None,
    timeout: int | None = None,
    check: bool = True,
) -> ProcessResult:
    """Run ``script`` with the module's folder as the working directory.

    ``script`` is either a path relative to the module root (that is how the
    modules run themselves, e.g. ``integration/scenario_controller.py``) or an
    absolute path to a platform driver in ``enertwin/adapters/drivers``. Both
    execute with the module root as cwd and as ``sys.path[0]``, which is what
    the modules' imports assume.
    """

    root = MODULE_ROOTS[module_key]
    if not root.is_dir():
        raise FileNotFoundError(f"module folder is missing: {root}")

    script_path = Path(script)
    if not script_path.is_absolute():
        script_path = root / script_path
    if not script_path.is_file():
        raise FileNotFoundError(f"entry point is missing: {script_path}")

    command = [module_python(), str(script_path), *args]

    child_env = os.environ.copy()
    # The module root comes first, so the module's own packages always win.
    # The project root follows so platform drivers can import ``enertwin``;
    # it holds no top-level Python modules that could shadow a module's.
    child_env["PYTHONPATH"] = os.pathsep.join(
        [str(root), str(PROJECT_ROOT), child_env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    # Keep module stdout unbuffered so a hung run still shows progress.
    child_env["PYTHONUNBUFFERED"] = "1"
    if env:
        child_env.update(env)

    started = time.perf_counter()
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            cwd=str(root),
            env=child_env,
            capture_output=True,
            text=True,
            timeout=timeout or MODULE_TIMEOUT_SECONDS,
        )
        returncode = completed.returncode
        stdout, stderr = completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as expired:
        timed_out = True
        returncode = -1
        stdout = expired.stdout or ""
        stderr = expired.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")

    result = ProcessResult(
        module=module_key,
        command=command,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=time.perf_counter() - started,
        timed_out=timed_out,
    )

    if check and not result.ok:
        raise ModuleProcessError(result)
    return result
