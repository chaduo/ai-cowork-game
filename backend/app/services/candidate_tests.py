from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import PurePosixPath

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.candidate_test_runner import CandidateTestRunner
from app.agents.candidate_test_runner import PHASER_TEST_HOOK, REQUIRED_EVIDENCE
from app.contracts.test_report import CandidateTestEvidence, RuntimeTestResult
from app.models import BuildCandidate, TestEvidence, TestReport, utc_now


MAX_REPAIR_ROUNDS = 3
BUILD_CHECK = "build_check"
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

        if candidate.status != "succeeded" or not self._safe_artifact_path(candidate.artifact_path):
            return self._persist_report(
                candidate,
                runtime_verdict="unknown",
                platform_verdict="INVALID",
                severity="critical",
                summary="Candidate build did not produce a testable artifact",
                diagnostics=[{"code": "artifact_not_testable", "message": "Candidate must have a successful build and artifact"}],
                evidence=[],
            )

        result = await self.runner.run(candidate)
        evidence = [self._build_check(candidate), *result.evidence]
        platform_verdict, severity, summary = self._platform_verdict(candidate, result, evidence)
        return self._persist_report(
            candidate,
            runtime_verdict=result.verdict,
            platform_verdict=platform_verdict,
            severity=severity,
            summary=summary,
            diagnostics=[item.model_dump(mode="json") for item in result.diagnostics],
            evidence=evidence,
        )

    def link_repair_candidate(self, parent_candidate_id: str, replacement_candidate_id: str) -> BuildCandidate:
        parent = self.session.get(BuildCandidate, parent_candidate_id)
        replacement = self.session.get(BuildCandidate, replacement_candidate_id)
        if parent is None or replacement is None:
            raise ValueError("candidate not found")
        parent_report = self.session.scalar(select(TestReport).where(TestReport.candidate_id == parent.id))
        if parent_report is None or parent_report.status not in {"PARTIAL_FAILURE", "CRITICAL_FAILURE", "INVALID", "fail", "invalid"}:
            raise ValueError("parent candidate must have a failed or invalid test report")
        if parent.project_id != replacement.project_id:
            raise ValueError("repair candidates must belong to the same project")
        if replacement.test_gate_status != "untested" or replacement.parent_candidate_id:
            raise ValueError("replacement candidate is already linked or tested")
        if replacement.repair_round != 0:
            raise ValueError("replacement candidate already belongs to a repair chain")
        if parent.repair_round >= MAX_REPAIR_ROUNDS:
            raise ValueError("maximum repair rounds reached")
        replacement.parent_candidate_id = parent.id
        replacement.attempt = parent.attempt + 1
        replacement.repair_round = parent.repair_round + 1
        self.session.flush()
        return replacement

    @staticmethod
    def _platform_verdict(
        candidate: BuildCandidate,
        result: RuntimeTestResult,
        evidence: list[CandidateTestEvidence],
    ) -> tuple[str, str, str]:
        kinds = Counter(item.kind for item in result.evidence)
        if any(count != 1 for count in kinds.values()) or set(kinds) != set(REQUIRED_EVIDENCE):
            return "INVALID", "critical", "Required browser and gameplay evidence is missing or duplicated"
        if any(
            not item.artifact_ref
            or not item.expected.strip()
            or not item.observed.strip()
            or item.source != "platform"
            or not CandidateTestService._safe_artifact_ref(candidate.artifact_path, item.artifact_ref)
            for item in evidence
        ):
            return "INVALID", "critical", "Evidence is not platform-owned or references an invalid artifact"

        build_check = next((item for item in evidence if item.kind == BUILD_CHECK), None)
        if build_check is None or build_check.status != "passed":
            return "CRITICAL_FAILURE", "critical", "Build Check did not pass"

        hook = next((item for item in evidence if item.kind == "phaser_hook"), None)
        hook_details = hook.details if hook else {}
        if hook is None or hook.status != "passed" or hook_details.get("test_hook") != PHASER_TEST_HOOK or hook_details.get("hook_validated") is not True:
            return "CRITICAL_FAILURE", "critical", "The Phaser test hook was not validated"

        failed = [item for item in evidence if item.status == "failed"]
        missing = [item for item in evidence if item.status == "missing"]
        if result.verdict == "pass" and (failed or missing):
            return "INVALID", "critical", "Runtime PASS contradicts failed or missing platform evidence"
        if result.verdict == "fail" and not failed:
            return "INVALID", "critical", "Runtime failure contradicts passing platform evidence"
        if missing:
            return "CRITICAL_FAILURE", "critical", "A required platform check is missing"
        if failed:
            if any(item.severity == "critical" for item in failed):
                return "CRITICAL_FAILURE", "critical", "A critical platform check failed"
            return "PARTIAL_FAILURE", "partial", "A supporting platform check failed"
        if result.verdict != "pass" or any(item.status != "passed" for item in evidence):
            return "INVALID", "critical", "Platform evidence did not establish a complete passing result"
        return "PASSED", "none", "Build, Browser Smoke and Core Gameplay Acceptance passed"

    @staticmethod
    def _safe_artifact_path(path: str | None) -> bool:
        if not path:
            return False
        normalized = PurePosixPath(path)
        return (
            not path.startswith(("/", "~"))
            and "://" not in path
            and ".." not in normalized.parts
            and normalized.suffix.lower() == ".html"
        )

    @staticmethod
    def _safe_artifact_ref(candidate_path: str | None, artifact_ref: str) -> bool:
        if not candidate_path or not CandidateTestService._safe_artifact_path(candidate_path):
            return False
        if artifact_ref.startswith(("/", "~")) or "://" in artifact_ref or "\x00" in artifact_ref:
            return False
        normalized = PurePosixPath(artifact_ref)
        if ".." in normalized.parts:
            return False
        root = PurePosixPath(candidate_path).parent
        return normalized == PurePosixPath(candidate_path) or str(normalized).startswith(f"{root}/")

    @staticmethod
    def _build_check(candidate: BuildCandidate) -> CandidateTestEvidence:
        return CandidateTestEvidence(
            kind=BUILD_CHECK,
            status="passed",
            source="platform",
            severity="critical",
            expected="Build succeeded and produced an HTML entry artifact",
            observed=f"Build candidate artifact: {candidate.artifact_path}",
            artifact_ref=candidate.artifact_path or "",
            details={"check_group": "build_check"},
        )

    def _persist_report(
        self,
        candidate: BuildCandidate,
        *,
        runtime_verdict: str,
        platform_verdict: str,
        severity: str,
        summary: str,
        diagnostics: list[dict],
        evidence: list[CandidateTestEvidence],
    ) -> TestReport:
        report = TestReport(
            candidate_id=candidate.id,
            runtime_verdict=runtime_verdict,
            platform_verdict=platform_verdict,
            status=platform_verdict,
            severity=severity,
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
                source=item.source,
                severity=item.severity,
                expected=item.expected,
                observed=item.observed,
                artifact_ref=item.artifact_ref,
                details_json=json.dumps(item.details, ensure_ascii=False) if item.details else None,
                created_at=datetime.now(timezone.utc),
            ))
        candidate.test_gate_status = {
            "PASSED": "ready",
            "PARTIAL_FAILURE": "failed",
            "CRITICAL_FAILURE": "failed",
            "INVALID": "invalid",
        }[platform_verdict]
        self.session.flush()
        return report
