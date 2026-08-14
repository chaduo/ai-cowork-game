from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.contracts.gamespec import CreatorGameSpec, RuntimeBuildSpec


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


GameBuildStatus = Literal[
    "succeeded",
    "failed",
    "cancelled",
    "timed_out",
    "invalid_output",
    "unsupported",
]


class WorkspaceRef(ContractModel):
    root: str = Field(min_length=1, max_length=4096)
    allowed_paths: list[str] = Field(default_factory=list, max_length=256)


class ArtifactManifestEntry(ContractModel):
    path: str = Field(min_length=1, max_length=4096)
    kind: str = Field(min_length=1, max_length=80)
    size_bytes: int = Field(default=0, ge=0)
    sha256: str | None = Field(default=None, min_length=64, max_length=64)


class Diagnostic(ContractModel):
    level: Literal["info", "warning", "error"]
    message: str = Field(min_length=1, max_length=4000)
    code: str | None = Field(default=None, min_length=1, max_length=120)


class ContractError(ContractModel):
    code: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=4000)
    details: list[str] = Field(default_factory=list, max_length=32)


class AgentRunHandle(ContractModel):
    run_id: str = Field(min_length=1, max_length=120)
    build_id: str = Field(min_length=1, max_length=120)


class GameBuildRequest(ContractModel):
    project_id: str = Field(min_length=1, max_length=120)
    build_id: str = Field(min_length=1, max_length=120)
    operation: str = Field(min_length=1, max_length=80)
    creator_game_spec: CreatorGameSpec
    runtime_build_spec: RuntimeBuildSpec
    workspace: WorkspaceRef
    baseline_playable: str | None = Field(default=None, max_length=120)
    request_text: str = Field(default="", max_length=4000)


class GameBuildResult(ContractModel):
    status: GameBuildStatus
    artifact_manifest: list[ArtifactManifestEntry] = Field(default_factory=list, max_length=512)
    preview_entry: str | None = Field(default=None, max_length=4096)
    diagnostics: list[Diagnostic] = Field(default_factory=list, max_length=256)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: ContractError | None = None

    @model_validator(mode="after")
    def validate_error_contract(self) -> "GameBuildResult":
        if self.status == "succeeded" and self.error is not None:
            raise ValueError("succeeded result cannot contain an error")
        if self.status != "succeeded" and self.error is None:
            raise ValueError(f"{self.status} result requires a structured error")
        return self


_FORBIDDEN_GATE_TOKENS = ("promot", "publish", "resource_saved", "resources_saved")


class RunEvent(ContractModel):
    run_id: str = Field(min_length=1, max_length=120)
    sequence: int = Field(ge=1)
    stage: str = Field(min_length=1, max_length=80)
    kind: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=4000)
    progress: float | None = Field(default=None, ge=0, le=1)
    artifact_ref: str | None = Field(default=None, max_length=4096)
    error: ContractError | None = None
    timestamp: datetime

    @field_validator("kind")
    @classmethod
    def reject_human_gate_events(cls, value: str) -> str:
        normalized = value.lower().replace("-", "_")
        if any(token in normalized for token in _FORBIDDEN_GATE_TOKENS):
            raise ValueError("provider events cannot express Human Gate decisions")
        return value
