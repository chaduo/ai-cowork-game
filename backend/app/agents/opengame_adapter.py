"""OpenGameAdapter (C10) — the V1 GameAgent implementation.

Maps a provider-neutral ``GameBuildRequest`` onto a real OpenGame CLI run via the
C09 ``ProcessExecutor``, and maps the stream-json output + ``ProcessResult`` back
onto ``RunEvent`` / ``GameBuildResult``. Upper layers (BuildService) see only the
``GameAgent`` surface — no OpenGame-specific types leak.

Success is NEVER inferred from log keywords alone (catalog AC). The decision
combines: ``ProcessResult.process_status`` + ``exit_code``, the parsed top-level
``result`` event (its ``is_error`` is unreliable per C08), the ``[API Error:]``
marker / zero-token check, and an independent artifact existence check in the
workspace (a "successful" run with no index.html is ``invalid_output``).
"""

from __future__ import annotations

import asyncio
import os
import shutil
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path

from app.agents.opengame_event_mapper import map_stream_to_run_events
from app.agents.executor import ProcessExecutor, ProcessResult
from app.agents.opengame_stream_parser import (
    OpenGameResultEvent,
    parse_stream_json,
    result_indicates_provider_error,
)
from app.agents.workspace import (
    WorkspaceEscapeError,
    WorkspaceManager,
    redact_stream,
)
from app.contracts.game_agent import (
    AgentRunHandle,
    ContractError,
    Diagnostic,
    GameBuildRequest,
    GameBuildResult,
    GameBuildStatus,
    RunEvent,
)

# Operations the V1 OpenGameAdapter supports. Per the C08 spike capability matrix
# (docs/development/c08-opengame-spike/README.md) only `create` has accepted real
# evidence; modify/repair/test would mean guessing provider behavior, so they MUST
# return the provider-neutral `unsupported` result until new real evidence is
# captured. See also design.md: "reports unsupported operations explicitly".
SUPPORTED_OPERATIONS = frozenset({"create"})

# Credentials passed through to the child as the approved env allowlist. The
# adapter never logs these; they come from config (set by the platform), not
# from arbitrary frontend input.
_CREDENTIAL_ENV = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL")


class OpenGameAdapter:
    """``GameAgent`` backed by the real OpenGame CLI (via a ProcessExecutor)."""

    def __init__(
        self,
        executor: ProcessExecutor,
        *,
        model: str = "kimi-k3",
        openai_api_key: str | None = None,
        openai_base_url: str | None = None,
        sandbox: bool = False,
        timeout_seconds: float | None = 300,
        opengame_cli_js: str | None = None,
        workspace_manager: WorkspaceManager | None = None,
    ) -> None:
        self._executor = executor
        self._model = model
        self._api_key = openai_api_key
        self._base_url = openai_base_url
        self._sandbox = sandbox
        self._timeout = timeout_seconds
        self._cli_js = opengame_cli_js or _default_cli_js()
        # C13: the workspace policy + lifecycle. Defaults to a real manager rooted
        # at data/workspaces; tests/Fake inject one. The adapter never reads the
        # parent environment for paths and confines artifact scanning to this.
        self._workspace = workspace_manager or WorkspaceManager()
        self._runs: dict[str, _Run] = {}
        self._counter = 0

    async def start(self, request: GameBuildRequest) -> AgentRunHandle:
        self._counter += 1
        run_id = f"opengame-run-{self._counter}"
        handle = AgentRunHandle(run_id=run_id, build_id=request.build_id)
        started_at = datetime.now(timezone.utc)

        if request.operation not in SUPPORTED_OPERATIONS:
            run = _Run.unsupported(handle, request, started_at)
            self._runs[run_id] = run
            return handle

        run = _Run(handle, request, started_at, self._build_command(request),
                   self._build_env(), self._timeout, self._executor, self._workspace)
        self._runs[run_id] = run
        await run.start()
        return handle

    def stream_events(self, handle: AgentRunHandle, after_sequence: int = 0) -> AsyncIterator[RunEvent]:
        run = self._require_run(handle)

        async def iterator() -> AsyncIterator[RunEvent]:
            await run.finished.wait()
            for event in run.run_events:
                if event.sequence > after_sequence:
                    yield event

        return iterator()

    async def result(self, handle: AgentRunHandle) -> GameBuildResult:
        run = self._require_run(handle)
        await run.wait_for_completion()
        return run.result

    async def cancel(self, handle: AgentRunHandle) -> None:
        run = self._require_run(handle)
        run.cancel()
        await self._executor.cancel()

    # -- helpers ------------------------------------------------------------- #

    def _require_run(self, handle: AgentRunHandle) -> _Run:
        try:
            return self._runs[handle.run_id]
        except KeyError as exc:
            raise ValueError(f"unknown agent run: {handle.run_id}") from exc

    def _build_command(self, request: GameBuildRequest) -> tuple[str, list[str]]:
        node = shutil.which("node") or "node"
        prompt = request.request_text or "build the game"
        args = [
            self._cli_js,
            "-p", prompt,
            "--yolo", "--auth-type", "openai",
            "-m", self._model,
            "-o", "stream-json",
        ]
        if not self._sandbox:
            # GEMINI_SANDBOX=false in env handles this; no flag needed.
            pass
        return node, args

    def _build_env(self) -> dict[str, str]:
        env: dict[str, str] = {"GEMINI_SANDBOX": "false"}
        if self._api_key:
            env["OPENAI_API_KEY"] = self._api_key
        if self._base_url:
            env["OPENAI_BASE_URL"] = self._base_url
        env["OPENAI_MODEL"] = self._model
        return env


