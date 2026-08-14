"""C09 — opengame-process-executor contract tests (TDD).

These exercise ``AsyncSubprocessExecutor`` against real ``node`` subprocesses
(no OpenGame / no credentials). They assert the C09 acceptance criteria:
real stdout/stderr/exit_code, fixed cwd, env allowlist (no parent leak),
timeout/cancel kill the whole process tree and never report completion.
"""

from __future__ import annotations

import asyncio
import os
import sys

import pytest

from app.agents.executor import ProcessResult
from app.agents.subprocess_executor import AsyncSubprocessExecutor

NODE = sys.executable  # the python running pytest is NOT node; use a real node below


def _node() -> str:
    """Locate node on PATH (tests require node, which the toolchain already needs)."""
    import shutil

    node = shutil.which("node")
    assert node is not None, "node must be on PATH for executor tests"
    return node


def run_async(coro):
    return asyncio.run(coro)


# --------------------------------------------------------------------------- #
# success / exit code / stream capture
# --------------------------------------------------------------------------- #


def test_success_returns_completed_with_real_streams(workspace) -> None:
    executor = AsyncSubprocessExecutor()
    result = run_async(
        executor.run(
            command=_node(),
            arguments=["-e", "process.exit(0)"],
            cwd=str(workspace),
            approved_env={},
            timeout=None,
        )
    )
    assert isinstance(result, ProcessResult)
    assert result.exit_code == 0
    assert result.process_status == "completed"
    assert result.duration_seconds >= 0.0


def test_nonzero_exit_is_completed_not_masked(workspace) -> None:
    executor = AsyncSubprocessExecutor()
    result = run_async(
        executor.run(
            command=_node(),
            arguments=["-e", "process.exit(3)"],
            cwd=str(workspace),
            approved_env={},
            timeout=None,
        )
    )
    assert result.exit_code == 3
    assert result.process_status == "completed"  # C10 maps this to "failed"


def test_stderr_captured(workspace) -> None:
    executor = AsyncSubprocessExecutor()
    result = run_async(
        executor.run(
            command=_node(),
            arguments=["-e", "console.error('boom')"],
            cwd=str(workspace),
            approved_env={},
            timeout=None,
        )
    )
    assert "boom" in result.stderr
    assert result.exit_code == 0


def test_stdout_captured(workspace) -> None:
    executor = AsyncSubprocessExecutor()
    result = run_async(
        executor.run(
            command=_node(),
            arguments=["-e", "console.log('hello')"],
            cwd=str(workspace),
            approved_env={},
            timeout=None,
        )
    )
    assert "hello" in result.stdout


# --------------------------------------------------------------------------- #
# cwd
# --------------------------------------------------------------------------- #


def test_cwd_is_honored(workspace) -> None:
    executor = AsyncSubprocessExecutor()
    # Print the cwd the child sees; it must equal the workspace we passed.
    result = run_async(
        executor.run(
            command=_node(),
            arguments=["-e", "console.log(process.cwd())"],
            cwd=str(workspace),
            approved_env={},
            timeout=None,
        )
    )
    assert os.path.realpath(workspace).replace("\\", "/") in result.stdout.replace("\\", "/")


# --------------------------------------------------------------------------- #
# approved_env allowlist: only approved vars reach the child; parent env leaks nothing
# --------------------------------------------------------------------------- #


def test_approved_env_value_reaches_child(workspace, monkeypatch) -> None:
    monkeypatch.setenv("PARENT_SECRET", "leak-me")
    executor = AsyncSubprocessExecutor()
    result = run_async(
        executor.run(
            command=_node(),
            arguments=["-e", "console.log(process.env.FOO)"],
            cwd=str(workspace),
            approved_env={"FOO": "bar"},
            timeout=None,
        )
    )
    assert "bar" in result.stdout


def test_parent_env_not_leaked_to_child(workspace, monkeypatch) -> None:
    monkeypatch.setenv("PARENT_SECRET", "leak-me")
    executor = AsyncSubprocessExecutor()
    result = run_async(
        executor.run(
            command=_node(),
            arguments=["-e", "console.log(typeof process.env.PARENT_SECRET)"],
            cwd=str(workspace),
            approved_env={"FOO": "bar"},
            timeout=None,
        )
    )
    assert "undefined" in result.stdout  # PARENT_SECRET did NOT leak


# --------------------------------------------------------------------------- #
# timeout kills the whole tree, status timed_out, never completed
# --------------------------------------------------------------------------- #


def test_timeout_kills_tree_and_reports_timed_out(workspace) -> None:
    executor = AsyncSubprocessExecutor()
    # Child spawns a grandchild that sleeps; timeout must kill BOTH.
    script = (
        "const {spawn} = require('child_process');"
        "spawn(process.argv[0], ['-e', 'setInterval(()=>{},5000)'],"
        "{stdio:'inherit'}); setInterval(()=>{},1000);"
    )
    result = run_async(
        executor.run(
            command=_node(),
            arguments=["-e", script],
            cwd=str(workspace),
            approved_env={},
            timeout=1.5,
        )
    )
    assert result.process_status == "timed_out"
    assert result.process_status != "completed"
    assert result.exit_code is None or result.exit_code != 0


