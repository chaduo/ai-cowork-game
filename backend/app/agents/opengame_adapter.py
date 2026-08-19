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
import json
import os
import shutil
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path

from app.agents.opengame_event_mapper import map_stream_to_run_events
from app.agents.executor import ExecutorBusyError, ProcessExecutor, ProcessResult
from app.agents.opengame_stream_parser import (
    OpenGameParseError,
    OpenGameResultEvent,
    OpenGameSystemEvent,
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
from app.redaction import redact_text

# Operations the V1 OpenGameAdapter supports via the provider-neutral `start`.
# Per the C08 spike capability matrix only `create` has accepted real evidence;
# modify/repair/test would mean guessing provider behavior, so they MUST return
# the provider-neutral `unsupported` result until new real evidence is captured.
# `resume` is a real OpenGame capability (`--resume <id>`) but it needs the
# provider-specific session id, so it is NOT a `start(operation=...)` (the neutral
# GameBuildRequest carries no session id); it is a dedicated `resume_session`
# method below (line-115), called by ContinuationService after a blocking
# decision resolves.
SUPPORTED_OPERATIONS = frozenset({"create"})

# Credentials passed through to the child as the approved env allowlist. The
# adapter never logs these; they come from config (set by the platform), not
# from arbitrary frontend input.
_CREDENTIAL_ENV = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL")


def _write_debug_stream(run_id: str, stdout: str, stderr: str) -> None:
    """Optionally persist redacted provider output for a single diagnostic run.

    Debug capture is opt-in because provider streams can contain prompts and
    generated source. Redact here as defense in depth so this helper is safe to
    call from future diagnostics as well.
    """
    debug_dir = os.getenv("OPENGAME_DEBUG_DIR")
    if not debug_dir:
        return
    root = Path(debug_dir)
    try:
        root.mkdir(parents=True, exist_ok=True)
        (root / f"{run_id}.stdout.jsonl").write_text(redact_stream(stdout), encoding="utf-8")
        (root / f"{run_id}.stderr.log").write_text(redact_stream(stderr), encoding="utf-8")
    except OSError:
        # Diagnostics must never change the provider result or strand a run.
        return


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
        require_credentials: bool = False,
    ) -> None:
        self._executor = executor
        self._model = model
        self._api_key = openai_api_key
        self._base_url = openai_base_url
        self._sandbox = sandbox
        self._timeout = timeout_seconds
        self._cli_js = opengame_cli_js or _default_cli_js()
        self._require_credentials = require_credentials
        # C13: the workspace policy + lifecycle. Defaults to a real manager rooted
        # at data/workspaces; tests/Fake inject one. The adapter never reads the
        # parent environment for paths and confines artifact scanning to this.
        self._workspace = workspace_manager or WorkspaceManager()
        self._runs: dict[str, _Run] = {}
        self._counter = 0
        self._active_run_id: str | None = None

    async def start(self, request: GameBuildRequest) -> AgentRunHandle:
        if self._active_run_id is not None:
            active = self._runs.get(self._active_run_id)
            if active is not None and not active.finished.is_set():
                raise ExecutorBusyError("OpenGameAdapter already owns an active run")
            self._active_run_id = None
        self._counter += 1
        run_id = f"opengame-run-{self._counter}"
        handle = AgentRunHandle(run_id=run_id, build_id=request.build_id)
        started_at = datetime.now(timezone.utc)

        if request.operation not in SUPPORTED_OPERATIONS:
            run = _Run.unsupported(handle, request, started_at)
            self._runs[run_id] = run
            return handle

        if self._require_credentials and (
            not self._cli_js or not self._api_key or not self._base_url
        ):
            run = _Run.configuration_error(handle, request, started_at)
            self._runs[run_id] = run
            return handle

        run = _Run(handle, request, started_at, self._build_command(request),
                   self._build_env(), self._timeout, self._executor, self._workspace)
        self._runs[run_id] = run
        self._active_run_id = run_id
        await run.start()
        return handle

    async def resume_session(
        self,
        handle: AgentRunHandle,
        *,
        session_id: str,
        decision_text: str,
        workspace_root: str,
        request: GameBuildRequest,
    ) -> AgentRunHandle:
        """Resume the OpenGame provider's paused session with a resolved decision.

        Drives ``opengame --resume <session_id> -p "<decision>" --yolo
        --auth-type openai -m <model> -o stream-json`` against the SAME run's
        workspace (a waiting run is paused, not cancelled — its working tree is
        reused, NOT a fresh/discard workspace). The resolved blocking decision is
        passed as the ``-p`` prompt (the OpenGame session's existing context
        resumes; the decision is the new input). Returns the SAME handle so the
        caller's stream_events/result continue to reference this run.

        This is the line-115 continuation path: ContinuationService calls it after
        RunRepository.continue_run resolves the blocking decision. It is OpenGame-
        specific (the session id is provider-specific), so it is a dedicated method,
        not a `start(operation="resume")` (the neutral GameBuildRequest carries no
        session id).
        """
        run = self._require_run(handle)
        command, args = self._build_resume_command(session_id, decision_text)
        # Reuse the same _Run: override the workspace root so the resumed run
        # executes in the SAME workspace (a waiting run is paused, not cancelled),
        # replace its command/env, reset terminal state, and re-drive the executor.
        run.request = request.model_copy(update={
            "workspace": request.workspace.model_copy(update={"root": workspace_root}),
        })
        run._command, run._args = command, args
        run._env = self._build_env()
        run.finished = asyncio.Event()
        run.process_result = None
        run.run_events = []
        run.result = run._pending_result()
        run._task = asyncio.ensure_future(run._run())
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
        # line-115: surface the captured OpenGame session id on the result metadata
        # so the platform can persist it (Run.opengame_session_id) and later resume
        # the paused session after a blocking decision resolves. metadata is a free
        # dict already in the contract; this is non-destructive (model_copy).
        if run.opengame_session_id and run.result.status == "waiting_for_input":
            run.result = run.result.model_copy(update={
                "metadata": {**run.result.metadata, "opengame_session_id": run.opengame_session_id},
            })
        return run.result

    async def cancel(self, handle: AgentRunHandle) -> None:
        run = self._require_run(handle)
        if run.finished.is_set():
            return
        run.request_cancel()
        await self._executor.cancel()

    # -- helpers ------------------------------------------------------------- #

    def _require_run(self, handle: AgentRunHandle) -> _Run:
        try:
            return self._runs[handle.run_id]
        except KeyError as exc:
            raise ValueError(f"unknown agent run: {handle.run_id}") from exc

    def _build_command(self, request: GameBuildRequest) -> tuple[str, list[str]]:
        node = shutil.which("node") or "node"
        prompt = _build_prompt(request)
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

    def _build_resume_command(self, session_id: str, decision_text: str) -> tuple[str, list[str]]:
        """Build the `opengame --resume <id> -p <decision>` command (line-115).

        The resolved blocking decision is the `-p` prompt (the session's existing
        context resumes; the decision is the new input). `--resume <id>` resumes
        the paused OpenGame session; `--yolo` auto-approves; `-o stream-json` keeps
        the normalized-event contract. No stdin — `-p` carries the decision.
        """
        node = shutil.which("node") or "node"
        prompt = redact_text(decision_text, max_length=len(decision_text))
        args = [
            self._cli_js,
            "--resume", session_id,
            "-p", prompt,
            "--yolo", "--auth-type", "openai",
            "-m", self._model,
            "-o", "stream-json",
        ]
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
    explicit = os.getenv("OPENGAME_CLI_JS")
    if explicit and os.path.isfile(explicit):
        return os.path.realpath(explicit)
    candidates = [
        r"D:\Program Files (x86)\nodejs\node_global\node_modules\@opengame\opengame\dist\cli.js",
        "vendor/opengame/dist/cli.js",
    ]
    og = shutil.which("opengame")
    if og:
        real_cli = os.path.realpath(og)
        if os.path.isfile(real_cli):
            candidates.append(real_cli)
        shim_dir = os.path.dirname(real_cli)
        candidates.append(
            os.path.join(shim_dir, "node_modules", "@opengame", "opengame", "dist", "cli.js")
        )
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return ""


