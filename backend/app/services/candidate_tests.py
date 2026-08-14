from __future__ import annotations

import asyncio
import json
from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.candidate_test_runner import CandidateTestRunner
from app.agents.fake_candidate_test_runner import REQUIRED_EVIDENCE
from app.contracts.test_report import CandidateTestEvidence, RuntimeTestResult
from app.models import BuildCandidate, TestEvidence, TestReport, utc_now


class CandidateTestService:
    def __init__(self, session: Session, runner: CandidateTestRunner) -> None:
        self.session = session
        self.runner = runner

    async def test_candidate(self, candidate_id: str) -> TestReport:
        candidate = self.session.get(BuildCandidate, candidate_id)
        if candidate is None:
            raise ValueError("candidate not found")
        existing = self.session.scalar(select(TestReport).where(TestReport.candidate_id == candidate.id))
        if existing is not None:
            return existing

        if candidate.status != "succeeded" or not candidate.artifact_path:
            return self._persist_report(
                candidate,
                runtime_verdict="unknown",
                platform_verdict="invalid",
                summary="Candidate build did not produce a testable artifact",
                diagnostics=[{"code": "artifact_not_testable", "message": "Candidate must have a successful build and artifact"}],
                evidence=[],
            )

        result = await self.runner.run(candidate)
        platform_verdict, summary = self._platform_verdict(result)
        return self._persist_report(
            candidate,
            runtime_verdict=result.verdict,
            platform_verdict=platform_verdict,
            summary=summary,
            diagnostics=[item.model_dump(mode="json") for item in result.diagnostics],
            evidence=result.evidence,
        )

    def link_repair_candidate(self, parent_candidate_id: str, replacement_candidate_id: str) -> BuildCandidate:
        parent = self.session.get(BuildCandidate, parent_candidate_id)
        replacement = self.session.get(BuildCandidate, replacement_candidate_id)
        if parent is None or replacement is None:
            raise ValueError("candidate not found")
        parent_report = self.session.scalar(select(TestReport).where(TestReport.candidate_id == parent.id))
        if parent_report is None or parent_report.status not in {"fail", "invalid"}:
            raise ValueError("parent candidate must have a failed or invalid test report")
        if parent.project_id != replacement.project_id:
            raise ValueError("repair candidates must belong to the same project")
        if replacement.test_gate_status != "untested" or replacement.parent_candidate_id:
            raise ValueError("replacement candidate is already linked or tested")
        replacement.parent_candidate_id = parent.id
        replacement.attempt = parent.attempt + 1
        self.session.flush()
        return replacement

    @staticmethod
    def _platform_verdict(result: RuntimeTestResult) -> tuple[str, str]:
        kinds = Counter(item.kind for item in result.evidence)
        if any(count != 1 for count in kinds.values()) or set(kinds) != set(REQUIRED_EVIDENCE):
            return "invalid", "Required test evidence is missing or duplicated"
        if any(not item.artifact_ref or not item.expected or not item.observed for item in result.evidence):
            return "invalid", "Test evidence is incomplete"
        failed = any(item.status == "failed" for item in result.evidence)
        if result.verdict == "pass" and failed:
            return "invalid", "Runtime PASS contradicts failed evidence"
        if result.verdict == "fail" and not failed:
            return "invalid", "Runtime failure contradicts passing evidence"
        if failed:
            return "fail", "One or more core checks failed"
        if result.verdict != "pass" or any(item.status != "passed" for item in result.evidence):
            return "invalid", "Runtime did not establish a complete passing result"
        return "pass", "All required platform checks passed"

    def _persist_report(
        self,
        candidate: BuildCandidate,
        *,
        runtime_verdict: str,
        platform_verdict: str,
        summary: str,
        diagnostics: list[dict],
        evidence: list[CandidateTestEvidence],
    ) -> TestReport:
        report = TestReport(
            candidate_id=candidate.id,
            runtime_verdict=runtime_verdict,
            platform_verdict=platform_verdict,
            status=platform_verdict,
            summary=summary,
            diagnostics_json=json.dumps(diagnostics, ensure_ascii=False) if diagnostics else None,
            created_at=utc_now(),
        )
        self.session.add(report)
        self.session.flush()
        for item in evidence:
            self.session.add(TestEvidence(
                test_report_id=report.id,
                kind=item.kind,
                status=item.status,
                expected=item.expected,
                observed=item.observed,
                artifact_ref=item.artifact_ref,
                details_json=json.dumps(item.details, ensure_ascii=False) if item.details else None,
                created_at=datetime.now(timezone.utc),
            ))
        candidate.test_gate_status = {
            "pass": "ready",
            "fail": "failed",
            "invalid": "invalid",
        }[platform_verdict]
        self.session.flush()
        return report
