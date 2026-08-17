from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    original_idea: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    current_playable_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    active_build_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class GameDesign(Base):
    __tablename__ = "game_designs"
    __table_args__ = (UniqueConstraint("project_id", name="uq_game_design_project"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    current_revision_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    confirmed_revision_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class GameDesignRevision(Base):
    __tablename__ = "game_design_revisions"
    __table_args__ = (UniqueConstraint("project_id", "revision_number", name="uq_game_design_revision_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    readiness_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # C20 line-114: immutable git checkpoint sha recorded by CheckpointService.confirm_gdd.
    git_commit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class GameSpecRevision(Base):
    __tablename__ = "game_spec_revisions"
    __table_args__ = (UniqueConstraint("project_id", "revision_number", name="uq_gamespec_revision_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    source_design_revision_id: Mapped[str | None] = mapped_column(
        ForeignKey("game_design_revisions.id"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # C20 line-114: immutable git checkpoint sha recorded by CheckpointService.confirm_gamespec.
    git_commit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class Build(Base):
    __tablename__ = "builds"
    __table_args__ = (
        Index(
            "uq_active_build_project",
            "project_id",
            unique=True,
            sqlite_where=text("status IN ('pending','running','cancelling')"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    gamespec_revision_id: Mapped[str] = mapped_column(ForeignKey("game_spec_revisions.id"), nullable=False)
    parent_build_id: Mapped[str | None] = mapped_column(ForeignKey("builds.id"), nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    operation: Mapped[str] = mapped_column(String(80), nullable=False, default="create")
    request_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    baseline_playable_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class BuildContext(Base):
    __tablename__ = "build_contexts"
    __table_args__ = (
        UniqueConstraint("build_id", name="uq_build_context_build"),
        Index("ix_build_contexts_project_created", "project_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    build_id: Mapped[str] = mapped_column(ForeignKey("builds.id"), nullable=False)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    gamespec_revision_id: Mapped[str] = mapped_column(ForeignKey("game_spec_revisions.id"), nullable=False)
    gamespec_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    gamespec_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    runtime_build_spec_json: Mapped[str] = mapped_column(Text, nullable=False)
    runtime_build_spec_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    baseline_playable_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    affected_scope_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    resource_references_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    implementation_dependencies_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    relevant_overrides_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    game_design_profile_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    gamespec_profile_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    game_build_profile_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    operation: Mapped[str] = mapped_column(String(80), nullable=False)
    request_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    context_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    build_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    last_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # C13: absolute prepared run workspace path + coarse lifecycle status
    # (prepared | discarded | imported). NULL for pre-C13 / Fake / test runs that
    # never touch disk. Lets orphan recovery discard partials and retry prove it
    # did not reuse a prior partial workspace.
    workspace_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    workspace_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # line-115: the OpenGame provider session id, captured from the run's first
    # `system` event. Lets ContinuationService resume the paused session
    # (`opengame --resume <id>`) when its blocking decision is resolved. NULL for
    # pre-line-115 / Fake / test runs; a waiting run with no session id cannot be
    # resumed and the continuation path surfaces that as a structured failure.
    opengame_session_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class RunPendingDecision(Base):
    __tablename__ = "run_pending_decisions"
    __table_args__ = (
        UniqueConstraint("run_id", "decision_id", name="uq_run_pending_decision"),
        Index("ix_run_pending_decisions_run_status", "run_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    decision_id: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    input_type: Mapped[str] = mapped_column(String(20), nullable=False)
    options_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RunEventRecord(Base):
    __tablename__ = "run_events"
    __table_args__ = (
        UniqueConstraint("run_id", "sequence", name="uq_run_event_sequence"),
        Index("ix_run_events_run_sequence", "run_id", "sequence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[str] = mapped_column(String(80), nullable=False)
    kind: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    progress: Mapped[float | None] = mapped_column(nullable=True)
    artifact_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BuildCandidate(Base):
    __tablename__ = "build_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    build_id: Mapped[str] = mapped_column(ForeignKey("builds.id"), nullable=False, unique=True)
    build_context_id: Mapped[str | None] = mapped_column(ForeignKey("build_contexts.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    test_gate_status: Mapped[str] = mapped_column(String(20), nullable=False, default="untested")
    parent_candidate_id: Mapped[str | None] = mapped_column(ForeignKey("build_candidates.id"), nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    repair_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    artifact_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    diagnostics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class TestReport(Base):
    __tablename__ = "test_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("build_candidates.id"), nullable=False, unique=True)
    runtime_verdict: Mapped[str] = mapped_column(String(20), nullable=False)
    platform_verdict: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    diagnostics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    evidence: Mapped[list["TestEvidence"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="TestEvidence.created_at",
    )


class TestEvidence(Base):
    __tablename__ = "test_evidence"
    __table_args__ = (Index("ix_test_evidence_report_created", "test_report_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    test_report_id: Mapped[str] = mapped_column(ForeignKey("test_reports.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="runtime")
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="critical")
    expected: Mapped[str] = mapped_column(Text, nullable=False)
    observed: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_ref: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    report: Mapped[TestReport] = relationship(back_populates="evidence")


class PlayableVersion(Base):
    __tablename__ = "playable_versions"
    __table_args__ = (UniqueConstraint("project_id", "number", name="uq_playable_version_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("build_candidates.id"), nullable=False, unique=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version_id: Mapped[str | None] = mapped_column(ForeignKey("playable_versions.id"), nullable=True)
    test_report_id: Mapped[str] = mapped_column(String(36), nullable=False)
    git_commit: Mapped[str] = mapped_column(String(128), nullable=False)
    artifact_path: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class Release(Base):
    __tablename__ = "releases"
    __table_args__ = (UniqueConstraint("project_id", "number", name="uq_release_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    playable_version_id: Mapped[str] = mapped_column(ForeignKey("playable_versions.id"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="published")
    # C20 line-114: publish-time git checkpoint snapshot (CheckpointService.publish) so a
    # Release resolves to an immutable commit, not only transitively via PlayableVersion.
    git_commit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