def _default_cli_js() -> str:
    """Locate opengame's dist/cli.js (the npm-link'd install), or a vendored copy."""
    candidates = [
        r"D:\Program Files (x86)\nodejs\node_global\node_modules\@opengame\opengame\dist\cli.js",
        "vendor/opengame/dist/cli.js",
    ]
    og = shutil.which("opengame")
    if og:
        shim_dir = os.path.dirname(os.path.realpath(og))
        candidates.append(
            os.path.join(shim_dir, "node_modules", "@opengame", "opengame", "dist", "cli.js")
        )
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return ""


class _Run:
    """In-flight state for one OpenGame run."""

    def __init__(self, handle, request, started_at, command_env, env, timeout, executor, workspace):
        self.handle = handle
        self.request = request
        self.started_at = started_at
        self._command, self._args = command_env
        self._env = env
        self._timeout = timeout
        self._executor = executor
        self._workspace = workspace
        self.finished = asyncio.Event()
        self.process_result: ProcessResult | None = None
        self.run_events: list[RunEvent] = []
        self.cancelled = False
        self.result: GameBuildResult = self._pending_result()
        self._task: asyncio.Task | None = None

    @classmethod
    def unsupported(cls, handle, request, started_at) -> "_Run":
        run = cls.__new__(cls)
        run.handle = handle
        run.request = request
        run.started_at = started_at
        run._command = run._args = None
        run._env = {}
        run._timeout = None
        run._executor = None
        run._workspace = None
        run.finished = asyncio.Event()
        run.finished.set()
        run.process_result = None
        run.run_events = [_unsupported_event(handle, started_at)]
        run.cancelled = False
        run._task = None
        run.result = GameBuildResult(
            status="unsupported",
            artifact_manifest=[],
            preview_entry=None,
            diagnostics=[Diagnostic(level="warning", code="unsupported_operation",
                                    message=f"{request.operation} is not supported")],
            error=ContractError(code="unsupported_operation",
                                message=f"{request.operation} is not supported"),
            metadata={"backend": "opengame", "operation": request.operation},
        )
        return run

    async def start(self) -> None:
        self._task = asyncio.ensure_future(self._run())

    async def _run(self) -> None:
        assert self._executor is not None
        try:
            self.process_result = await self._executor.run(
                command=self._command,
                arguments=self._args,
                cwd=self.request.workspace.root,
                approved_env=self._env,
                timeout=self._timeout,
            )
        except Exception as exc:  # executor raised (e.g. spawn failed)
            self.process_result = ProcessResult(
                stdout="", stderr=str(exc), exit_code=None,
                process_status="completed", duration_seconds=0.0,
            )
        # C13: scrub secrets from the raw provider stream BEFORE it reaches the
        # event mapper or the status/scan decision, so a key echoed in stdout can
        # never land in a RunEvent, Diagnostic, or audit record. Redaction does
        # not truncate (the stream-json parser needs the full buffer).
        pr = self.process_result
        self.process_result = ProcessResult(
            stdout=redact_stream(pr.stdout),
            stderr=redact_stream(pr.stderr),
            exit_code=pr.exit_code,
            process_status=pr.process_status,
            duration_seconds=pr.duration_seconds,
            output_truncated=pr.output_truncated,
        )
        self.run_events = map_stream_to_run_events(
            parse_stream_json(self.process_result.stdout),
            run_id=self.handle.run_id,
            started_at=self.started_at,
        )
        self.result = _build_result(self.process_result, self.run_events, self.request, self._workspace)
        self.finished.set()

    def cancel(self) -> None:
        # Mark this run cancelled; result() applies it after the run task settles.
        # The executor's cancel() drives the tree-kill for a real subprocess.
        self.cancelled = True

    async def wait_for_completion(self) -> None:
        if self._task is not None:
            await self._task
        await self.finished.wait()
        if self.cancelled:
            self._apply_cancelled()

    def _apply_cancelled(self) -> None:
        """Override result/events for a cancelled run (platform-driven cancel)."""
        err = ContractError(code="cancelled", message="Build cancelled")
        # Ensure a cancelled terminal event exists as the last event.
        seq = (self.run_events[-1].sequence if self.run_events else 0) + 1
        self.run_events.append(RunEvent(
            run_id=self.handle.run_id, sequence=seq, stage="terminal", kind="cancelled",
            message="build cancelled", progress=1.0, timestamp=datetime.now(timezone.utc),
            error=err,
        ))
        self.result = GameBuildResult(
            status="cancelled",
            artifact_manifest=[],
            preview_entry=None,
            diagnostics=[Diagnostic(level="warning", code="cancelled", message="Build cancelled")],
            error=err,
            metadata={"backend": "opengame", "operation": self.request.operation},
        )

    def _pending_result(self) -> GameBuildResult:
        return GameBuildResult(
            status="failed",
            artifact_manifest=[],
            preview_entry=None,
            diagnostics=[],
            error=ContractError(code="not_started", message="run not started"),
            metadata={"backend": "opengame"},
        )


