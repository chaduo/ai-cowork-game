"""Process execution primitive for the OpenGame adapter (C09).

A leaf module: it executes a fixed external CLI with an explicit argument
list, a fixed working directory, an environment-variable allowlist, and an
optional timeout. It kills the whole child process tree on timeout or cancel
and never reports a killed process as completed.

It deliberately imports no Project / GameSpec / Candidate / Playable / Vue /
FastAPI repository types — it is consumed by the OpenGameAdapter (C10), which
maps ``ProcessResult`` onto the provider-neutral ``GameBuildResult`` contract.

Contract source of truth:
- ``specs/001-game-creation-mvp/contracts/game-agent-adapter.md`` —
  ``asyncio.create_subprocess_exec`` (no ``shell=True``), explicit args, fixed
  cwd, env allowlist, timeout, process-group cancellation.
- ``backend/app/contracts/game_agent.py`` — ``GameBuildStatus`` semantics the
  adapter maps onto (C09 only produces ``process_status``; C10 does the mapping).
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Awaitable, Callable
from typing import Literal, Protocol

# C09 distinguishes process termination cause. C10 maps these onto GameBuildStatus:
#   completed + exit 0      -> succeeded
#   completed + exit != 0   -> failed (provider_failed)
#   timed_out               -> timed_out (timeout)
#   cancelled               -> cancelled (cancelled)
# timed_out vs cancelled cannot be read from the process stream — the executor
# knows which trigger fired (deadline reached vs an explicit cancel() call).
ProcessStatus = Literal["completed", "timed_out", "cancelled"]
AsyncLineCallback = Callable[[str], Awaitable[None]]


class ExecutorBusyError(RuntimeError):
    """Raised when one executor instance is asked to own two active runs."""

# Soft cap on captured stdout/stderr to bound memory. Anything beyond is truncated
# and flagged via ``ProcessResult.output_truncated`` so the adapter can surface a
# diagnostic without carrying an unbounded buffer.
DEFAULT_OUTPUT_LIMIT_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class ProcessResult:
    """Structured outcome of running one external command.

    ``stdout``/``stderr`` are the captured streams (truncated above the limit).
    ``exit_code`` is ``None`` when the process was killed before it could exit
    naturally (timeout/cancel). ``process_status`` is the authoritative cause;
    callers must not infer success from ``exit_code is not None`` alone.
    """

    stdout: str
    stderr: str
    exit_code: int | None
    process_status: ProcessStatus
    duration_seconds: float
    output_truncated: bool = False


class ProcessExecutor(Protocol):
    """Executes one fixed external command with an env allowlist and tree-cancel."""

    async def run(
        self,
        *,
        command: str,
        arguments: list[str],
        cwd: str,
        approved_env: dict[str, str],
        timeout: float | None,
        on_stdout_line: AsyncLineCallback | None = None,
        on_stderr_line: AsyncLineCallback | None = None,
    ) -> ProcessResult:
        """Run ``command arguments`` in ``cwd`` with only ``approved_env``.

        ``command`` is a single program path/name; ``arguments`` is an explicit
        list — never a shell string. ``approved_env`` is the exact environment the
        child receives (plus a minimal set the executor adds so the program can be
        found); the parent's other environment variables are NOT inherited. If
        ``timeout`` elapses, the whole process tree is killed and ``process_status``
        is ``timed_out``.
        """
        ...

    async def cancel(self) -> None:
        """Cancel the in-flight run: kill the whole process tree.

        A subsequent ``run`` result has ``process_status="cancelled"``.
        """
        ...
