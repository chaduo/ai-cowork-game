"""Persist the C16 immutable Release snapshot and extraction batch boundary."""

from alembic import op
import sqlalchemy as sa


revision = "0015_c16_release_publishing"
down_revision = "0014_c14_playable_promotion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("releases", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("game_design_revision_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("gamespec_revision_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("artifact_path", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("artifact_checksum", sa.String(length=128), nullable=True))
        batch_op.create_foreign_key(
            "fk_releases_game_design_revision",
            "game_design_revisions",
            ["game_design_revision_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_releases_gamespec_revision",
            "game_spec_revisions",
            ["gamespec_revision_id"],
            ["id"],
        )

    op.create_table(
        "resource_extraction_batches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("release_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="empty"),
        sa.Column("candidate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("release_id", name="uq_resource_extraction_batch_release"),
    )


def downgrade() -> None:
    op.drop_table("resource_extraction_batches")
    with op.batch_alter_table("releases", recreate="always") as batch_op:
        batch_op.drop_column("artifact_checksum")
        batch_op.drop_column("artifact_path")
        batch_op.drop_column("gamespec_revision_id")
        batch_op.drop_column("game_design_revision_id")
        batch_op.drop_column("description")
        batch_op.drop_column("name")
