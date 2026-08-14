"""Persist provider input decisions and decision-aware run events."""

from alembic import op
import sqlalchemy as sa


revision = "0008_c07_run_input_conformance"
down_revision = "0007_c05_design_revisions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("run_events", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("decision_id", sa.String(120), nullable=True))

    op.create_table(
        "run_pending_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(120), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("decision_id", sa.String(120), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("input_type", sa.String(20), nullable=False),
        sa.Column("options_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("response_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("run_id", "decision_id", name="uq_run_pending_decision"),
    )
    op.create_index(
        "ix_run_pending_decisions_run_status",
        "run_pending_decisions",
        ["run_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_run_pending_decisions_run_status", table_name="run_pending_decisions")
    op.drop_table("run_pending_decisions")
    with op.batch_alter_table("run_events", recreate="always") as batch_op:
        batch_op.drop_column("decision_id")