def _build_prompt(request: GameBuildRequest) -> str:
    """Serialize the confirmed design and approved build context deterministically.

    The provider receives the design contract, not the host workspace path or raw
    environment. Sorting keys keeps command evidence and retries reproducible.
    """
    payload = {
        "runtime_build_spec": request.runtime_build_spec.model_dump(mode="json"),
        "first_playable": {
            "goal": request.creator_game_spec.first_playable.goal,
            "hypothesis": request.creator_game_spec.first_playable.hypothesis,
            "validation": request.creator_game_spec.validation,
        },
        "approved_context": {
            "baseline_playable": request.baseline_playable,
            "affected_scope": request.affected_scope.model_dump(mode="json"),
            "resource_references": [item.model_dump(mode="json") for item in request.resource_references],
            "implementation_dependencies": request.implementation_dependencies,
            "relevant_overrides": [item.model_dump(mode="json") for item in request.relevant_overrides],
        },
    }
    spec_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    prompt = (
        "MANDATORY EXECUTION ORDER: your first meaningful action must be a "
        "write_file tool call that creates the playable index.html in the "
        "current workspace. Do not answer with a plan, explanation, markdown, "
        "or a code block before making that tool call; a text-only response is "
        "a failure. After the write_file result, verify that index.html exists "
        "in the current workspace (use a file/directory tool if needed), and "
        "only then continue implementation or send a final response. "
        "Build a self-contained playable game from the confirmed design. "
        "Write the preview entry as index.html inside the supplied workspace. "
        "The generated index.html MUST expose a platform test hook exactly as "
        "window.__GAME_TEST__ = {version: 1, ready: true, run: async (check) => "
        "({passed: boolean, observed: string})}. The run function MUST support "
        "the checks core_input, gameplay, and completion and must exercise the "
        "actual game state rather than returning hardcoded PASS. "
        "Do not access host paths, credentials, or files outside the workspace.\n"
        f"Creator request: {request.request_text or '(none)'}\n"
        f"Confirmed design (JSON): {spec_json}"
    )
    # Redact credential-shaped values supplied through user-controlled context,
    # while retaining the complete prompt for the provider.
    return redact_text(prompt, max_length=len(prompt))


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
        # line-115: the OpenGame session id, captured from the first `system`
        # event so a later resume (`opengame --resume <id>`) can re-drive this
        # session after a blocking decision resolves. None until the run starts.
        self.opengame_session_id: str | None = None
        self.cancel_requested = False
        self.cancel_before_executor_started = False
        self.executor_started = False
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
        run.opengame_session_id = None
        run.cancel_requested = False
        run.cancel_before_executor_started = False
        run.executor_started = False
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

    @classmethod
    def configuration_error(cls, handle, request, started_at) -> "_Run":
        run = cls.unsupported(handle, request, started_at)
        error = ContractError(
            code="opengame_not_configured",
            message="OpenGame provider is not configured; set OPENGAME_CLI_JS, OPENAI_API_KEY and OPENAI_BASE_URL",
        )
        run.run_events = [RunEvent(
            run_id=handle.run_id,
            sequence=1,
            stage="terminal",
            kind="terminal",
            message=error.message,
            timestamp=started_at,
            error=error,
        )]
        run.result = GameBuildResult(
            status="failed",
            diagnostics=[Diagnostic(level="error", code=error.code, message=error.message)],
            metadata={"backend": "opengame", "operation": request.operation},
            error=error,
        )
        return run

    async def start(self) -> None:
        self._task = asyncio.ensure_future(self._run())

    async def _run(self) -> None:
        assert self._executor is not None
        if self.cancel_requested and self.cancel_before_executor_started:
            self.process_result = ProcessResult(
                stdout="", stderr="", exit_code=None,
                process_status="cancelled", duration_seconds=0.0,
            )
            self.run_events = []
            self.result = _build_result(self.process_result, self.run_events, self.request, self._workspace)
            self.finished.set()
            return
        self.executor_started = True
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
        _write_debug_stream(
            self.handle.run_id,
            self.process_result.stdout,
            self.process_result.stderr,
        )
        self.run_events = map_stream_to_run_events(
            parse_stream_json(self.process_result.stdout),
            run_id=self.handle.run_id,
            started_at=self.started_at,
        )
        # line-115: capture the OpenGame session id from the first system event so
        # a later resume can re-drive this session after a blocking decision.
        if self.opengame_session_id is None:
            for event in parse_stream_json(self.process_result.stdout):
                if isinstance(event, OpenGameSystemEvent) and event.session_id:
                    self.opengame_session_id = event.session_id
                    break
        self.result = _build_result(self.process_result, self.run_events, self.request, self._workspace)
        self.finished.set()

    def request_cancel(self) -> None:
        # A pre-start cancellation must win even for a deterministic fake
        # executor that returns a completed result. Once the executor has
        # started, its authoritative process status decides whether cancellation
        # won a race with natural completion.
        self.cancel_requested = True
        if not self.executor_started:
            self.cancel_before_executor_started = True

    async def wait_for_completion(self) -> None:
        if self._task is not None:
            await self._task
        await self.finished.wait()
        process_status = self.process_result.process_status if self.process_result else None
        if self.cancel_requested and (
            self.cancel_before_executor_started or process_status != "completed"
        ):
            self._apply_cancelled()

    def _apply_cancelled(self) -> None:
        """Override result/events for a cancelled run (platform-driven cancel)."""
        if self.result.status == "cancelled":
            if self.run_events and self.run_events[-1].kind == "cancelled":
                return
            err = self.result.error or ContractError(code="cancelled", message="Build cancelled")
            seq = (self.run_events[-1].sequence if self.run_events else 0) + 1
            self.run_events.append(RunEvent(
                run_id=self.handle.run_id, sequence=seq, stage="terminal", kind="cancelled",
                message="build cancelled", progress=1.0, timestamp=datetime.now(timezone.utc),
                error=err,
            ))
            return
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

    # 2. Parse the stream. A malformed line is provider output corruption, even
    # if a later line happens to contain a success result.
    parsed_events = parse_stream_json(process.stdout)
    if any(isinstance(event, OpenGameParseError) for event in parsed_events):
        return _result("invalid_output", "invalid_provider_output",
                       "OpenGame produced malformed stream output", events, request, process)

    # 3. Parse the top-level result event (its is_error is unreliable — C08).
    result_events = [e for e in parsed_events if isinstance(e, OpenGameResultEvent)]
    top_result = result_events[-1] if result_events else None

    if top_result is not None and top_result.subtype == "cancelled":
        return _result("cancelled", "cancelled", "Build cancelled", events, request, process)

    if top_result is not None and result_indicates_provider_error(top_result):
        return _result("failed", "provider_failed", "OpenGame provider error", events, request, process)

    # 4. exit code
    if process.exit_code not in (None, 0):
        return _result("failed", "provider_failed",
                        f"OpenGame exited with code {process.exit_code}", events, request, process)

    # 5. no terminal result event → interrupted stream → failed (not succeeded)
    if top_result is None:
        return _result("failed", "provider_failed", "OpenGame run produced no result", events, request, process)

    # 6. top-level is_error true → failed
    if top_result.is_error:
        return _result("failed", "provider_failed", "OpenGame run reported failure", events, request, process)

    # 7. artifact existence check — success without an artifact is invalid_output (C08).
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
    if preview is None:
        return _result("invalid_output", "invalid_artifact",
                       "OpenGame produced artifacts without index.html",
                       events, request, process)

    # 8. success
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
