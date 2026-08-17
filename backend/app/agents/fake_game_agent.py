from dataclasses import dataclass
from datetime import datetime, timezone
from collections.abc import AsyncIterator
from typing import Mapping

from app.agents.game_agent import GameAgent
from app.contracts.game_agent import (
    AgentRunHandle,
    ArtifactManifestEntry,
    ContractError,
    Diagnostic,
    GameBuildRequest,
    GameBuildResult,
    GameBuildStatus,
    PendingDecision,
    RunEvent,
)


SUPPORTED_OPERATIONS = frozenset({"create", "modify", "repair", "test"})


@dataclass
class _FakeRun:
    request: GameBuildRequest
    handle: AgentRunHandle
    events: list[RunEvent]
    result: GameBuildResult


class FakeGameAgent(GameAgent):
    """Deterministic runtime used by the shared contract tests only."""

    def __init__(self, outcome_by_operation: Mapping[str, GameBuildStatus] | None = None) -> None:
        self._outcomes = dict(outcome_by_operation or {})
        self._runs: dict[str, _FakeRun] = {}
        self._next_run = 1
        self.requests: list[GameBuildRequest] = []

    async def start(self, request: GameBuildRequest) -> AgentRunHandle:
        self.requests.append(request)
        run_id = f"fake-run-{self._next_run}"
        self._next_run += 1
        handle = AgentRunHandle(run_id=run_id, build_id=request.build_id)
        status = self._outcomes.get(request.operation)
        if request.operation not in SUPPORTED_OPERATIONS:
            status = "unsupported"
        events, result = self._build_trace(request, handle, status or "succeeded")
        self._runs[run_id] = _FakeRun(request=request, handle=handle, events=events, result=result)
        return handle

    async def result(self, handle: AgentRunHandle) -> GameBuildResult:
        return self._run(handle).result

    async def cancel(self, handle: AgentRunHandle) -> None:
        run = self._run(handle)
        events, result = self._build_trace(run.request, handle, "cancelled")
        run.events = events
        run.result = result

    def stream_events(self, handle: AgentRunHandle, after_sequence: int = 0) -> AsyncIterator[RunEvent]:
        run = self._run(handle)

        async def iterator():
            for event in run.events:
                if event.sequence > after_sequence:
                    yield event

        return iterator()

    def _run(self, handle: AgentRunHandle) -> _FakeRun:
        try:
            return self._runs[handle.run_id]
        except KeyError as error:
            raise ValueError(f"unknown agent run: {handle.run_id}") from error

    def _build_trace(
        self,
        request: GameBuildRequest,
        handle: AgentRunHandle,
        status: GameBuildStatus,
    ) -> tuple[list[RunEvent], GameBuildResult]:
        now = datetime.now(timezone.utc)
        if status == "succeeded":
            events = [
                RunEvent(run_id=handle.run_id, sequence=1, stage="starting", kind="started", message="Build started", progress=0, timestamp=now),
                RunEvent(run_id=handle.run_id, sequence=2, stage="building", kind="progress", message="Building artifact", progress=0.5, timestamp=now),
                RunEvent(run_id=handle.run_id, sequence=3, stage="complete", kind="completed", message="Build completed", progress=1, artifact_ref="dist/index.html", timestamp=now),
            ]
            result = GameBuildResult(
                status="succeeded",
                artifact_manifest=[ArtifactManifestEntry(path="dist/index.html", kind="preview_entry", size_bytes=1200, sha256="0" * 64)],
                preview_entry="dist/index.html",
                diagnostics=[],
                metadata={"backend": "fake", "operation": request.operation},
            )
            return events, result

        if status == "waiting_for_input":
            decision_id = f"decision-{request.operation}-{handle.run_id.rsplit('-', 1)[-1]}"
            decision = PendingDecision(
                decision_id=decision_id,
                prompt="选择下一步构建策略",
                input_type="choice",
                options=["继续默认方案", "调整当前范围"],
            )
            events = [
                RunEvent(run_id=handle.run_id, sequence=1, stage="building", kind="started", message="Build started", progress=0, timestamp=now),
                RunEvent(
                    run_id=handle.run_id,
                    sequence=2,
                    stage="waiting_for_input",
                    kind="build.needs_input",
                    message=decision.prompt,
                    progress=None,
                    timestamp=now,
                    decision_id=decision.decision_id,
                ),
            ]
            return events, GameBuildResult(
                status="waiting_for_input",
                diagnostics=[Diagnostic(level="info", message="Waiting for user input", code="waiting_for_input")],
                metadata={"backend": "fake", "operation": request.operation},
                pending_decision=decision,
            )

        error_by_status = {
            "cancelled": ("cancelled", "Build cancelled"),
            "timed_out": ("timeout", "Build timed out"),
            "invalid_output": ("invalid_output", "Build output is invalid"),
            "unsupported": ("unsupported_operation", f"{request.operation} is not supported"),
            "failed": ("provider_failed", "Fake runtime failed"),
        }
        error_code, error_message = error_by_status[status]
        error = ContractError(code=error_code, message=error_message)
        event_kind = "cancelled" if status == "cancelled" else "terminal"
        events = [
            RunEvent(run_id=handle.run_id, sequence=1, stage="starting", kind="started", message="Build started", progress=0, timestamp=now),
            RunEvent(run_id=handle.run_id, sequence=2, stage="terminal", kind=event_kind, message=error_message, error=error, timestamp=now),
        ]
        diagnostics_level = "warning" if status in {"cancelled", "timed_out", "unsupported"} else "error"
        result = GameBuildResult(
            status=status,
            artifact_manifest=[],
            preview_entry=None,
            diagnostics=[Diagnostic(level=diagnostics_level, message=error_message, code=error_code)],
            metadata={"backend": "fake", "operation": request.operation},
            error=error,
        )
        return events, result
