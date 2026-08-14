import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Build, BuildCandidate, Project
from app.services.lifecycle import ProjectLifecycleService
from tests.test_c05_design_api import draft_payload
from tests.test_c05_gamespec_contract import valid_gamespec


def confirmed_service(session: Session) -> tuple[ProjectLifecycleService, Project]:
    service = ProjectLifecycleService(session)
    project = service.create_project("Garden", "A quiet garden game")
    service.submit_design(project.id, draft_payload())
    service.confirm_design(project.id)
    revision = service.create_gamespec_revision(project.id, valid_gamespec())
    service.confirm_gamespec_revision(project.id, revision.id)
    return service, project


def test_build_requires_confirmed_gamespec_and_guards_concurrency(isolated_database) -> None:
    with Session(isolated_database) as session:
        service = ProjectLifecycleService(session)
        project = service.create_project("Garden", "A quiet garden game")
        with pytest.raises(ValueError, match="confirmed"):
            service.start_build(project.id, "missing-revision")

        service, project = confirmed_service(session)
        first = service.start_build(project.id)
        assert first.status == "running"
        assert session.get(Project, project.id).active_build_id == first.id
        with pytest.raises(ValueError, match="active build"):
            service.start_build(project.id)


def test_failed_cancelled_and_successful_builds_create_candidates_without_promoting(isolated_database) -> None:
    with Session(isolated_database) as session:
        service, project = confirmed_service(session)

        failed = service.start_build(project.id)
        failed_candidate = service.finish_build(failed.id, "failed", summary="compile failed")
        cancelled = service.start_build(project.id)
        cancelled_candidate = service.finish_build(cancelled.id, "cancelled", summary="user stopped")
        succeeded = service.start_build(project.id)
        succeeded_candidate = service.finish_build(succeeded.id, "succeeded", summary="ready", artifact_path="artifacts/v1")

        assert {failed_candidate.status, cancelled_candidate.status, succeeded_candidate.status} == {"failed", "cancelled", "succeeded"}
        assert session.get(Project, project.id).current_playable_version_id is None
        assert session.scalar(select(BuildCandidate).where(BuildCandidate.id == succeeded_candidate.id)).status == "succeeded"


def test_projects_have_independent_active_build_guards(isolated_database) -> None:
    with Session(isolated_database) as session:
        service, first_project = confirmed_service(session)
        second_project = service.create_project("River", "A river game")
        service.submit_design(second_project.id, draft_payload())
        service.confirm_design(second_project.id)
        revision = service.create_gamespec_revision(second_project.id, valid_gamespec())
        service.confirm_gamespec_revision(second_project.id, revision.id)

        first_build = service.start_build(first_project.id)
        second_build = service.start_build(second_project.id)

        assert first_build.project_id != second_build.project_id
        assert session.get(Project, first_project.id).active_build_id == first_build.id
        assert session.get(Project, second_project.id).active_build_id == second_build.id


def test_cancel_and_retry_create_a_new_build_chain(isolated_database) -> None:
    with Session(isolated_database) as session:
        service, project = confirmed_service(session)
        first = service.start_build(project.id)
        service.cancel_build(first.id, summary="user stopped")

        retry = service.retry_build(first.id)

        assert retry.parent_build_id == first.id
        assert retry.attempt == first.attempt + 1
        assert retry.status == "running"
        assert session.get(Project, project.id).active_build_id == retry.id
