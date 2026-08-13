"""Add idempotency key for C03 project creation."""

from alembic import op
import sqlalchemy as sa

revision = "0003_project_creation_idempotency"
down_revision = "0002_project_lifecycle_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("idempotency_key", sa.String(128), nullable=True))
    op.create_index("uq_project_idempotency_key", "projects", ["idempotency_key"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_project_idempotency_key", table_name="projects")
    op.drop_column("projects", "idempotency_key")
