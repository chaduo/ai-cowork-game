"""Align C12 verification verdict, evidence provenance and repair limits."""

from alembic import op
import sqlalchemy as sa


revision = "0010_c12_verification_conformance"
down_revision = "0009_c11_build_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("build_candidates", sa.Column("repair_round", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("test_reports", sa.Column("severity", sa.String(20), nullable=False, server_default="none"))
    op.add_column("test_evidence", sa.Column("source", sa.String(20), nullable=False, server_default="runtime"))
    op.add_column("test_evidence", sa.Column("severity", sa.String(20), nullable=False, server_default="critical"))

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE test_reports
            SET platform_verdict = CASE platform_verdict
                WHEN 'pass' THEN 'PASSED'
                WHEN 'fail' THEN 'CRITICAL_FAILURE'
                WHEN 'invalid' THEN 'INVALID'
                ELSE platform_verdict
            END,
            status = CASE status
                WHEN 'pass' THEN 'PASSED'
                WHEN 'fail' THEN 'CRITICAL_FAILURE'
                WHEN 'invalid' THEN 'INVALID'
                ELSE status
            END,
            severity = CASE platform_verdict
                WHEN 'pass' THEN 'critical'
                WHEN 'fail' THEN 'critical'
                ELSE 'critical'
            END
            """
        )
    )


def downgrade() -> None:
    op.drop_column("test_evidence", "severity")
    op.drop_column("test_evidence", "source")
    op.drop_column("test_reports", "severity")
    op.drop_column("build_candidates", "repair_round")
