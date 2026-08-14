"""AsyncSubprocessExecutor — C09 real process executor.

Executes a fixed external CLI via ``asyncio.create_subprocess_exec`` (never
``shell=True``), with an environment-variable allowlist, fixed cwd, optional
timeout, and whole-process-tree cancellation. Captures stdout/stderr up to a
soft cap and returns a structured ``ProcessResult``.

Platform notes:
- Linux/macOS: start the child in a new session (``start_new_session=True``) and
  kill the whole process group with ``os.killpg``.
- Windows: there is no process-group equivalent; kill the tree with
  ``taskkill /T /F /PID <pid>`` (matches the C08 spike finding — git-bash ``$!``
  is unreliable, but the real PID from ``asyncio`` subprocess is correct).
"""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import sys
import time
from typing import Any

from app.agents.executor import (
    AsyncLineCallback,
    DEFAULT_OUTPUT_LIMIT_BYTES,
    ProcessResult,
    ProcessStatus,
)

# Minimal env vars the child needs to be functional even under an allowlist.
# We add these to approved_env so the program can be found and the OS works,
# but we do NOT copy the parent's whole environment.
if sys.platform == "win32":
    _ESSENTIAL_ENV = ("PATH", "SystemRoot", "TEMP", "TMP")
else:
    _ESSENTIAL_ENV = ("PATH", "HOME", "TEMP", "TMP")


class AsyncSubprocessExecutor:
    """Runs one external command with an env allowlist and tree-cancel."""

    def __init__(self, *, output_limit_bytes: int = DEFAULT_OUTPUT_LIMIT_BYTES) -> None:
        self._output_limit = output_limit_bytes
        self._cancel_requested = False
        self._proc: asyncio.subprocess.Process | None = None

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
        self._cancel_requested = False
        self._proc = None

        # Build the child env: only approved vars + the minimal essentials (taken
        # from the parent's env, not from arbitrary frontend input).
        env: dict[str, str] = {}
        for key in _ESSENTIAL_ENV:
            value = os.environ.get(key)
            if value is not None:
                env[key] = value
        env.update(approved_env)

        start = time.monotonic()
        kwargs: dict[str, Any] = {
            "cwd": cwd,
            "env": env,
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
        }
        # New session on POSIX so we can kill the whole group. Ignored on Windows.
        if sys.platform != "win32":
            kwargs["start_new_session"] = True

        self._proc = await asyncio.create_subprocess_exec(command, *arguments, **kwargs)

        stdout_buf = bytearray()
        stderr_buf = bytearray()
        truncated = False

        async def drain(
            stream: asyncio.StreamReader,
            buf: bytearray,
            callback: AsyncLineCallback | None,
        ) -> None:
            nonlocal truncated
            pending = bytearray()
            while True:
                chunk = await stream.read(8192)
                if not chunk:
                    break
                if len(chunk) >= self._output_limit:
                    buf[:] = chunk[-self._output_limit :]
                    truncated = True
                elif len(buf) + len(chunk) <= self._output_limit:
                    buf.extend(chunk)
                else:
                    overflow = len(buf) + len(chunk) - self._output_limit
                    del buf[:overflow]
                    buf.extend(chunk)
                    truncated = True
                if callback is not None:
                    pending.extend(chunk)
                    while True:
                        newline = pending.find(b"\n")
                        if newline < 0:
                            break
                        raw_line = bytes(pending[:newline])
                        del pending[: newline + 1]
                        await callback(raw_line.rstrip(b"\r").decode("utf-8", errors="replace"))
            if callback is not None and pending:
                await callback(bytes(pending).rstrip(b"\r").decode("utf-8", errors="replace"))

        drain_out = asyncio.ensure_future(drain(self._proc.stdout, stdout_buf, on_stdout_line))
        drain_err = asyncio.ensure_future(drain(self._proc.stderr, stderr_buf, on_stderr_line))
        process_wait = asyncio.ensure_future(self._proc.wait())

        async def wait_for_completion() -> int:
            done, _pending = await asyncio.wait(
                {process_wait, drain_out, drain_err},
                return_when=asyncio.FIRST_EXCEPTION,
            )
            for task in (drain_out, drain_err):
                if task in done and not task.cancelled() and task.exception() is not None:
                    error = task.exception()
                    await self._kill_tree()
                    await asyncio.gather(process_wait, drain_out, drain_err, return_exceptions=True)
                    assert error is not None
                    raise error
            exit_status = await process_wait
            await asyncio.gather(drain_out, drain_err)
            return exit_status

        process_status: ProcessStatus = "completed"
        exit_code: int | None = None
        try:
            if timeout is None:
                exit_code = await wait_for_completion()
            else:
                exit_code = await asyncio.wait_for(wait_for_completion(), timeout=timeout)
        except asyncio.TimeoutError:
            process_status = "timed_out"
            await self._kill_tree()
            exit_code = self._proc.returncode  # likely None or signal
        except asyncio.CancelledError:
            # The test harness may cancel our task; ensure the tree dies too.
            process_status = "cancelled"
            await self._kill_tree()
            raise
        finally:
            # If cancel() was called externally, the proc may still be alive.
            if process_status == "completed" and self._cancel_requested:
                process_status = "cancelled"
                await self._kill_tree()
                exit_code = self._proc.returncode

        # Make sure all child-facing tasks finish after timeout or cancellation.
        await asyncio.gather(process_wait, drain_out, drain_err, return_exceptions=True)

        duration = time.monotonic() - start
        return ProcessResult(
            stdout=stdout_buf.decode("utf-8", errors="replace"),
            stderr=stderr_buf.decode("utf-8", errors="replace"),
            exit_code=exit_code,
            process_status=process_status,
            duration_seconds=duration,
            output_truncated=truncated,
        )

    async def cancel(self) -> None:
        """Cancel the in-flight run: kill the whole process tree."""
        self._cancel_requested = True
        if self._proc is not None and self._proc.returncode is None:
            await self._kill_tree()

    async def _kill_tree(self) -> None:
        proc = self._proc
        if proc is None or proc.returncode is not None:
            return
        pid = proc.pid
        if sys.platform == "win32":
            # taskkill /T /F: kill the tree rooted at pid.
            kill = await asyncio.create_subprocess_exec(
                "taskkill", "/T", "/F", "/PID", str(pid),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await kill.wait()
        else:
            try:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except ProcessLookupError:
                # Already gone — nothing to do.
                pass
        # Reap so the process doesn't linger as a zombie.
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            pass
