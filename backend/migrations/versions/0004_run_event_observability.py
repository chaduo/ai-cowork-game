"""Persist runs and ordered normalized events."""

from alembic import op
import sqlalchemy as sa


revision = "0004_run_event_observability"
down_revision = "0003_project_creation_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("id", sa.String(120), primary_key=True),
        sa.Column("build_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("last_sequence", sa.Integer(), nullable=False),
        sa.Column("cancel_requested_at", sa.DateTime(timezone=True)),
        sa.Column("failure_code", sa.String(120)),
        sa.Column("failure_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "run_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(120), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(80), nullable=False),
        sa.Column("kind", sa.String(80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("progress", sa.Float()),
        sa.Column("artifact_ref", sa.Text()),
        sa.Column("error_json", sa.Text()),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_id", "sequence", name="uq_run_event_sequence"),
    )
    op.create_index("ix_run_events_run_sequence", "run_events", ["run_id", "sequence"])


def downgrade() -> None:
    op.drop_index("ix_run_events_run_sequence", table_name="run_events")
    op.drop_table("run_events")
    op.drop_table("runs")
