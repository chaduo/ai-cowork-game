import asyncio

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.fake_candidate_test_runner import FakeCandidateTestRunner
from app.models import BuildCandidate, HumanPlayReview, PlayableVersion, Project, TestReport as ReportRecord
from app.services.candidate_tests import CandidateTestService
from app.services.lifecycle import ProjectLifecycleService
from app.services.builds import BuildService
from app.agents.fake_game_agent import FakeGameAgent
from tests.test_c12_candidate_test_gate import confirmed_project, create_candidate


def prepared_candidate(session: Session, *, fixture: str = "pass"):
    project = confirmed_project(session)
    candidate = create_candidate(session, project, artifact_path="dist/index.html")
    candidate.artifact_checksum = "a" * 64
    report = asyncio.run(CandidateTestService(session, FakeCandidateTestRunner(fixture)).test_candidate(candidate.id))
    return project, candidate, report


def accept_review(session: Session, candidate: BuildCandidate, **kwargs) -> HumanPlayReview:
    decision = kwargs.pop("decision", "accepted")
    return ProjectLifecycleService(session).record_human_play_review(
        candidate.id,
        decision=decision,
        notes="Played the candidate",
        **kwargs,
    )


def test_promote_requires_persisted_platform_pass_and_accepted_review(isolated_database) -> None:
    with Session(isolated_database) as session:
        project, candidate, report = prepared_candidate(session)
        service = ProjectLifecycleService(session)

        with pytest.raises(ValueError, match="Human Play Review"):
            service.promote_candidate(candidate.id, git_commit="abc123")

        accept_review(session, candidate)
        version = service.promote_candidate(candidate.id, git_commit="abc123")

        assert version.test_report_id == report.id
        assert version.artifact_checksum == "a" * 64
        assert session.get(Project, project.id).current_playable_version_id == version.id


@pytest.mark.parametrize(
    ("fixture", "review_kwargs", "message"),
    [
        ("runtime_only_pass", {}, "PASSED"),
        ("pass", {"decision": "rejected"}, "accepted"),
        ("pass", {"amendment_status": "unconfirmed"}, "Amendment"),
        ("pass", {"drift_status": "unresolved"}, "drift"),
    ],
)
def test_promote_rejects_incomplete_or_blocked_gates(isolated_database, fixture, review_kwargs, message) -> None:
    with Session(isolated_database) as session:
        project, candidate, _ = prepared_candidate(session, fixture=fixture)
        if fixture == "runtime_only_pass":
            accept_review(session, candidate)
        else:
            accept_review(session, candidate, **review_kwargs)
        with pytest.raises(ValueError, match=message):
            ProjectLifecycleService(session).promote_candidate(candidate.id, git_commit="abc123")
        assert session.get(Project, project.id).current_playable_version_id is None


def test_promote_requires_candidate_checksum_and_is_idempotent(isolated_database) -> None:
    with Session(isolated_database) as session:
        project, candidate, _ = prepared_candidate(session)
        candidate.artifact_checksum = None
        accept_review(session, candidate)
        with pytest.raises(ValueError, match="checksum"):
            ProjectLifecycleService(session).promote_candidate(candidate.id, git_commit="abc123")

        candidate.artifact_checksum = "b" * 64
        service = ProjectLifecycleService(session)
        first = service.promote_candidate(candidate.id, git_commit="abc123")
        second = service.promote_candidate(candidate.id, git_commit="ignored")
        assert first.id == second.id
        assert session.scalar(select(func.count(PlayableVersion.id)).where(PlayableVersion.project_id == project.id)) == 1


def test_restore_creates_new_untested_candidate_and_preserves_history(isolated_database) -> None:
    with Session(isolated_database) as session:
        project, candidate, _ = prepared_candidate(session)
        accept_review(session, candidate)
        service = ProjectLifecycleService(session)
        version = service.promote_candidate(candidate.id, git_commit="abc123")
        session.commit()

        restored = service.restore_playable_version(project.id, version.id)
        repeated = service.restore_playable_version(project.id, version.id)

        assert restored.id == repeated.id
        assert restored.id != candidate.id
        assert restored.source_playable_version_id == version.id
        assert restored.test_gate_status == "untested"
        assert restored.status == "succeeded"
        assert session.get(Project, project.id).current_playable_version_id == version.id
        assert session.scalar(select(func.count(PlayableVersion.id)).where(PlayableVersion.project_id == project.id)) == 1
        assert session.scalar(select(func.count(ReportRecord.id)).where(ReportRecord.candidate_id == restored.id)) == 0


def test_restore_rejects_cross_project_version(isolated_database) -> None:
    with Session(isolated_database) as session:
        first, candidate, _ = prepared_candidate(session)
        accept_review(session, candidate)
        service = ProjectLifecycleService(session)
        version = service.promote_candidate(candidate.id, git_commit="abc123")
        second = confirmed_project(session)

        with pytest.raises(ValueError, match="project"):
            service.restore_playable_version(second.id, version.id)
