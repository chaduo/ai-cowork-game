"""FakeProcessExecutor — deterministic stand-in for AsyncSubprocessExecutor.

Used by C10 / the shared contract suite when no real ``opengame`` binary is
available. Mirrors the ``candidate_test_runner`` / ``fake_candidate_test_runner``
Protocol + Fake pair pattern. Does NOT spawn any process.
"""

from __future__ import annotations

from app.agents.executor import AsyncLineCallback, ProcessResult


class FakeProcessExecutor:
    """Returns canned ProcessResults; records the last run's inputs."""

    def __init__(self, outcome: str = "succeeded") -> None:
        # outcome ∈ {succeeded, failed, timed_out, cancelled}
        self.outcome = outcome
        self.runs: list[dict[str, object]] = []
        self.cancel_called = False

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
        self.runs.append(
            {"command": command, "arguments": arguments, "cwd": cwd,
             "approved_env": approved_env, "timeout": timeout}
        )
        if self.outcome == "succeeded":
            stdout = (
                '{"type":"system","subtype":"init","session_id":"s1","model":"kimi-k3","cwd":"/ws","tools":[]}\n'
                '{"type":"result","subtype":"success","session_id":"s1","is_error":false,'
                '"result":"done","usage":{"input_tokens":100,"output_tokens":5}}\n'
            )
            if on_stdout_line is not None:
                for line in stdout.splitlines():
                    await on_stdout_line(line)
            return ProcessResult(
                stdout=stdout,
                stderr="", exit_code=0, process_status="completed", duration_seconds=0.01,
            )
        if self.outcome == "failed":
            if on_stderr_line is not None:
                await on_stderr_line("boom")
            return ProcessResult(
                stdout="", stderr="boom", exit_code=1, process_status="completed",
                duration_seconds=0.01,
            )
        if self.outcome == "timed_out":
            return ProcessResult(
                stdout="", stderr="", exit_code=None, process_status="timed_out",
                duration_seconds=1.5,
            )
        if self.outcome == "cancelled":
            return ProcessResult(
                stdout="", stderr="", exit_code=None, process_status="cancelled",
                duration_seconds=0.6,
            )
        raise ValueError(f"unknown fake executor outcome: {self.outcome}")

    async def cancel(self) -> None:
        self.cancel_called = True
