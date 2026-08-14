from app.agents.candidate_test_runner import CandidateTestRunner
from app.contracts.game_agent import Diagnostic
from app.contracts.test_report import CandidateTestEvidence, RuntimeTestResult
from app.models import BuildCandidate


REQUIRED_EVIDENCE = ("browser_started", "console", "core_input", "gameplay", "completion")


class FakeCandidateTestRunner(CandidateTestRunner):
    """Deterministic C12 bridge used until a real browser adapter is available."""

    def __init__(self, fixture: str = "pass") -> None:
        self.fixture = fixture

    async def run(self, candidate: BuildCandidate) -> RuntimeTestResult:
        evidence = [
            CandidateTestEvidence(
                kind=kind,
                status="passed",
                expected=f"{kind} passes",
                observed=f"{kind} observed",
                artifact_ref=candidate.artifact_path or "dist/index.html",
            )
            for kind in REQUIRED_EVIDENCE
        ]
        if self.fixture == "missing_evidence":
            evidence = [item for item in evidence if item.kind != "completion"]
            return RuntimeTestResult(verdict="pass", evidence=evidence)
        if self.fixture == "runtime_only_pass":
            return RuntimeTestResult(verdict="pass", evidence=[])
        if self.fixture == "contradictory":
            return RuntimeTestResult(verdict="fail", evidence=evidence)
        if self.fixture == "console_failure":
            evidence[1] = evidence[1].model_copy(update={"status": "failed", "observed": "console error observed"})
            return RuntimeTestResult(
                verdict="fail",
                evidence=evidence,
                diagnostics=[Diagnostic(level="error", code="console_error", message="Console reported an error")],
            )
        if self.fixture == "completion_failure":
            evidence[-1] = evidence[-1].model_copy(update={"status": "failed", "observed": "completion not observed"})
            return RuntimeTestResult(
                verdict="fail",
                evidence=evidence,
                diagnostics=[Diagnostic(level="error", code="completion_failed", message="Completion condition was not observed")],
            )
        if self.fixture != "pass":
            raise ValueError(f"unknown fake test fixture: {self.fixture}")
        return RuntimeTestResult(verdict="pass", evidence=evidence)
