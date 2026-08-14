"""Persist candidate test reports, evidence and repair ancestry."""

from alembic import op
import sqlalchemy as sa


revision = "0006_candidate_test_gate"
down_revision = "0005_build_job_orchestration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("build_candidates", sa.Column("test_gate_status", sa.String(20), nullable=False, server_default="untested"))
    op.add_column("build_candidates", sa.Column("parent_candidate_id", sa.String(36), nullable=True))
    op.add_column("build_candidates", sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"))
    with op.batch_alter_table("build_candidates", recreate="always") as batch_op:
        batch_op.create_foreign_key(
            "fk_build_candidates_parent_candidate",
            "build_candidates",
            ["parent_candidate_id"],
            ["id"],
        )
    op.create_table(
        "test_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("candidate_id", sa.String(36), sa.ForeignKey("build_candidates.id"), nullable=False),
        sa.Column("runtime_verdict", sa.String(20), nullable=False),
        sa.Column("platform_verdict", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("diagnostics_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("candidate_id", name="uq_test_report_candidate"),
    )
    op.create_table(
        "test_evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("test_report_id", sa.String(36), sa.ForeignKey("test_reports.id"), nullable=False),
        sa.Column("kind", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("expected", sa.Text(), nullable=False),
        sa.Column("observed", sa.Text(), nullable=False),
        sa.Column("artifact_ref", sa.Text(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_test_evidence_report_created", "test_evidence", ["test_report_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_test_evidence_report_created", table_name="test_evidence")
    op.drop_table("test_evidence")
    op.drop_table("test_reports")
    with op.batch_alter_table("build_candidates", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_build_candidates_parent_candidate", type_="foreignkey")
    op.drop_column("build_candidates", "attempt")
    op.drop_column("build_candidates", "parent_candidate_id")
    op.drop_column("build_candidates", "test_gate_status")
