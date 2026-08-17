"""Provider continuation: resume a paused run after a blocking decision (line-115).

When zhao's C21 Blocking Build Decision gate resolves a pending decision on a
`waiting_for_input` run (`RunRepository.continue_run`), this zhang-owned service
re-drives the OpenGame provider's SAME session with the resolved decision — a
*resume* (the run is paused, not cancelled), not a rebuild. It calls the
OpenGameAdapter's `resume_session` (`opengame --resume <id> -p <decision> ...`),
consumes the resumed run's events into the same run's sequence, and persists the
terminal. The run's workspace is reused (a paused run's working tree is trusted,
not an untrusted partial — C13's discard-on-cancel/failure does NOT apply here).

Binding requirements:
- Rebaseline Aug-16 zhang line 115 + daily gate "confirmed Amendment resumes safely."
- run-observability spec "Safe cancellation and retry": retry from most recent
  playable without reusing an *untrusted partial* workspace. A paused waiting
  run's workspace is trusted; resume reuses it.
- Owner split: zhang owns the OpenGame resume path; zhao's `continue_run`
  repository + `waiting_for_input` persistence stay zhao's — this service is
  called AFTER the decision resolves.

Multi-loop lesson: the resume drive uses a single asyncio.run (start/stream/result
share one loop — the adapter's background _run task can't survive a loop tear-down).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.game_agent import GameBuildResult, RunEvent
from app.models import Build, BuildContext, Run, RunPendingDecision


class _ResumableAgent(Protocol):
    """The OpenGame resume surface (OpenGameAdapter). Duck-typed so tests inject
    a fake; the real one is `OpenGameAdapter`."""
    async def resume_session(self, handle, *, session_id: str, decision_text: str,
                              workspace_root: str, request) -> Any: ...
    def stream_events(self, handle, after_sequence: int = 0): ...
    async def result(self, handle) -> GameBuildResult: ...


RequestBuilder = Callable[[Build, Run], Any]
"""Builds the GameBuildRequest for the resumed run from its Build + Run."""


class ContinuationService:
    """Resumes a paused run's provider session after a blocking decision resolves.

    ``session`` is the SQLite session; ``agent`` is the OpenGameAdapter (or a fake
    with the resume surface); ``request_builder`` rebuilds the GameBuildRequest
    from the run's Build + BuildContext (so the resumed run carries the confirmed
    spec / baseline / scope). Tests inject fakes; production wires the real
    adapter + BuildService._request_for (or an equivalent builder).
    """

    def __init__(
        self,
        session: Session,
        *,
        agent: _ResumableAgent | None = None,
        request_builder: RequestBuilder | None = None,
    ) -> None:
        self.session = session
        self._agent = agent
        self._request_builder = request_builder

    async def resume_build(
        self,
        run_id: str,
        decision_id: str,
        response: Any,
    ) -> Run:
        """Re-drive the provider for a resolved blocking decision on the same run.

        Assumes zhao's ``RunRepository.continue_run`` has already resolved the
        decision (status "resolved") and flipped run.status to "running". This
        service builds the resume request, calls the adapter's resume_session,
        consumes events into the run, and persists the terminal — in ONE event
        loop (the caller drives this under a single asyncio.run).
        """
        run = self.session.get(Run, run_id)
        if run is None:
            raise ValueError("run not found")
        if run.status != "running":
            raise ValueError(f"run is not running after continuation (status={run.status})")
        decision = self.session.scalar(
            select(RunPendingDecision).where(
                RunPendingDecision.run_id == run_id,
                RunPendingDecision.decision_id == decision_id,
            )
        )
        if decision is None or decision.status != "resolved":
            raise ValueError("blocking decision is not resolved")
        if not run.opengame_session_id:
            # A waiting run that captured no OpenGame session cannot be resumed.
            # Surface as a structured failure rather than silently sticking.
            run.failure_code = "session_not_resumable"
            run.failure_message = "Run has no OpenGame session id to resume"
            run.status = "failed"
            self.session.flush()
            return run

        if self._agent is None or self._request_builder is None:
            raise ValueError("ContinuationService needs an agent and request_builder to resume")

        build = self.session.get(Build, run.build_id)
        context = self.session.scalar(select(BuildContext).where(BuildContext.build_id == build.id))
        request = self._request_builder(build, run)

        # A lightweight handle identifying this (same) run for the adapter's dict.
        from app.contracts.game_agent import AgentRunHandle
        handle = AgentRunHandle(run_id=run.id, build_id=build.id)

        decision_text = self._serialize_decision(decision, response)
        await self._agent.resume_session(
            handle,
            session_id=run.opengame_session_id,
            decision_text=decision_text,
            workspace_root=run.workspace_path or request.workspace.root,
            request=request,
        )

        # Consume the resumed run's events + terminal in the SAME event loop (the
        # caller drives this whole method under one asyncio.run). Mirror
        # BuildService._consume_agent: stream non-terminal events, then persist the
        # terminal + run status. Sequences are assigned by RunRepository.append_event
        # (run.last_sequence + 1), not by the adapter's stream sequence.
        from app.repositories.runs import RunRepository
        repo = RunRepository(self.session)
        terminal: RunEvent | None = None
        async for event in self._agent.stream_events(handle, after_sequence=0):
            normalized = event.model_copy(update={"run_id": run.id, "sequence": run.last_sequence + 1})
            if normalized.kind in {"completed", "cancelled", "terminal"}:
                terminal = normalized
            else:
                repo.append_event(normalized)
        result = await self._agent.result(handle)

        # Build the terminal event (with artifact_ref for success) and finish the run.
        from datetime import datetime, timezone
        if terminal is None:
            terminal = RunEvent(
                run_id=run.id, sequence=run.last_sequence + 1,
                stage="complete" if result.status == "succeeded" else "terminal",
                kind="completed" if result.status == "succeeded" else "terminal",
                message="Build completed" if result.status == "succeeded" else (result.error.message if result.error else "Build finished"),
                progress=1 if result.status == "succeeded" else None,
                artifact_ref=result.preview_entry,
                error=result.error,
                timestamp=datetime.now(timezone.utc),
            )
        else:
            # Ensure the success terminal has an artifact_ref (finish_run requires it).
            if result.status == "succeeded" and not terminal.artifact_ref:
                terminal = terminal.model_copy(update={"artifact_ref": result.preview_entry})
            # finish_run requires a non-success terminal to carry an error.
            if result.status != "succeeded" and not terminal.error:
                terminal = terminal.model_copy(update={"error": result.error})
            terminal = terminal.model_copy(update={"sequence": run.last_sequence + 1})
        repo.finish_run(run.id, result.status, terminal)
        if result.status != "succeeded":
            run.failure_code = result.error.code if result.error else None
            run.failure_message = result.error.message if result.error else None
        self.session.flush()
        return run

    @staticmethod
    def _serialize_decision(decision: RunPendingDecision, response: Any) -> str:
        """Render the resolved decision as the resume prompt's decision text."""
        return (
            f"Blocking decision resolved.\n"
            f"Decision: {decision.prompt}\n"
            f"Resolved response: {json.dumps(response, ensure_ascii=False, sort_keys=True)}"
        )
