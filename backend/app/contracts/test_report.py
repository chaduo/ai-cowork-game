from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.game_agent import Diagnostic


class TestReportModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


EvidenceStatus = Literal["passed", "failed", "missing"]
RuntimeVerdict = Literal["pass", "fail", "unknown"]
PlatformVerdict = Literal["pass", "fail", "invalid"]


class CandidateTestEvidence(TestReportModel):
    kind: str = Field(min_length=1, max_length=80)
    status: EvidenceStatus
    expected: str = Field(min_length=1, max_length=4000)
    observed: str = Field(min_length=1, max_length=4000)
    artifact_ref: str = Field(min_length=1, max_length=4096)
    details: dict[str, Any] = Field(default_factory=dict)


class RuntimeTestResult(TestReportModel):
    verdict: RuntimeVerdict
    evidence: list[CandidateTestEvidence] = Field(default_factory=list, max_length=128)
    diagnostics: list[Diagnostic] = Field(default_factory=list, max_length=128)
