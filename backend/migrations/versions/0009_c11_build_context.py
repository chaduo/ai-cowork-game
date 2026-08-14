"""Persist immutable provider-ready Build Context snapshots for C11."""

from alembic import op
import sqlalchemy as sa


revision = "0009_c11_build_context"
down_revision = "0008_c07_run_input_conformance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "build_contexts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("build_id", sa.String(36), sa.ForeignKey("builds.id"), nullable=False),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("gamespec_revision_id", sa.String(36), sa.ForeignKey("game_spec_revisions.id"), nullable=False),
        sa.Column("gamespec_snapshot_json", sa.Text(), nullable=False),
        sa.Column("gamespec_snapshot_hash", sa.String(64), nullable=False),
        sa.Column("runtime_build_spec_json", sa.Text(), nullable=False),
        sa.Column("runtime_build_spec_hash", sa.String(64), nullable=False),
        sa.Column("baseline_playable_version_id", sa.String(36), nullable=True),
        sa.Column("affected_scope_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("resource_references_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("implementation_dependencies_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("relevant_overrides_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("game_design_profile_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("gamespec_profile_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("game_build_profile_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("operation", sa.String(80), nullable=False),
        sa.Column("request_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("context_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("build_id", name="uq_build_context_build"),
    )
    op.create_index("ix_build_contexts_project_created", "build_contexts", ["project_id", "created_at"])

    with op.batch_alter_table("build_candidates", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("build_context_id", sa.String(36), nullable=True))
        batch_op.create_foreign_key(
            "fk_build_candidates_build_context",
            "build_contexts",
            ["build_context_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("build_candidates", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_build_candidates_build_context", type_="foreignkey")
        batch_op.drop_column("build_context_id")
    op.drop_index("ix_build_contexts_project_created", table_name="build_contexts")
    op.drop_table("build_contexts")
