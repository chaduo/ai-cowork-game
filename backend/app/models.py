from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class GameSpecRevision(Base):
    __tablename__ = "game_spec_revisions"
    __table_args__ = (UniqueConstraint("project_id", "revision_number", name="uq_gamespec_revision_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    build_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    last_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


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
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BuildCandidate(Base):
    __tablename__ = "build_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    build_id: Mapped[str] = mapped_column(ForeignKey("builds.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    diagnostics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


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
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
