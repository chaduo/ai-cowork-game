"""C13 — BuildService workspace lifecycle integration (cancel/retry/orphan cleanup).

Exercises the run-observability spec requirement "cancel an active runtime and its
child work, preserve diagnostics, and allow retry ... without reusing an untrusted
partial workspace" at the BuildService level, using the deterministic FakeGameAgent
and a tmp-rooted WorkspaceManager (no real disk under data/workspaces).

Covers task 4.1's cancellation-cleanup half: a partial workspace left by cancel,
failure, timeout, invalid_output, or an orphaned run is discarded and never trusted
or reused on retry.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.fake_game_agent import FakeGameAgent
from app.agents.workspace import WorkspaceManager
from app.models import Build, Run
from app.services.builds import BuildService
from tests.test_c11_build_orchestration import confirmed_project


def _service(session: Session, tmp_path: Path, outcomes=None) -> BuildService:
    """A BuildService whose workspaces live under tmp_path (no data/workspaces)."""
    return BuildService(
        session,
        FakeGameAgent(outcomes or {}),
        workspace_manager=WorkspaceManager(root_base=tmp_path / "ws"),
    )


def _run_for(session: Session, build_id: str) -> Run:
    return session.scalar(select(Run).where(Run.build_id == build_id).order_by(Run.created_at.desc()))


# --------------------------------------------------------------------------- #
# success keeps the workspace; non-success discards it
# --------------------------------------------------------------------------- #


def test_execute_build_prepares_isolated_workspace(isolated_database, tmp_path: Path) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        service = _service(session, tmp_path)
        job = service.create_build(project.id, build_id="b-ok", run_id="run-ok")
        asyncio.run(service.execute_build(job.build_id))
        run = _run_for(session, job.build_id)
        assert run.workspace_path is not None
        assert run.workspace_status == "prepared"  # success keeps the workspace
        assert Path(run.workspace_path).is_dir()


@pytest.mark.parametrize("outcome,status", [
    ({"create": "failed"}, "failed"),
    ({"create": "timed_out"}, "timed_out"),
    ({"create": "invalid_output"}, "invalid_output"),
])
def test_non_success_discards_partial_workspace(isolated_database, tmp_path, outcome, status) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        service = _service(session, tmp_path, outcome)
        job = service.create_build(project.id, build_id=f"b-{status}", run_id=f"run-{status}")
        asyncio.run(service.execute_build(job.build_id))
        run = _run_for(session, job.build_id)
        assert run.workspace_status == "discarded"
        # The partial workspace dir is gone — not trusted for reuse.
        if run.workspace_path:
            assert not Path(run.workspace_path).exists()


# --------------------------------------------------------------------------- #
# cancel discards the partial workspace
# --------------------------------------------------------------------------- #


def test_cancel_discards_partial_workspace(isolated_database, tmp_path: Path) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        service = _service(session, tmp_path)
        job = service.create_build(project.id, build_id="b-cancel", run_id="run-cancel")
        asyncio.run(service.execute_build(job.build_id))  # build first (succeeds)
        # Now cancel a fresh build to exercise the cancel path end-to-end.
        job2 = service.create_build(project.id, build_id="b-cancel2", run_id="run-cancel2")
        asyncio.run(service.cancel_build(job2.build_id))
        run2 = _run_for(session, job2.build_id)
        assert run2.status == "cancelled"
        assert run2.workspace_status == "discarded"
        if run2.workspace_path:
            assert not Path(run2.workspace_path).exists()


# --------------------------------------------------------------------------- #
# retry gets a fresh workspace; the prior partial is never reused
# --------------------------------------------------------------------------- #


def test_retry_uses_fresh_workspace_not_prior_partial(isolated_database, tmp_path: Path) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)

        class _FailFirstThenSucceed(FakeGameAgent):
            """First create fails (partial workspace); the retry succeeds (kept)."""
            def __init__(self):
                super().__init__({"create": "failed"})
                self._calls = 0

            async def start(self, request):
                self._calls += 1
                if self._calls > 1:
                    self._outcomes = {}  # retry succeeds
                return await super().start(request)

        service = BuildService(
            session, _FailFirstThenSucceed(), workspace_manager=WorkspaceManager(root_base=tmp_path / "ws")
        )
        job = service.create_build(project.id, build_id="b-retry", run_id="run-retry")
        asyncio.run(service.execute_build(job.build_id))
        prior_run = _run_for(session, job.build_id)
        assert prior_run.workspace_status == "discarded"  # failed -> discarded

        # Retry: a fresh run_id -> a fresh workspace, never the prior partial.
        retry_job = service.retry_build(job.build_id)
        asyncio.run(service.execute_build(retry_job.build_id))
        retry_run = _run_for(session, retry_job.build_id)
        assert retry_run.workspace_path is not None
        assert prior_run.workspace_path != retry_run.workspace_path  # fresh, not reused
        assert retry_run.workspace_status == "prepared"  # succeeded -> kept
        assert Path(retry_run.workspace_path).is_dir()
        # The prior partial workspace remains gone.
        if prior_run.workspace_path:
            assert not Path(prior_run.workspace_path).exists()


# --------------------------------------------------------------------------- #
# orphan recovery discards a lingering prepared workspace
# --------------------------------------------------------------------------- #


def test_orphan_recovery_discards_lingering_workspace(isolated_database, tmp_path: Path) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        service = _service(session, tmp_path)
        job = service.create_build(project.id, build_id="b-orphan", run_id="run-orphan")
        # Simulate the run being interrupted by a restart: prepare a workspace but
        # mark the run orphaned (recover_orphaned_runs would set this on startup).
        run = _run_for(session, job.build_id)
        paths = service._workspace.prepare(run.id, run.id)
        run.workspace_path = str(paths.root)
        run.workspace_status = "prepared"
        run.status = "orphaned"
        session.flush()
        assert Path(run.workspace_path).is_dir()

        recovered = service.recover_orphaned_jobs()
        session.flush()
        run = _run_for(session, job.build_id)
        assert run.workspace_status == "discarded"
        assert not Path(run.workspace_path).exists()
        assert recovered >= 1
