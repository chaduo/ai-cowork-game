from datetime import datetime, timezone
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
    "waiting_for_input",
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


class ContractProfile(ContractModel):
    name: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=40)
    capabilities: list[str] = Field(default_factory=list, max_length=128)


class AffectedScope(ContractModel):
    sections: list[str] = Field(default_factory=list, max_length=128)
    description: str = Field(default="", max_length=4000)


class ResourceReference(ContractModel):
    resource_id: str = Field(min_length=1, max_length=120)
    resource_revision: str = Field(min_length=1, max_length=120)
    source_project_id: str = Field(min_length=1, max_length=120)
    source_release_id: str | None = Field(default=None, max_length=120)
    snapshot_hash: str | None = Field(default=None, min_length=64, max_length=64)
    role: str = Field(min_length=1, max_length=120)


class BuildOverride(ContractModel):
    key: str = Field(min_length=1, max_length=160)
    value: Any
    source: Literal["user", "resource", "system"] = "user"
    provenance: str = Field(min_length=1, max_length=240)


class PendingDecision(ContractModel):
    decision_id: str = Field(min_length=1, max_length=120)
    prompt: str = Field(min_length=1, max_length=4000)
    input_type: Literal["choice", "text", "boolean"] = "choice"
    options: list[str] = Field(default_factory=list, max_length=64)


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
    affected_scope: AffectedScope = Field(default_factory=AffectedScope)
    resource_references: list[ResourceReference] = Field(default_factory=list, max_length=128)
    implementation_dependencies: list[str] = Field(default_factory=list, max_length=128)
    relevant_overrides: list[BuildOverride] = Field(default_factory=list, max_length=128)
    game_design_profile: ContractProfile = Field(
        default_factory=lambda: ContractProfile(name="creator-game-design", version="1", capabilities=[]),
    )
    gamespec_profile: ContractProfile = Field(
        default_factory=lambda: ContractProfile(name="creator-gamespec", version="1", capabilities=[]),
    )
    game_build_profile: ContractProfile = Field(
        default_factory=lambda: ContractProfile(name="runtime-build", version="1", capabilities=[]),
    )


class GameBuildResult(ContractModel):
    status: GameBuildStatus
    artifact_manifest: list[ArtifactManifestEntry] = Field(default_factory=list, max_length=512)
    preview_entry: str | None = Field(default=None, max_length=4096)
    diagnostics: list[Diagnostic] = Field(default_factory=list, max_length=256)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: ContractError | None = None
    pending_decision: PendingDecision | None = None

    @model_validator(mode="after")
    def validate_error_contract(self) -> "GameBuildResult":
        if self.status == "waiting_for_input":
            if self.pending_decision is None or self.error is not None:
                raise ValueError("waiting_for_input result requires a pending decision and no error")
            return self
        if self.pending_decision is not None:
            raise ValueError("terminal result cannot contain a pending decision")
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
    decision_id: str | None = Field(default=None, max_length=120)

    @field_validator("kind")
    @classmethod
    def reject_human_gate_events(cls, value: str) -> str:
        normalized = value.lower().replace("-", "_")
        if any(token in normalized for token in (*_FORBIDDEN_GATE_TOKENS, "resource_save", "save_resource", "saved_resource")):
            raise ValueError("provider events cannot express Human Gate decisions")
        return value

    @field_validator("timestamp")
    @classmethod
    def require_utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("RunEvent timestamp must include a timezone")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_decision_event(self) -> "RunEvent":
        normalized = self.kind.lower().replace("-", "_")
        if normalized in {"build.needs_input", "build_needs_input", "needs_input", "waiting_for_input"} and not self.decision_id:
            raise ValueError("input events require a stable decision_id")
        if normalized in {"build.continued", "build_continued", "continued"} and not self.decision_id:
            raise ValueError("continuation events require a stable decision_id")
        return self
