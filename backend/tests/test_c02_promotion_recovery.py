from sqlalchemy import select
from sqlalchemy.orm import Session
import pytest

from app.models import Build, BuildCandidate, PlayableVersion, Project, Release
from app.services.lifecycle import ProjectLifecycleService, ProjectStage

from tests.test_c02_build_service import confirmed_service


def test_promote_requires_pass_and_publish_is_explicit(isolated_database) -> None:
    with Session(isolated_database) as session:
        service, project = confirmed_service(session)
        build = service.start_build(project.id)
        candidate = service.finish_build(build.id, "succeeded", summary="ready", artifact_path="artifacts/v1")
        assert service.derive_project_stage(project.id) == ProjectStage.CANDIDATE_REVIEW

        version = service.promote_candidate(
            candidate.id,
            test_report_id="report-1",
            verdict="pass",
            git_commit="abc123",
            artifact_checksum="sha256:one",
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
        candidate = service.finish_build(build.id, "succeeded", summary="ready", artifact_path="artifacts/v1")

        with pytest.raises(ValueError, match="passing"):
            service.promote_candidate(
                candidate.id,
                test_report_id="report-fail",
                verdict="fail",
                git_commit="abc123",
                artifact_checksum="sha256:one",
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
