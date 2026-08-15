"""C09 — opengame-process-executor contract tests (TDD).

These exercise ``AsyncSubprocessExecutor`` against real ``node`` subprocesses
(no OpenGame / no credentials). They assert the C09 acceptance criteria:
real stdout/stderr/exit_code, fixed cwd, env allowlist (no parent leak),
timeout/cancel kill the whole process tree and never report completion.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

import pytest

from app.agents.executor import ExecutorBusyError, OutputLineTooLongError, ProcessResult
from app.agents.subprocess_executor import AsyncSubprocessExecutor
from app.agents import subprocess_executor as subprocess_executor_module

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


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX process-group regression")
def test_kill_tree_terminates_descendant_after_process_group_leader_exits(workspace) -> None:
    executor = AsyncSubprocessExecutor()
    marker = workspace / "descendant-survived"
    pid_file = workspace / "descendant-pid"
    descendant = f"setTimeout(() => require('fs').writeFileSync({json.dumps(str(marker))}, 'alive'), 3000)"
    parent = (
        "const {spawn}=require('child_process'); const fs=require('fs');"
        f"const child=spawn(process.argv[0], ['-e', {json.dumps(descendant)}], {{stdio:'inherit'}});"
        f"fs.writeFileSync({json.dumps(str(pid_file))}, String(child.pid));"
        "child.unref(); process.exit(0);"
    )

    async def scenario() -> ProcessResult:
        run_task = asyncio.create_task(
            executor.run(
                command=_node(),
                arguments=["-e", parent],
                cwd=str(workspace),
                approved_env={},
                timeout=None,
            )
        )
        while executor._proc is None:
            await asyncio.sleep(0.01)
        while executor._proc.returncode is None:
            await asyncio.sleep(0.01)
        assert executor._proc.returncode == 0
        assert not run_task.done()
        assert executor._process_group_id is not None
        descendant_pid = int(pid_file.read_text())
        assert os.getpgid(descendant_pid) == executor._process_group_id
        await executor._kill_tree()
        return await asyncio.wait_for(run_task, timeout=4)

    result = run_async(scenario())
    assert result.process_status == "completed"
    assert result.exit_code == 0
    assert not marker.exists()


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


def test_cancel_requested_during_spawn_is_not_lost(workspace, monkeypatch) -> None:
    executor = AsyncSubprocessExecutor()
    real_create = subprocess_executor_module.asyncio.create_subprocess_exec

    async def scenario() -> ProcessResult:
        spawn_started = asyncio.Event()
        allow_spawn = asyncio.Event()

        async def delayed_create(*args, **kwargs):
            spawn_started.set()
            await allow_spawn.wait()
            return await real_create(*args, **kwargs)

        monkeypatch.setattr(
            subprocess_executor_module.asyncio,
            "create_subprocess_exec",
            delayed_create,
        )
        run_task = asyncio.create_task(
            executor.run(
                command=_node(),
                arguments=["-e", "setInterval(()=>{},1000)"],
                cwd=str(workspace),
                approved_env={},
                timeout=None,
            )
        )
        await spawn_started.wait()
        await executor.cancel()
        allow_spawn.set()
        return await asyncio.wait_for(run_task, timeout=2)

    result = run_async(scenario())
    assert result.process_status == "cancelled"


def test_second_concurrent_run_is_rejected_without_replacing_active_process(workspace) -> None:
    executor = AsyncSubprocessExecutor()

    async def scenario() -> ProcessResult:
        first = asyncio.create_task(
            executor.run(
                command=_node(),
                arguments=["-e", "setInterval(()=>{},1000)"],
                cwd=str(workspace),
                approved_env={},
                timeout=None,
            )
        )
        await asyncio.sleep(0.2)
        with pytest.raises(ExecutorBusyError):
            await executor.run(
                command=_node(),
                arguments=["-e", "process.exit(0)"],
                cwd=str(workspace),
                approved_env={},
                timeout=None,
            )
        await executor.cancel()
        return await asyncio.wait_for(first, timeout=2)

    result = run_async(scenario())
    assert result.process_status == "cancelled"


def test_cancel_after_natural_completion_does_not_rewrite_result(workspace) -> None:
    executor = AsyncSubprocessExecutor()

    async def scenario() -> ProcessResult:
        result = await executor.run(
            command=_node(),
            arguments=["-e", "process.exit(0)"],
            cwd=str(workspace),
            approved_env={},
            timeout=None,
        )
        await executor.cancel()
        return result

    result = run_async(scenario())
    assert result.process_status == "completed"
    assert result.exit_code == 0


def test_cancel_after_process_exit_does_not_interrupt_callback_drain(workspace) -> None:
    executor = AsyncSubprocessExecutor()

    async def scenario() -> tuple[ProcessResult, list[str]]:
        callback_started = asyncio.Event()
        release_callback = asyncio.Event()
        lines: list[str] = []

        async def slow_callback(line: str) -> None:
            callback_started.set()
            await release_callback.wait()
            lines.append(line)

        run_task = asyncio.create_task(
            executor.run(
                command=_node(),
                arguments=["-e", "console.log('finished')"],
                cwd=str(workspace),
                approved_env={},
                timeout=None,
                on_stdout_line=slow_callback,
            )
        )
        await callback_started.wait()
        while executor._proc is not None and executor._proc.returncode is None:
            await asyncio.sleep(0.01)
        await executor.cancel()
        release_callback.set()
        return await run_task, lines

    result, lines = run_async(scenario())
    assert result.process_status == "completed"
    assert result.exit_code == 0
    assert lines == ["finished"]


def test_windows_taskkill_failure_falls_back_to_direct_kill(monkeypatch) -> None:
    executor = AsyncSubprocessExecutor()

    class OwnedProcess:
        pid = 123
        returncode = None
        kill_called = False

        def kill(self) -> None:
            self.kill_called = True
            self.returncode = -9

        async def wait(self) -> int:
            return self.returncode or 0

    class FailedTaskkill:
        returncode = 1

        async def wait(self) -> int:
            return self.returncode

    owned = OwnedProcess()

    async def fake_create(*_args, **_kwargs):
        return FailedTaskkill()

    executor._proc = owned  # type: ignore[assignment]
    monkeypatch.setattr(subprocess_executor_module.sys, "platform", "win32")
    monkeypatch.setattr(
        subprocess_executor_module.asyncio,
        "create_subprocess_exec",
        fake_create,
    )

    run_async(executor._kill_tree())

    assert owned.kill_called is True


def test_windows_missing_taskkill_falls_back_to_direct_kill(monkeypatch) -> None:
    executor = AsyncSubprocessExecutor()

    class OwnedProcess:
        pid = 123
        returncode = None
        kill_called = False

        def kill(self) -> None:
            self.kill_called = True
            self.returncode = -9

        async def wait(self) -> int:
            return self.returncode or 0

    owned = OwnedProcess()

    async def missing_taskkill(*_args, **_kwargs):
        raise FileNotFoundError("taskkill not found")

    executor._proc = owned  # type: ignore[assignment]
    monkeypatch.setattr(subprocess_executor_module.sys, "platform", "win32")
    monkeypatch.setattr(
        subprocess_executor_module.asyncio,
        "create_subprocess_exec",
        missing_taskkill,
    )

    run_async(executor._kill_tree())

    assert owned.kill_called is True


def test_windows_job_terminates_descendants_after_root_exit(monkeypatch) -> None:
    executor = AsyncSubprocessExecutor()

    class ExitedProcess:
        pid = 123
        returncode = 0

        async def wait(self) -> int:
            return 0

    class OwnedJob:
        terminate_called = False

        def terminate(self) -> None:
            self.terminate_called = True

    job = OwnedJob()
    executor._proc = ExitedProcess()  # type: ignore[assignment]
    executor._windows_job = job  # type: ignore[assignment]
    monkeypatch.setattr(subprocess_executor_module.sys, "platform", "win32")

    run_async(executor._kill_tree())

    assert job.terminate_called is True


def test_windows_child_is_suspended_until_job_is_attached(workspace, monkeypatch) -> None:
    events: list[str] = []

    class EmptyProcess:
        pid = 123
        returncode = 0

        def __init__(self) -> None:
            self.stdout = asyncio.StreamReader()
            self.stderr = asyncio.StreamReader()
            self.stdout.feed_eof()
            self.stderr.feed_eof()

        async def wait(self) -> int:
            events.append("wait")
            return 0

    class OwnedJob:
        def terminate(self) -> None:
            events.append("terminate")

        def close(self) -> None:
            events.append("close")

    async def fake_create(*_args, **kwargs):
        assert kwargs["creationflags"] & 0x00000004
        events.append("spawn-suspended")
        return EmptyProcess()

    def fake_attach(pid: int):
        assert pid == 123
        events.append("attach-job")
        return OwnedJob()

    def fake_resume(pid: int) -> None:
        assert pid == 123
        events.append("resume")

    monkeypatch.setattr(subprocess_executor_module.sys, "platform", "win32")
    monkeypatch.setattr(
        subprocess_executor_module.asyncio,
        "create_subprocess_exec",
        fake_create,
    )
    monkeypatch.setattr(subprocess_executor_module.WindowsJob, "attach", fake_attach)
    monkeypatch.setattr(subprocess_executor_module, "resume_windows_process", fake_resume)

    result = run_async(
        AsyncSubprocessExecutor().run(
            command="node",
            arguments=["--help"],
            cwd=str(workspace),
            approved_env={},
            timeout=None,
        )
    )

    assert result.process_status == "completed"
    assert events[:3] == ["spawn-suspended", "attach-job", "resume"]


def test_windows_cancel_during_spawn_never_resumes_child(workspace, monkeypatch) -> None:
    events: list[str] = []
    spawn_started: asyncio.Event
    allow_spawn: asyncio.Event

    class SuspendedProcess:
        pid = 123
        returncode: int | None = None

        def __init__(self) -> None:
            self.stdout = asyncio.StreamReader()
            self.stderr = asyncio.StreamReader()
            self.stdout.feed_eof()
            self.stderr.feed_eof()

        async def wait(self) -> int:
            while self.returncode is None:
                await asyncio.sleep(0.01)
            return self.returncode

        def kill(self) -> None:
            self.returncode = -9

    process: SuspendedProcess

    class OwnedJob:
        def terminate(self) -> None:
            events.append("terminate")
            process.returncode = -9

        def close(self) -> None:
            events.append("close")

    async def fake_create(*_args, **kwargs):
        assert kwargs["creationflags"] & 0x00000004
        events.append("spawn-started")
        spawn_started.set()
        await allow_spawn.wait()
        return process

    def fake_attach(_pid: int):
        events.append("attach-job")
        return OwnedJob()

    def fake_resume(_pid: int) -> None:
        events.append("resume")

    async def scenario() -> ProcessResult:
        nonlocal spawn_started, allow_spawn, process
        spawn_started = asyncio.Event()
        allow_spawn = asyncio.Event()
        process = SuspendedProcess()
        executor = AsyncSubprocessExecutor()
        run_task = asyncio.create_task(
            executor.run(
                command="node",
                arguments=["--help"],
                cwd=str(workspace),
                approved_env={},
                timeout=None,
            )
        )
        await spawn_started.wait()
        await executor.cancel()
        allow_spawn.set()
        return await asyncio.wait_for(run_task, timeout=2)

    monkeypatch.setattr(subprocess_executor_module.sys, "platform", "win32")
    monkeypatch.setattr(
        subprocess_executor_module.asyncio,
        "create_subprocess_exec",
        fake_create,
    )
    monkeypatch.setattr(subprocess_executor_module.WindowsJob, "attach", fake_attach)
    monkeypatch.setattr(subprocess_executor_module, "resume_windows_process", fake_resume)

    result = run_async(scenario())

    assert result.process_status == "cancelled"
    assert "resume" not in events
    assert events[:3] == ["spawn-started", "attach-job", "terminate"]


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


def test_unterminated_callback_line_is_bounded_and_rejected(workspace) -> None:
    executor = AsyncSubprocessExecutor(output_limit_bytes=128)

    async def accept_line(_line: str) -> None:
        pass

    with pytest.raises(OutputLineTooLongError):
        run_async(
            executor.run(
                command=_node(),
                arguments=["-e", "process.stdout.write('x'.repeat(64*1024)); setInterval(()=>{},1000)"],
                cwd=str(workspace),
                approved_env={},
                timeout=2,
                on_stdout_line=accept_line,
            )
        )


def test_timeout_cancels_a_non_returning_callback(workspace) -> None:
    executor = AsyncSubprocessExecutor()
    never = asyncio.Event()

    async def block_forever(_line: str) -> None:
        await never.wait()

    result = run_async(
        asyncio.wait_for(
            executor.run(
                command=_node(),
                arguments=["-e", "console.log('line'); setInterval(()=>{},1000)"],
                cwd=str(workspace),
                approved_env={},
                timeout=0.2,
                on_stdout_line=block_forever,
            ),
            timeout=2,
        )
    )

    assert result.process_status == "timed_out"


def test_callback_cleanup_failure_is_not_swallowed_by_timeout(workspace) -> None:
    executor = AsyncSubprocessExecutor()

    async def fail_when_cancelled(_line: str) -> None:
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError as error:
            raise RuntimeError("parser cleanup failed") from error

    with pytest.raises(RuntimeError, match="parser cleanup failed"):
        run_async(
            executor.run(
                command=_node(),
                arguments=["-e", "console.log('line'); setInterval(()=>{},1000)"],
                cwd=str(workspace),
                approved_env={},
                timeout=0.2,
                on_stdout_line=fail_when_cancelled,
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