def _unsupported_event(handle, started_at) -> RunEvent:
    return RunEvent(
        run_id=handle.run_id, sequence=1, stage="terminal", kind="terminal",
        message="unsupported operation", progress=1.0, timestamp=started_at,
        error=ContractError(code="unsupported_operation", message="unsupported operation"),
    )


def _build_result(
    process: ProcessResult,
    events: list[RunEvent],
    request: GameBuildRequest,
    workspace: WorkspaceManager,
) -> GameBuildResult:
    """Decide GameBuildStatus WITHOUT trusting log keywords (catalog AC)."""
    # 1. process-level cause (C09): timeout/cancelled are authoritative.
    if process.process_status == "cancelled":
        return _result("cancelled", "cancelled", "Build cancelled", events, request, process)
    if process.process_status == "timed_out":
        return _result("timed_out", "timeout", "Build timed out", events, request, process)

    # 2. parse the top-level result event (its is_error is unreliable — C08).
    result_events = [e for e in parse_stream_json(process.stdout) if isinstance(e, OpenGameResultEvent)]
    top_result = result_events[-1] if result_events else None

    if top_result is not None and result_indicates_provider_error(top_result):
        return _result("failed", "provider_failed", "OpenGame provider error", events, request, process)

    # 3. exit code
    if process.exit_code not in (None, 0):
        return _result("failed", "provider_failed",
                        f"OpenGame exited with code {process.exit_code}", events, request, process)

    # 4. no terminal result event → interrupted stream → failed (not succeeded)
    if top_result is None:
        return _result("failed", "provider_failed", "OpenGame run produced no result", events, request, process)

    # 5. top-level is_error true → failed
    if top_result.is_error:
        return _result("failed", "provider_failed", "OpenGame run reported failure", events, request, process)

    # 6. artifact existence check — success without an artifact is invalid_output (C08).
    #    C13: the scan is escape-safe; a generated symlink/traversal pointing at host
    #    files is rejected and recorded as a sanitized workspace_escape policy error
    #    (not imported), rather than trusted from log keywords alone.
    try:
        artifacts, preview = workspace.scan_preview(
            Path(request.workspace.root), request.workspace.allowed_paths
        )
    except WorkspaceEscapeError as esc:
        # Preserve the specific escape reason (protected_path / symlink_escape /
        # traversal / ...) in the error code for audit; the message is sanitized.
        return _result("invalid_output", esc.code, esc.message, events, request, process)
    if not artifacts:
        return _result("invalid_output", "invalid_output",
                        "OpenGame succeeded but produced no playable artifact",
                        events, request, process)

    # 7. success
    return GameBuildResult(
        status="succeeded",
        artifact_manifest=artifacts,
        preview_entry=preview,
        diagnostics=[],
        metadata={"backend": "opengame", "operation": request.operation,
                   "duration_seconds": process.duration_seconds},
    )


def _result(status: GameBuildStatus, code: str, message: str,
            events: list[RunEvent], request: GameBuildRequest, process: ProcessResult) -> GameBuildResult:
    err = ContractError(code=code, message=message)
    return GameBuildResult(
        status=status,
        artifact_manifest=[],
        preview_entry=None,
        diagnostics=[Diagnostic(level="error", code=code, message=message)],
        error=err,
        metadata={"backend": "opengame", "operation": request.operation,
                  "duration_seconds": process.duration_seconds},
    )
