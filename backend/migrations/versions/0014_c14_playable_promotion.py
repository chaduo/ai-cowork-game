"""Persist C14 Human Play Review and restore provenance."""

from alembic import op
import sqlalchemy as sa


revision = "0014_c14_playable_promotion"
down_revision = "0013_opengame_resume"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("build_candidates", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("source_playable_version_id", sa.String(36), nullable=True))
        batch_op.create_foreign_key(
            "fk_build_candidates_source_playable_version",
            "playable_versions",
            ["source_playable_version_id"],
            ["id"],
        )

    op.create_table(
        "human_play_reviews",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("candidate_id", sa.String(36), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("amendment_status", sa.String(20), nullable=False, server_default="not_required"),
        sa.Column("drift_status", sa.String(20), nullable=False, server_default="clear"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["build_candidates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", name="uq_human_play_review_candidate"),
    )


def downgrade() -> None:
    op.drop_table("human_play_reviews")
    with op.batch_alter_table("build_candidates", recreate="always") as batch_op:
        batch_op.drop_column("source_playable_version_id")
