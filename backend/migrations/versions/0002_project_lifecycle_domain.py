"""Create C02 project lifecycle tables."""

from alembic import op
import sqlalchemy as sa

revision = "0002_project_lifecycle_domain"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("original_idea", sa.Text(), nullable=False),
        sa.Column("current_playable_version_id", sa.String(36)),
        sa.Column("active_build_id", sa.String(36)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "game_designs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", name="uq_game_design_project"),
    )
    op.create_table(
        "game_spec_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "revision_number", name="uq_gamespec_revision_number"),
    )
    op.create_table(
        "builds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("gamespec_revision_id", sa.String(36), sa.ForeignKey("game_spec_revisions.id"), nullable=False),
        sa.Column("parent_build_id", sa.String(36), sa.ForeignKey("builds.id")),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("failure_code", sa.String(80)),
        sa.Column("failure_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("uq_active_build_project", "builds", ["project_id"], unique=True, sqlite_where=sa.text("status IN ('pending','running','cancelling')"))
    op.create_table(
        "build_candidates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("build_id", sa.String(36), sa.ForeignKey("builds.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("artifact_path", sa.Text()),
        sa.Column("artifact_checksum", sa.String(128)),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("build_id", name="uq_candidate_build"),
    )
    op.create_table(
        "playable_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("candidate_id", sa.String(36), sa.ForeignKey("build_candidates.id"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("parent_version_id", sa.String(36), sa.ForeignKey("playable_versions.id")),
        sa.Column("test_report_id", sa.String(36), nullable=False),
        sa.Column("git_commit", sa.String(128), nullable=False),
        sa.Column("artifact_path", sa.Text(), nullable=False),
        sa.Column("artifact_checksum", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "number", name="uq_playable_version_number"),
        sa.UniqueConstraint("candidate_id", name="uq_version_candidate"),
    )
    op.create_table(
        "releases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("playable_version_id", sa.String(36), sa.ForeignKey("playable_versions.id"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "number", name="uq_release_number"),
    )


def downgrade() -> None:
    op.drop_table("releases")
    op.drop_table("playable_versions")
    op.drop_table("build_candidates")
    op.drop_index("uq_active_build_project", table_name="builds")
    op.drop_table("builds")
    op.drop_table("game_spec_revisions")
    op.drop_table("game_designs")
    op.drop_table("projects")
