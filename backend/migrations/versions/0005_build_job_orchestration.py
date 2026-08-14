"""Persist build inputs and result diagnostics for C11 orchestration."""

from alembic import op
import sqlalchemy as sa


revision = "0005_build_job_orchestration"
down_revision = "0004_run_event_observability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("builds", sa.Column("operation", sa.String(80), nullable=False, server_default="create"))
    op.add_column("builds", sa.Column("request_text", sa.Text(), nullable=False, server_default=""))
    op.add_column("builds", sa.Column("baseline_playable_version_id", sa.String(36), nullable=True))
    op.add_column("build_candidates", sa.Column("diagnostics_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("build_candidates", "diagnostics_json")
    op.drop_column("builds", "baseline_playable_version_id")
    op.drop_column("builds", "request_text")
    op.drop_column("builds", "operation")
