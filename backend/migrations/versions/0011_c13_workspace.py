"""Persist C13 run workspace path + lifecycle status.

A run now records the absolute prepared workspace path and a coarse lifecycle
status so that:
- startup orphan recovery knows which runs left a partial workspace on disk to
  discard (status ``prepared`` but run is terminal-orphaned);
- retry can prove it did NOT reuse a prior partial workspace (each run persists
  its own path; a ``discarded`` workspace is never imported from).

Both columns are nullable: pre-C13 runs and Fake/test runs that never touch disk
leave them NULL. ``workspace_status`` is one of ``prepared`` / ``discarded`` /
``imported``.
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_c13_workspace"
down_revision = "0010_c12_verification_conformance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("runs", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("workspace_path", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("workspace_status", sa.String(20), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("runs", recreate="always") as batch_op:
        batch_op.drop_column("workspace_status")
        batch_op.drop_column("workspace_path")
