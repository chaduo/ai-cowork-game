import asyncio

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.fake_candidate_test_runner import FakeCandidateTestRunner
from app.agents.fake_game_agent import FakeGameAgent
from app.models import Build, BuildCandidate, GameSpecRevision, Project, TestEvidence as EvidenceRecord, TestReport as ReportRecord
from app.services.builds import BuildService
from app.services.candidate_tests import CandidateTestService
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


def successful_candidate(session: Session, project: Project) -> BuildCandidate:
    job = BuildService(session, FakeGameAgent()).create_build(project.id)
    asyncio.run(BuildService(session, FakeGameAgent()).execute_build(job.build_id))
    return session.scalar(select(BuildCandidate).where(BuildCandidate.build_id == job.build_id))


def create_candidate(session: Session, project: Project, *, build_status: str = "succeeded", artifact_path: str | None = "dist/index.html") -> BuildCandidate:
    revision = session.scalar(select(GameSpecRevision).where(GameSpecRevision.project_id == project.id).order_by(GameSpecRevision.revision_number.desc()))
    if revision is None:
        revision = ProjectLifecycleService(session).create_gamespec_revision(project.id, valid_gamespec())
        revision.status = "confirmed"
        session.flush()
    build = Build(project_id=project.id, gamespec_revision_id=revision.id, status=build_status)
    session.add(build)
    session.flush()
    candidate = BuildCandidate(project_id=project.id, build_id=build.id, status=build_status, artifact_path=artifact_path, summary="candidate")
    session.add(candidate)
    session.flush()
    return candidate


def test_complete_evidence_marks_candidate_ready(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        candidate = successful_candidate(session, project)
        report = asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("pass")).test_candidate(candidate.id))
        session.commit()

        assert report.status == "pass"
        assert report.platform_verdict == "pass"
        assert session.get(BuildCandidate, candidate.id).test_gate_status == "ready"
        assert {item.kind for item in report.evidence} == {"browser_started", "console", "core_input", "gameplay", "completion"}


@pytest.mark.parametrize("fixture,expected", [("runtime_only_pass", "invalid"), ("missing_evidence", "invalid"), ("contradictory", "invalid"), ("console_failure", "fail"), ("completion_failure", "fail")])
def test_incomplete_or_conflicting_evidence_cannot_be_ready(isolated_database, fixture: str, expected: str) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        candidate = successful_candidate(session, project)
        report = asyncio.run(CandidateTestService(session, FakeCandidateTestRunner(fixture)).test_candidate(candidate.id))
        session.commit()

        assert report.status == expected
        assert report.platform_verdict == expected
        assert session.get(BuildCandidate, candidate.id).test_gate_status in {"failed", "invalid"}


def test_build_failure_and_missing_artifact_cannot_be_ready(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        failed = create_candidate(session, project, build_status="failed", artifact_path=None)
        failed_report = asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("pass")).test_candidate(failed.id))
        missing_artifact = create_candidate(session, project, artifact_path=None)
        missing_report = asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("pass")).test_candidate(missing_artifact.id))
        session.commit()

        assert failed_report.status == missing_report.status == "invalid"
        assert session.get(BuildCandidate, failed.id).test_gate_status == "invalid"
        assert session.get(BuildCandidate, missing_artifact.id).test_gate_status == "invalid"


def test_retesting_candidate_returns_immutable_report_and_does_not_touch_current_playable(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        project.current_playable_version_id = "playable-before-test"
        candidate = successful_candidate(session, project)
        service = CandidateTestService(session, FakeCandidateTestRunner("pass"))
        first = asyncio.run(service.test_candidate(candidate.id))
        second = asyncio.run(service.test_candidate(candidate.id))
        report_count = session.scalar(select(func.count(ReportRecord.id)).where(ReportRecord.candidate_id == candidate.id))
        evidence_count = session.scalar(select(func.count(EvidenceRecord.id)).where(EvidenceRecord.test_report_id == first.id))
        session.commit()

        assert first.id == second.id
        assert report_count == 1
        assert evidence_count == 5
        assert session.get(Project, project.id).current_playable_version_id == "playable-before-test"


def test_repair_links_new_candidate_without_overwriting_failed_parent(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = confirmed_project(session)
        parent = create_candidate(session, project)
        asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("console_failure")).test_candidate(parent.id))
        replacement = create_candidate(session, project)

        linked = CandidateTestService(session, FakeCandidateTestRunner("pass")).link_repair_candidate(parent.id, replacement.id)
        session.commit()

        assert linked.parent_candidate_id == parent.id
        assert linked.attempt == parent.attempt + 1
        assert session.get(BuildCandidate, parent.id).parent_candidate_id is None
        assert session.get(BuildCandidate, parent.id).test_gate_status == "failed"


def test_repair_rejects_successful_parent_cross_project_and_tested_replacement(isolated_database) -> None:
    with Session(isolated_database) as session:
        first_project = confirmed_project(session)
        second_project = confirmed_project(session)
        successful_parent = create_candidate(session, first_project)
        cross_project = create_candidate(session, second_project)
        tested_replacement = create_candidate(session, first_project)
        asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("pass")).test_candidate(tested_replacement.id))
        service = CandidateTestService(session, FakeCandidateTestRunner("pass"))

        with pytest.raises(ValueError, match="failed or invalid"):
            service.link_repair_candidate(successful_parent.id, cross_project.id)
        failed_parent = create_candidate(session, first_project)
        asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("console_failure")).test_candidate(failed_parent.id))
        with pytest.raises(ValueError, match="already linked or tested"):
            service.link_repair_candidate(failed_parent.id, tested_replacement.id)
