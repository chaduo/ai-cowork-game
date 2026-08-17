import asyncio

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.fake_candidate_test_runner import FakeCandidateTestRunner
from app.services.candidate_tests import CandidateTestService
import pytest

from app.models import Build, BuildCandidate, PlayableVersion, Project, Release
from app.services.lifecycle import ProjectLifecycleService, ProjectStage

from tests.test_c02_build_service import confirmed_service


def test_promote_requires_pass_and_publish_is_explicit(isolated_database) -> None:
    with Session(isolated_database) as session:
        service, project = confirmed_service(session)
        build = service.start_build(project.id)
        candidate = service.finish_build(build.id, "succeeded", summary="ready", artifact_path="dist/index.html")
        assert service.derive_project_stage(project.id) == ProjectStage.CANDIDATE_REVIEW
        candidate.artifact_checksum = "a" * 64
        asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("pass")).test_candidate(candidate.id))
        service.record_human_play_review(candidate.id, decision="accepted")

        version = service.promote_candidate(
            candidate.id,
            git_commit="abc123",
        )
        assert session.get(Project, project.id).current_playable_version_id == version.id
        assert service.derive_project_stage(project.id) == ProjectStage.PLAYABLE
        release = service.publish_version(version.id)
        assert release.playable_version_id == version.id
        assert service.derive_project_stage(project.id) == ProjectStage.PUBLISHED


def test_promotion_rejects_non_passing_verdict(isolated_database) -> None:
    with Session(isolated_database) as session:
        service, project = confirmed_service(session)
        build = service.start_build(project.id)
        candidate = service.finish_build(build.id, "succeeded", summary="ready", artifact_path="dist/index.html")
        candidate.artifact_checksum = "a" * 64
        asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("console_failure")).test_candidate(candidate.id))

        with pytest.raises(ValueError, match="PASSED"):
            service.promote_candidate(
                candidate.id,
                git_commit="abc123",
            )


def test_failed_candidate_cannot_promote_and_recovery_is_idempotent(isolated_database) -> None:
    with Session(isolated_database) as session:
        service, project = confirmed_service(session)
        build = service.start_build(project.id)
        build.status = "running"
        candidate = BuildCandidate(
            project_id=project.id,
            build_id=build.id,
            status="failed",
            summary="failed",
        )
        session.add(candidate)
        project.active_build_id = build.id
        session.flush()

        service.recover_orphaned_builds()
        service.recover_orphaned_builds()
        session.expire_all()
        assert session.get(Build, build.id).status == "orphaned"
        assert session.get(Project, project.id).active_build_id is None
        assert session.scalar(select(PlayableVersion).where(PlayableVersion.project_id == project.id)) is None
        assert session.scalar(select(Release).where(Release.project_id == project.id)) is None
