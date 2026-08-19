"""Persist the verified Candidate artifact manifest for safe Promote snapshots."""

from alembic import op
import sqlalchemy as sa


revision = "0016_candidate_artifact_manifest"
down_revision = "0015_c16_release_publishing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("build_candidates", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("artifact_manifest_json", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("build_candidates", recreate="always") as batch_op:
        batch_op.drop_column("artifact_manifest_json")
