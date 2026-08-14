import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.fake_game_agent import FakeGameAgent
from app.models import Build, BuildCandidate, Project, Run
from app.services.builds import BuildService
from app.services.lifecycle import ProjectLifecycleService
from tests.test_c05_design_api import draft_payload
from tests.test_c05_gamespec_contract import valid_gamespec


def confirmed_project(session: Session) -> Project:
    lifecycle = ProjectLifecycleService(session)
    project = lifecycle.create_project("Garden", "A quiet garden game")
    lifecycle.submit_design(project.id, draft_payload())
    lifecycle.confirm_design(project.id)
    revision = lifecycle.create_gamespec_revision(project.id, valid_gamespec())
    lifecycle.confirm_gamespec_revision(project.id, revision.id)
    session.commit()
    return project


def test_create_build_captures_confirmed_input_and_stable_ids(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        agent = FakeGameAgent()
        service = BuildService(session, agent)

        job = service.create_build(project.id, build_id="build-c11-1", run_id="run-c11-1")
        session.commit()
        build = session.get(Build, job.build_id)
        run = session.get(Run, job.run_id)

        assert build is not None
        assert build.gamespec_revision_id
        assert build.operation == "create"
        assert run is not None and run.build_id == build.id
        assert job.build_id == "build-c11-1"
        assert job.run_id == "run-c11-1"


def test_build_captures_baseline_playable_pointer_once(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        project.current_playable_version_id = "playable-before-build"
        session.flush()
        service = BuildService(session, FakeGameAgent())

        job = service.create_build(project.id)
        project.current_playable_version_id = "playable-changed-later"
        session.flush()

        build = session.get(Build, job.build_id)
        assert build.baseline_playable_version_id == "playable-before-build"


def test_duplicate_create_is_idempotent_and_does_not_start_second_agent_run(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        agent = FakeGameAgent()
        service = BuildService(session, agent)

        first = service.create_build(project.id, build_id="same-build", run_id="same-run")
        second = service.create_build(project.id, build_id="same-build", run_id="same-run")

        assert first == second
        assert len(agent.requests) == 0
        assert session.scalar(select(Build).where(Build.project_id == project.id)).id == "same-build"


def test_success_creates_candidate_without_promoting_current_playable(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        service = BuildService(session, FakeGameAgent())
        job = service.create_build(project.id)
        result = asyncio.run(service.execute_build(job.build_id))
        session.commit()

        candidate = session.scalar(select(BuildCandidate).where(BuildCandidate.build_id == job.build_id))
        assert result.status == "succeeded"
        assert candidate is not None and candidate.status == "succeeded"
        assert candidate.artifact_path == "dist/index.html"
        assert session.get(Project, project.id).current_playable_version_id is None
        assert session.get(Run, job.run_id).status == "succeeded"


def test_waiting_build_is_persisted_and_duplicate_execution_does_not_start_provider_again(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        agent = FakeGameAgent({"create": "waiting_for_input"})
        service = BuildService(session, agent)
        job = service.create_build(project.id)

        first = asyncio.run(service.execute_build(job.build_id))
        second = asyncio.run(service.execute_build(job.build_id))
        session.commit()

        assert first.status == second.status == "waiting_for_input"
        assert first.pending_decision is not None
        assert second.pending_decision is not None
        assert len(agent.requests) == 1
        assert session.get(Run, job.run_id).status == "waiting_for_input"


@pytest.mark.parametrize("operation,status", [("modify", "failed"), ("modify", "timed_out"), ("bad", "unsupported")])
def test_non_success_keeps_diagnostics_and_does_not_promote(isolated_database, operation: str, status: str) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        service = BuildService(session, FakeGameAgent({operation: status}))
        job = service.create_build(project.id, operation=operation)
        result = asyncio.run(service.execute_build(job.build_id))
        session.commit()

        candidate = session.scalar(select(BuildCandidate).where(BuildCandidate.build_id == job.build_id))
        build = session.get(Build, job.build_id)
        assert result.status == status
        assert candidate is not None and candidate.status == status
        assert candidate.diagnostics_json
        assert build.failure_code
        assert session.get(Project, project.id).current_playable_version_id is None


def test_cancel_retry_creates_new_run_and_preserves_parent(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        agent = FakeGameAgent()
        service = BuildService(session, agent)
        first = service.create_build(project.id)
        cancelled = asyncio.run(service.cancel_build(first.build_id))
        retry = service.retry_build(first.build_id)
        session.commit()

        assert cancelled.status == "cancelled"
        assert retry.build_id != first.build_id
        assert retry.run_id != first.run_id
        assert session.get(Build, retry.build_id).parent_build_id == first.build_id
        assert session.get(Project, project.id).active_build_id == retry.build_id


def test_recovery_orphans_build_and_run_after_restart(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        service = BuildService(session, FakeGameAgent())
        job = service.create_build(project.id)
        session.commit()

        assert service.recover_orphaned_jobs() == 1
        session.commit()
        assert session.get(Build, job.build_id).status == "orphaned"
        assert session.get(Run, job.run_id).status == "orphaned"
        assert session.get(Project, project.id).active_build_id is None
