from typing import Protocol

from app.contracts.test_report import RuntimeTestResult
from app.models import BuildCandidate


REQUIRED_EVIDENCE = (
    "browser_started",
    "console",
    "core_input",
    "gameplay",
    "completion",
    "phaser_hook",
)

EVIDENCE_GROUPS = {
    "browser_started": "browser_smoke",
    "console": "browser_smoke",
    "core_input": "core_gameplay",
    "gameplay": "core_gameplay",
    "completion": "core_gameplay",
    "phaser_hook": "core_gameplay",
}

PHASER_TEST_HOOK = "window.__GAME_TEST__"


class CandidateTestRunner(Protocol):
    async def run(self, candidate: BuildCandidate) -> RuntimeTestResult:
        """Return runtime claims and raw evidence; never assign a platform verdict."""