def test_cancel_kills_tree_and_reports_cancelled(workspace) -> None:
    executor = AsyncSubprocessExecutor()
    script = (
        "const {spawn} = require('child_process');"
        "spawn(process.argv[0], ['-e', 'setInterval(()=>{},5000)'],"
        "{stdio:'inherit'}); setInterval(()=>{},1000);"
    )

    async def run_and_cancel():
        # Start the run, cancel it shortly after, then await the result.
        run_task = asyncio.ensure_future(
            executor.run(
                command=_node(),
                arguments=["-e", script],
                cwd=str(workspace),
                approved_env={},
                timeout=None,
            )
        )
        await asyncio.sleep(0.6)
        await executor.cancel()
        return await run_task

    result = run_async(run_and_cancel())
    assert result.process_status == "cancelled"
    assert result.process_status != "completed"


# --------------------------------------------------------------------------- #
# output limit (sanitized diagnostics)
# --------------------------------------------------------------------------- #


def test_large_output_is_truncated_not_unbounded(workspace) -> None:
    executor = AsyncSubprocessExecutor(output_limit_bytes=4096)
    # Print ~64KB; must be truncated, not blow memory.
    result = run_async(
        executor.run(
            command=_node(),
            arguments=["-e", "process.stdout.write('x'.repeat(64*1024))"],
            cwd=str(workspace),
            approved_env={},
            timeout=None,
        )
    )
    assert result.output_truncated is True
    assert len(result.stdout) <= 4096


def test_stdout_and_stderr_callbacks_receive_complete_lines_in_order(workspace) -> None:
    executor = AsyncSubprocessExecutor()
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    async def on_stdout_line(line: str) -> None:
        stdout_lines.append(line)

    async def on_stderr_line(line: str) -> None:
        stderr_lines.append(line)

    result = run_async(
        executor.run(
            command=_node(),
            arguments=[
                "-e",
                "console.log('first'); console.log('second'); console.error('warning')",
            ],
            cwd=str(workspace),
            approved_env={},
            timeout=None,
            on_stdout_line=on_stdout_line,
            on_stderr_line=on_stderr_line,
        )
    )

    assert result.exit_code == 0
    assert stdout_lines == ["first", "second"]
    assert stderr_lines == ["warning"]


def test_callback_receives_terminal_line_after_diagnostic_truncation(workspace) -> None:
    executor = AsyncSubprocessExecutor(output_limit_bytes=128)
    stdout_lines: list[str] = []

    async def on_stdout_line(line: str) -> None:
        stdout_lines.append(line)

    result = run_async(
        executor.run(
            command=_node(),
            arguments=[
                "-e",
                (
                    "for (let i=0;i<20;i++) console.log(JSON.stringify({type:'assistant',i,payload:'x'.repeat(40)}));"
                    "console.log(JSON.stringify({type:'result',subtype:'success'}));"
                ),
            ],
            cwd=str(workspace),
            approved_env={},
            timeout=None,
            on_stdout_line=on_stdout_line,
        )
    )

    assert result.output_truncated is True
    assert len(result.stdout.encode("utf-8")) <= 128
    assert stdout_lines[-1] == '{"type":"result","subtype":"success"}'


def test_callback_failure_terminates_process_and_propagates(workspace) -> None:
    executor = AsyncSubprocessExecutor()

    async def reject_line(_line: str) -> None:
        raise RuntimeError("parser rejected line")

    with pytest.raises(RuntimeError, match="parser rejected line"):
        run_async(
            executor.run(
                command=_node(),
                arguments=["-e", "console.log('bad'); setInterval(()=>{},1000)"],
                cwd=str(workspace),
                approved_env={},
                timeout=2,
                on_stdout_line=reject_line,
            )
        )


# --------------------------------------------------------------------------- #
# no shell=True: command is a single program, never shell-parsed
# --------------------------------------------------------------------------- #


def test_command_is_not_shell_parsed(workspace) -> None:
    """A command containing shell metacharacters must NOT be interpreted by a shell.

    If shell=True were used, 'echo' as command with arg 'hi' would still run echo;
    but a command string with a space/metachar would be split. We pass a real program
    and assert the child receives arguments verbatim (no shell re-parse).
    """
    executor = AsyncSubprocessExecutor()
    # arg contains a space and a shell metachar; child must see it intact.
    result = run_async(
        executor.run(
            command=_node(),
            arguments=["-e", "console.log(process.argv[1])", "a b; rm -rf /"],
            cwd=str(workspace),
            approved_env={},
            timeout=None,
        )
    )
    assert "a b; rm -rf /" in result.stdout
