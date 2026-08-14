import json
from datetime import datetime

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.fake_candidate_test_runner import FakeCandidateTestRunner
from app.errors import ApiError
from app.models import BuildCandidate, TestReport
from app.services.candidate_tests import CandidateTestService


router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])


class RepairLinkRequest(BaseModel):
    replacement_candidate_id: str = Field(min_length=1, max_length=36)


class EvidenceResponse(BaseModel):
    id: str
    kind: str
    status: str
    source: str
    severity: str
    expected: str
    observed: str
    artifact_ref: str
    details: dict = Field(default_factory=dict)


class TestReportResponse(BaseModel):
    id: str
    candidate_id: str
    runtime_verdict: str
    platform_verdict: str
    status: str
    severity: str
    summary: str
    diagnostics: list[dict] = Field(default_factory=list)
    created_at: datetime
    evidence: list[EvidenceResponse] = Field(default_factory=list)


class CandidateResponse(BaseModel):
    candidate_id: str
    project_id: str
    build_id: str
    build_status: str
    test_gate_status: str
    parent_candidate_id: str | None
    attempt: int
    repair_round: int
    report: TestReportResponse | None = None


def _session(request: Request) -> Session:
    return Session(request.app.state.engine)


def _candidate(session: Session, candidate_id: str) -> BuildCandidate:
    candidate = session.get(BuildCandidate, candidate_id)
    if candidate is None:
        raise ApiError("candidate_not_found", "Candidate not found", [], 404)
    return candidate


def _report_response(report: TestReport) -> TestReportResponse:
    diagnostics = json.loads(report.diagnostics_json) if report.diagnostics_json else []
    return TestReportResponse(
        id=report.id,
        candidate_id=report.candidate_id,
        runtime_verdict=report.runtime_verdict,
        platform_verdict=report.platform_verdict,
        status=report.status,
        severity=report.severity,
        summary=report.summary,
        diagnostics=diagnostics,
        created_at=report.created_at,
        evidence=[EvidenceResponse(
            id=item.id,
            kind=item.kind,
            status=item.status,
            source=item.source,
            severity=item.severity,
            expected=item.expected,
            observed=item.observed,
            artifact_ref=item.artifact_ref,
            details=json.loads(item.details_json) if item.details_json else {},
        ) for item in report.evidence],
    )


def _candidate_response(candidate: BuildCandidate, report: TestReport | None = None) -> CandidateResponse:
    return CandidateResponse(
        candidate_id=candidate.id,
        project_id=candidate.project_id,
        build_id=candidate.build_id,
        build_status=candidate.status,
        test_gate_status=candidate.test_gate_status,
        parent_candidate_id=candidate.parent_candidate_id,
        attempt=candidate.attempt,
        repair_round=candidate.repair_round,
        report=_report_response(report) if report else None,
    )


def _service(request: Request, session: Session) -> CandidateTestService:
    runner = getattr(request.app.state, "candidate_test_runner", None)
    if runner is None:
        runner = FakeCandidateTestRunner("pass")
    return CandidateTestService(session, runner)


@router.post("/{candidate_id}/test", response_model=CandidateResponse)
async def test_candidate(candidate_id: str, request: Request) -> CandidateResponse:
    with _session(request) as session:
        _candidate(session, candidate_id)
        try:
            report = await _service(request, session).test_candidate(candidate_id)
            session.commit()
            candidate = _candidate(session, candidate_id)
            return _candidate_response(candidate, report)
        except ValueError as cause:
            session.rollback()
            raise ApiError("candidate_test_failed", str(cause), [], 409) from cause


@router.get("/{candidate_id}/test-report", response_model=CandidateResponse)
def get_test_report(candidate_id: str, request: Request) -> CandidateResponse:
    with _session(request) as session:
        candidate = _candidate(session, candidate_id)
        report = session.scalar(select(TestReport).where(TestReport.candidate_id == candidate.id))
        if report is None:
            raise ApiError("test_report_not_found", "Test report not found", [], 404)
        return _candidate_response(candidate, report)


@router.post("/{candidate_id}/repair-link", response_model=CandidateResponse, status_code=status.HTTP_200_OK)
def link_repair_candidate(candidate_id: str, payload: RepairLinkRequest, request: Request) -> CandidateResponse:
    with _session(request) as session:
        _candidate(session, candidate_id)
        try:
            replacement = _service(request, session).link_repair_candidate(candidate_id, payload.replacement_candidate_id)
            session.commit()
            return _candidate_response(replacement)
        except ValueError as cause:
            session.rollback()
            raise ApiError("candidate_repair_failed", str(cause), [], 409) from cause
