from typing import Protocol

from app.contracts.test_report import RuntimeTestResult
from app.models import BuildCandidate


class CandidateTestRunner(Protocol):
    async def run(self, candidate: BuildCandidate) -> RuntimeTestResult:
        """Return runtime claims and raw evidence; never assign a platform verdict."""
