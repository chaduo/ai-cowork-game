from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.models import Build, BuildCandidate, GameSpecRevision, Project, TestEvidence as EvidenceRecord, TestReport as ReportRecord


def test_c12_migration_creates_test_gate_tables_and_candidate_columns(isolated_database) -> None:
    inspector = inspect(isolated_database)
    assert {"test_reports", "test_evidence"}.issubset(set(inspector.get_table_names()))
    candidate_columns = {column["name"] for column in inspector.get_columns("build_candidates")}
    assert {"test_gate_status", "parent_candidate_id", "attempt", "repair_round"}.issubset(candidate_columns)


def test_c12_records_reload_with_repair_ancestry_and_evidence(isolated_database) -> None:
    with Session(isolated_database) as session:
        project = Project(name="Garden", original_idea="A quiet garden game")
        session.add(project)
        session.flush()
        revision = GameSpecRevision(project_id=project.id, revision_number=1, content_json="{}", status="confirmed")
        session.add(revision)
        session.flush()
        build = Build(project_id=project.id, gamespec_revision_id=revision.id, status="succeeded")
        session.add(build)
        session.flush()
        parent = BuildCandidate(project_id=project.id, build_id=build.id, status="succeeded", summary="failed test", test_gate_status="failed")
        session.add(parent)
        session.flush()
        replacement_build = Build(project_id=project.id, gamespec_revision_id=revision.id, status="succeeded")
        session.add(replacement_build)
        session.flush()
        replacement = BuildCandidate(
            project_id=project.id,
            build_id=replacement_build.id,
            status="succeeded",
            summary="repair",
            parent_candidate_id=parent.id,
            attempt=2,
        )
        session.add(replacement)
        session.flush()
        report = ReportRecord(
            candidate_id=replacement.id,
            runtime_verdict="pass",
            platform_verdict="PASSED",
            status="PASSED",
            severity="none",
            summary="all checks passed",
        )
        session.add(report)
        session.flush()
        session.add(EvidenceRecord(
            test_report_id=report.id,
            kind="browser_started",
            status="passed",
            source="platform",
            severity="critical",
            expected="browser starts",
            observed="browser started",
            artifact_ref="dist/index.html",
        ))
        session.commit()

        loaded = session.scalar(select(BuildCandidate).where(BuildCandidate.id == replacement.id))
        loaded_report = session.scalar(select(ReportRecord).where(ReportRecord.candidate_id == replacement.id))
        assert loaded.parent_candidate_id == parent.id
        assert loaded.attempt == 2
        assert loaded_report.status == "PASSED"
        assert loaded_report.severity == "none"
        assert loaded_report.evidence[0].kind == "browser_started"
        assert loaded_report.evidence[0].source == "platform"
