from app.agents.candidate_test_runner import CandidateTestRunner, EVIDENCE_GROUPS, REQUIRED_EVIDENCE
from app.contracts.game_agent import Diagnostic
from app.contracts.test_report import CandidateTestEvidence, RuntimeTestResult
from app.models import BuildCandidate


_GROUPS = EVIDENCE_GROUPS


class FakeCandidateTestRunner(CandidateTestRunner):
    """Deterministic C12 bridge used until a real browser adapter is available."""

    def __init__(self, fixture: str = "pass") -> None:
        self.fixture = fixture

    async def run(self, candidate: BuildCandidate) -> RuntimeTestResult:
        evidence = [
            CandidateTestEvidence(
                kind=kind,
                status="passed",
                source="platform",
                severity="critical",
                expected=f"{kind} passes",
                observed=f"{kind} observed",
                artifact_ref=candidate.artifact_path or "dist/index.html",
                details={
                    "check_group": _GROUPS[kind],
                    **(
                        {"test_hook": "window.__GAME_TEST__", "hook_validated": True}
                        if kind == "phaser_hook"
                        else {}
                    ),
                },
            )
            for kind in REQUIRED_EVIDENCE
        ]
        if self.fixture == "missing_evidence":
            evidence = [item for item in evidence if item.kind not in {"completion", "phaser_hook"}]
            return RuntimeTestResult(verdict="pass", evidence=evidence)
        if self.fixture == "runtime_only_pass":
            return RuntimeTestResult(
                verdict="pass",
                evidence=[item.model_copy(update={"source": "runtime"}) for item in evidence],
            )
        if self.fixture == "contradictory":
            return RuntimeTestResult(verdict="fail", evidence=evidence)
        if self.fixture == "invalid_artifact":
            evidence[0] = evidence[0].model_copy(update={"artifact_ref": "../outside/index.html"})
            return RuntimeTestResult(verdict="pass", evidence=evidence)
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
        if self.fixture == "partial_failure":
            evidence[1] = evidence[1].model_copy(
                update={"status": "failed", "severity": "partial", "observed": "supporting browser signal missing"}
            )
            return RuntimeTestResult(verdict="fail", evidence=evidence)
        if self.fixture == "hook_failure":
            evidence[-1] = evidence[-1].model_copy(
                update={"status": "failed", "observed": "window.__GAME_TEST__ unavailable"}
            )
            return RuntimeTestResult(verdict="fail", evidence=evidence)
        if self.fixture != "pass":
            raise ValueError(f"unknown fake test fixture: {self.fixture}")
        return RuntimeTestResult(verdict="pass", evidence=evidence)
