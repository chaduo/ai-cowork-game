import asyncio
import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.fake_game_agent import FakeGameAgent
from app.contracts.game_agent import ArtifactManifestEntry, AffectedScope, BuildOverride, GameBuildResult, ResourceReference, RunEvent
from app.models import Build, BuildCandidate, BuildContext, Project, Run
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


def test_build_context_is_immutable_and_candidate_provenance_is_linked(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        project.current_playable_version_id = "playable-before-context"
        agent = FakeGameAgent()
        service = BuildService(session, agent)
        scope = AffectedScope(sections=["gameplay", "characters"], description="关系玩法 first playable")
        resources = [ResourceReference(
            resource_id="relationship-system",
            resource_revision="resource-rev-1",
            source_project_id="source-project-1",
            source_release_id="release-1",
            snapshot_hash="a" * 64,
            role="gameplay-module",
        )]
        overrides = [BuildOverride(
            key="max_favor",
            value=100,
            source="resource",
            provenance="resource-rev-1",
        )]
        job = service.create_build(
            project.id,
            affected_scope=scope,
            resource_references=resources,
            implementation_dependencies=["relationship-events:v1"],
            relevant_overrides=overrides,
        )
        context = session.scalar(select(BuildContext).where(BuildContext.build_id == job.build_id))
        assert context is not None
        original_hashes = (context.context_hash, context.gamespec_snapshot_hash, context.runtime_build_spec_hash)
        original_snapshot = context.gamespec_snapshot_json

        project.current_playable_version_id = "playable-after-context"
        later_spec = valid_gamespec()
        later_spec["title"] = "后来编辑的游戏"
        later_revision = service.lifecycle.create_gamespec_revision(project.id, later_spec)
        service.lifecycle.confirm_gamespec_revision(project.id, later_revision.id)
        service.lifecycle._design(project.id).status = "draft"
        request = service._request_for(session.get(Build, job.build_id), session.get(Run, job.run_id))
        result = asyncio.run(service.execute_build(job.build_id))
        session.commit()

        candidate = session.scalar(select(BuildCandidate).where(BuildCandidate.build_id == job.build_id))
        refreshed = session.get(BuildContext, context.id)
        assert result.status == "succeeded"
        assert candidate is not None and candidate.build_context_id == context.id
        assert refreshed is not None
        assert (refreshed.context_hash, refreshed.gamespec_snapshot_hash, refreshed.runtime_build_spec_hash) == original_hashes
        assert refreshed.gamespec_snapshot_json == original_snapshot
        assert request.creator_game_spec.title == "多代田园物语"
        assert request.affected_scope == scope
        assert request.resource_references == resources
        assert request.implementation_dependencies == ["relationship-events:v1"]
        assert request.relevant_overrides == overrides
        assert agent.requests[0].build_id == job.build_id


def test_duplicate_build_request_cannot_replace_existing_context(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        service = BuildService(session, FakeGameAgent())
        first = service.create_build(
            project.id,
            build_id="context-idempotent-build",
            run_id="context-idempotent-run",
            affected_scope=AffectedScope(sections=["first"]),
        )
        context = session.scalar(select(BuildContext).where(BuildContext.build_id == first.build_id))
        duplicate = service.create_build(
            project.id,
            build_id="context-idempotent-build",
            run_id="context-idempotent-run",
            affected_scope=AffectedScope(sections=["replacement"]),
        )

        assert duplicate == first
        assert session.scalar(select(BuildContext).where(BuildContext.build_id == first.build_id)).id == context.id
        assert json.loads(context.affected_scope_json)["sections"] == ["first"]


def test_retry_copies_context_without_mutating_parent(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        service = BuildService(session, FakeGameAgent({"modify": "failed"}))
        first = service.create_build(
            project.id,
            operation="modify",
            affected_scope=AffectedScope(sections=["characters"]),
            implementation_dependencies=["npc-runtime:v2"],
        )
        asyncio.run(service.execute_build(first.build_id))
        retry = service.retry_build(first.build_id)
        session.commit()

        parent_context = session.scalar(select(BuildContext).where(BuildContext.build_id == first.build_id))
        retry_context = session.scalar(select(BuildContext).where(BuildContext.build_id == retry.build_id))
        assert parent_context is not None and retry_context is not None
        assert retry_context.id != parent_context.id
        assert retry_context.context_hash == parent_context.context_hash
        assert retry_context.affected_scope_json == parent_context.affected_scope_json
        assert retry_context.implementation_dependencies_json == parent_context.implementation_dependencies_json


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
        assert json.loads(candidate.artifact_manifest_json) == [
            {
                "path": "dist/index.html",
                "kind": "preview_entry",
                "size_bytes": 1200,
                "sha256": "0" * 64,
            }
        ]
        assert session.get(Project, project.id).current_playable_version_id is None
        assert session.get(Run, job.run_id).status == "succeeded"


def test_success_result_normalizes_provider_terminal_event_with_artifact(isolated_database) -> None:
    """A provider terminal event is not allowed to hide a successful artifact."""
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        service = BuildService(session, FakeGameAgent())
        job = service.create_build(project.id)
        build = session.get(Build, job.build_id)
        run = session.get(Run, job.run_id)
        assert build is not None and run is not None

        provider_terminal = RunEvent(
            run_id=run.id,
            sequence=1,
            stage="terminal",
            kind="terminal",
            message="build completed",
            progress=1,
            timestamp=datetime.now(timezone.utc),
        )
        result = GameBuildResult(
            status="succeeded",
            artifact_manifest=[ArtifactManifestEntry(path="dist/index.html", kind="html")],
            preview_entry="dist/index.html",
        )

        persisted = service._persist_result(build, run, result, provider_terminal)
        session.commit()

        assert persisted.status == "succeeded"
        events = service.runs.list_events(run.id)
        assert events[-1].kind == "completed"
        assert events[-1].artifact_ref == "dist/index.html"


def test_non_success_result_normalizes_provider_terminal_error(isolated_database) -> None:
    """A generic provider terminal event must not erase the platform error."""
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        service = BuildService(session, FakeGameAgent())
        job = service.create_build(project.id)
        build = session.get(Build, job.build_id)
        run = session.get(Run, job.run_id)
        assert build is not None and run is not None

        provider_terminal = RunEvent(
            run_id=run.id,
            sequence=1,
            stage="terminal",
            kind="terminal",
            message="build completed",
            progress=1,
            timestamp=datetime.now(timezone.utc),
        )
        result = GameBuildResult(
            status="invalid_output",
            error={"code": "invalid_artifact", "message": "index.html is missing"},
        )

        persisted = service._persist_result(build, run, result, provider_terminal)
        session.commit()

        assert persisted.status == "invalid_output"
        events = service.runs.list_events(run.id)
        assert events[-1].error is not None
        assert events[-1].error.code == "invalid_artifact"


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
