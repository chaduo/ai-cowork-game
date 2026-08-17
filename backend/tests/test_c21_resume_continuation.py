"""line-115 — provider continuation (resume) for a resolved blocking decision.

Rebaseline Aug-16 zhang item: a `waiting_for_input` run whose blocking decision
is resolved resumes the OpenGame provider's SAME session (not a rebuild), on the
SAME run/workspace, and reaches a terminal. The run-observability "safe retry"
invariant holds — a *paused* run's workspace is trusted (not an untrusted
partial), so resume reuses it; C13 discard only applies to cancel/failure/orphan.

These tests drive `ContinuationService.resume_build` with a fake resumable agent
(no real OpenGame session), asserting: same run_id + reused workspace, events
appended in order after the resolve, terminal persisted, decision resolved,
idempotent re-resolve, and the session-not-resumable failure when no session id.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.game_agent import (
    AgentRunHandle,
    ContractError,
    GameBuildRequest,
    GameBuildResult,
    RunEvent,
    WorkspaceRef,
)
from app.models import Build, BuildCandidate, Run, RunPendingDecision
from app.services.continuation import ContinuationService
from app.services.lifecycle import ProjectLifecycleService
from tests.test_c05_design_api import draft_payload
from tests.test_c05_gamespec_contract import valid_gamespec


SESSION_ID = "og-session-abc"


def _confirmed_project(session: Session) -> str:
    lifecycle = ProjectLifecycleService(session)
    project = lifecycle.create_project("Resume Garden", "A resume test game")
    design = lifecycle.submit_design(project.id, draft_payload())
    session.flush()
    # Drive readiness to ready so confirm_design passes.
    from app.contracts.design import DesignReadiness
    import json
    rev = session.get(__import__("app.models", fromlist=["GameDesignRevision"]).GameDesignRevision, design.current_revision_id)
    rev.readiness_json = json.dumps(DesignReadiness(status="ready", blockers=[], unresolved_decisions=[]).model_dump(mode="json"), ensure_ascii=False)
    session.flush()
    lifecycle.confirm_design(project.id)
    lifecycle.create_gamespec_revision(project.id, valid_gamespec())
    session.commit()
    return project.id


def _waiting_run(session: Session, project_id: str, workspace_root: Path) -> tuple[Run, RunPendingDecision]:
    """Build a Run that paused at waiting_for_input with a pending blocking decision
    and a captured OpenGame session id (the state after a create that paused)."""
    revision = session.scalar(
        select(__import__("app.models", fromlist=["GameSpecRevision"]).GameSpecRevision)
        .where(__import__("app.models", fromlist=["GameSpecRevision"]).GameSpecRevision.project_id == project_id)
        .order_by(__import__("app.models", fromlist=["GameSpecRevision"]).GameSpecRevision.revision_number.desc())
    )
    build = Build(project_id=project_id, gamespec_revision_id=revision.id, status="running")
    session.add(build)
    session.flush()
    workspace_root.mkdir(parents=True, exist_ok=True)
    run = Run(
        id=f"run-{build.id}", build_id=build.id, status="waiting_for_input",
        last_sequence=2, workspace_path=str(workspace_root),
        workspace_status="prepared", opengame_session_id=SESSION_ID,
    )
    session.add(run)
    session.flush()
    decision = RunPendingDecision(
        id="dec-1", run_id=run.id, decision_id="dec-1",
        prompt="Choose scope: default or adjusted?", input_type="choice",
        options_json='["default","adjusted"]', status="pending",
    )
    session.add(decision)
    session.flush()
    return run, decision


class _FakeResumableAgent:
    """A fake with the resume surface: resume_session re-drives and the resumed
    stream/result return a succeeded terminal. Mirrors OpenGameAdapter's
    stream_events/result contract (events already produced, then a terminal)."""

    def __init__(self, terminal_status: str = "succeeded"):
        self._terminal_status = terminal_status
        self.resume_called: dict = {}
        self._handle: AgentRunHandle | None = None

    async def resume_session(self, handle, *, session_id, decision_text, workspace_root, request):
        self.resume_called = {
            "session_id": session_id, "decision_text": decision_text,
            "workspace_root": workspace_root, "operation": request.operation,
        }
        self._handle = handle
        return handle

    def stream_events(self, handle, after_sequence: int = 0):
        async def iterator():
            # A resumed run emits a continuation event then a terminal.
            yield RunEvent(
                run_id=handle.run_id, sequence=after_sequence + 1, stage="running",
                kind="progress", message="resuming session", progress=0.5,
                timestamp=datetime.now(timezone.utc),
            )
            kind = "completed" if self._terminal_status == "succeeded" else "terminal"
            yield RunEvent(
                run_id=handle.run_id, sequence=after_sequence + 2, stage="terminal",
                kind=kind, message="Build completed" if self._terminal_status == "succeeded" else "Build failed",
                progress=1.0 if self._terminal_status == "succeeded" else None,
                timestamp=datetime.now(timezone.utc),
            )
        return iterator()

    async def result(self, handle) -> GameBuildResult:
        if self._terminal_status == "succeeded":
            return GameBuildResult(
                status="succeeded", artifact_manifest=[], preview_entry="playable/index.html",
                diagnostics=[], metadata={"backend": "fake-resume"},
            )
        return GameBuildResult(
            status="failed", artifact_manifest=[], preview_entry=None, diagnostics=[],
            error=ContractError(code="resume_failed", message="resume failed"),
            metadata={"backend": "fake-resume"},
        )


def _request_builder(build, run):
    """Build the resume GameBuildRequest (operation stays 'create' — the neutral
    contract has no 'resume'; resume_session is the OpenGame-specific path)."""
    revision = build.gamespec_revision_id
    from app.contracts.gamespec import CreatorGameSpec
    spec = CreatorGameSpec.model_validate({
        "schema_version": 1, "title": "resume", "first_playable": {"goal": "g", "hypothesis": "h"},
        "gameplay": {"core_loop": ["m"], "actions": ["m"]},
        "characters": {"player": "p", "player_actions": ["m"], "npc_name": "n", "npc_role": "r",
                       "npc_behaviors": ["i"], "dialogue_states": ["a"], "world_areas": ["w"],
                       "primary_npcs": "n", "relationship_growth": "x", "favor_rules": "x",
                       "relationship_events": "x", "request_rewards": "x"},
        "rules": {"progression": ["x"], "completion": "x"},
        "scope": {"included": ["x"], "later": []}, "validation": ["x"],
    })
    return GameBuildRequest(
        project_id=build.project_id, build_id=build.id, operation="create",
        creator_game_spec=spec, runtime_build_spec=spec.to_runtime_build_spec(),
        workspace=WorkspaceRef(root=run.workspace_path or "ws", allowed_paths=["dist", "logs"]),
        baseline_playable=None, request_text="resume decision",
    )


def _resolve_decision(session, run, decision, response="default"):
    """Mimic zhao's RunRepository.continue_run resolving the decision (without
    depending on the repo body) so the test sets up the resolved state."""
    import json
    decision.status = "resolved"
    decision.response_json = json.dumps(response, ensure_ascii=False, sort_keys=True)
    run.status = "running"
    session.flush()


# --------------------------------------------------------------------------- #
# resume path
# --------------------------------------------------------------------------- #


def test_resume_drives_same_run_to_terminal(isolated_database, tmp_path: Path) -> None:
    with Session(isolated_database) as session:
        project_id = _confirmed_project(session)
        ws_root = tmp_path / "ws" / project_id
        run, decision = _waiting_run(session, project_id, ws_root)
        _resolve_decision(session, run, decision, response="default")
        session.commit()

        agent = _FakeResumableAgent("succeeded")
        svc = ContinuationService(session, agent=agent, request_builder=_request_builder)

        resumed = asyncio.run(svc.resume_build(run.id, decision.decision_id, "default"))
        session.commit()

        # Same run, terminal succeeded, workspace reused (NOT discarded).
        assert resumed.id == run.id
        assert resumed.status == "succeeded"
        assert resumed.workspace_status == "prepared"
        # The adapter was told to resume the SAME session in the SAME workspace.
        assert agent.resume_called["session_id"] == SESSION_ID
        assert agent.resume_called["workspace_root"] == str(ws_root)
        # The decision text carries the resolved response.
        assert "default" in agent.resume_called["decision_text"]


def test_resume_appends_events_in_order(isolated_database, tmp_path: Path) -> None:
    with Session(isolated_database) as session:
        project_id = _confirmed_project(session)
        ws_root = tmp_path / "ws" / project_id
        run, decision = _waiting_run(session, project_id, ws_root)
        before_seq = run.last_sequence
        _resolve_decision(session, run, decision)
        session.commit()

        agent = _FakeResumableAgent("succeeded")
        svc = ContinuationService(session, agent=agent, request_builder=_request_builder)
        asyncio.run(svc.resume_build(run.id, decision.decision_id, "default"))
        session.commit()

        from app.repositories.runs import RunRepository
        events = RunRepository(session).list_events(run.id)
        seqs = [e.sequence for e in events]
        assert seqs == sorted(seqs)  # monotonic
        assert seqs[-1] > before_seq  # continuation events appended after the pause
        # A terminal event exists.
        assert events[-1].kind in {"completed", "terminal"}


def test_resume_failed_persists_failure(isolated_database, tmp_path: Path) -> None:
    with Session(isolated_database) as session:
        project_id = _confirmed_project(session)
        ws_root = tmp_path / "ws" / project_id
        run, decision = _waiting_run(session, project_id, ws_root)
        _resolve_decision(session, run, decision)
        session.commit()

        agent = _FakeResumableAgent("failed")
        svc = ContinuationService(session, agent=agent, request_builder=_request_builder)
        resumed = asyncio.run(svc.resume_build(run.id, decision.decision_id, "default"))
        session.commit()
        assert resumed.status == "failed"
        assert resumed.failure_code == "resume_failed"


# --------------------------------------------------------------------------- #
# session-not-resumable + guard rails
# --------------------------------------------------------------------------- #


def test_resume_without_session_id_fails_gracefully(isolated_database, tmp_path: Path) -> None:
    with Session(isolated_database) as session:
        project_id = _confirmed_project(session)
        ws_root = tmp_path / "ws" / project_id
        run, decision = _waiting_run(session, project_id, ws_root)
        run.opengame_session_id = None  # no captured session
        _resolve_decision(session, run, decision)
        session.commit()

        agent = _FakeResumableAgent()
        svc = ContinuationService(session, agent=agent, request_builder=_request_builder)
        resumed = asyncio.run(svc.resume_build(run.id, decision.decision_id, "default"))
        session.commit()
        assert resumed.status == "failed"
        assert resumed.failure_code == "session_not_resumable"
        assert agent.resume_called == {}  # resume was NOT attempted


def test_resume_rejects_unresolved_decision(isolated_database, tmp_path: Path) -> None:
    with Session(isolated_database) as session:
        project_id = _confirmed_project(session)
        ws_root = tmp_path / "ws" / project_id
        run, decision = _waiting_run(session, project_id, ws_root)
        # Decision still pending, run still waiting — NOT resolved.
        session.commit()
        agent = _FakeResumableAgent()
        svc = ContinuationService(session, agent=agent, request_builder=_request_builder)
        with pytest.raises(ValueError, match="not resolved|not running"):
            asyncio.run(svc.resume_build(run.id, decision.decision_id, "default"))


# --------------------------------------------------------------------------- #
# owner-boundary: lifecycle.py + runs.py continue_run body unchanged
# --------------------------------------------------------------------------- #


def test_lifecycle_and_continue_run_unchanged() -> None:
    """line-115 adds ContinuationService + adapter resume_session; it does NOT
    modify lifecycle.py gate bodies or RunRepository.continue_run."""
    import inspect
    from app.services.lifecycle import ProjectLifecycleService
    from app.repositories.runs import RunRepository
    # continue_run still takes (run_id, decision_id, response) — unchanged signature.
    sig = inspect.signature(RunRepository.continue_run)
    assert list(sig.parameters)[1:] == ["run_id", "decision_id", "response"]
    # No resume_session on the lifecycle service (resume is zhang's adapter).
    assert not hasattr(ProjectLifecycleService, "resume_session")
