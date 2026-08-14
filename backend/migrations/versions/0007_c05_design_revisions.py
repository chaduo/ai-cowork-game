"""Persist immutable C05 design revisions and GameSpec provenance."""

import json
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "0007_c05_design_revisions"
down_revision = "0006_candidate_test_gate"
branch_labels = None
depends_on = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def upgrade() -> None:
    op.add_column("game_designs", sa.Column("current_revision_id", sa.String(36), nullable=True))
    op.add_column("game_designs", sa.Column("confirmed_revision_id", sa.String(36), nullable=True))
    op.create_table(
        "game_design_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column("readiness_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "revision_number", name="uq_game_design_revision_number"),
    )
    with op.batch_alter_table("game_spec_revisions", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("source_design_revision_id", sa.String(36), nullable=True))
        batch_op.create_foreign_key(
            "fk_game_spec_revisions_source_design_revision",
            "game_design_revisions",
            ["source_design_revision_id"],
            ["id"],
        )

    bind = op.get_bind()
    designs = sa.table(
        "game_designs",
        sa.column("id", sa.String(36)),
        sa.column("project_id", sa.String(36)),
        sa.column("content_json", sa.Text()),
        sa.column("status", sa.String(20)),
        sa.column("current_revision_id", sa.String(36)),
        sa.column("confirmed_revision_id", sa.String(36)),
        sa.column("confirmed_at", sa.DateTime(timezone=True)),
    )
    revisions = sa.table(
        "game_design_revisions",
        sa.column("id", sa.String(36)),
        sa.column("project_id", sa.String(36)),
        sa.column("revision_number", sa.Integer()),
        sa.column("content_json", sa.Text()),
        sa.column("readiness_json", sa.Text()),
        sa.column("status", sa.String(20)),
        sa.column("confirmed_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    for row in bind.execute(sa.select(designs)).mappings():
        revision_id = str(uuid4())
        confirmed = row["status"] == "confirmed"
        readiness = {
            "status": "ready" if confirmed else "not_ready",
            "blockers": [] if confirmed else ["readiness_not_recorded"],
            "unresolved_decisions": [],
            "checked_at": row["confirmed_at"].isoformat() if confirmed and row["confirmed_at"] else None,
        }
        bind.execute(
            revisions.insert().values(
                id=revision_id,
                project_id=row["project_id"],
                revision_number=1,
                content_json=row["content_json"],
                readiness_json=json.dumps(readiness, ensure_ascii=False),
                status="confirmed" if confirmed else "draft",
                confirmed_at=row["confirmed_at"] if confirmed else None,
                created_at=row["confirmed_at"] or _now(),
            )
        )
        bind.execute(
            designs.update().where(designs.c.id == row["id"]).values(
                current_revision_id=revision_id,
                confirmed_revision_id=revision_id if confirmed else None,
            )
        )


def downgrade() -> None:
    op.drop_table("game_design_revisions")
    with op.batch_alter_table("game_spec_revisions", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_game_spec_revisions_source_design_revision", type_="foreignkey")
        batch_op.drop_column("source_design_revision_id")
    op.drop_column("game_designs", "confirmed_revision_id")
    op.drop_column("game_designs", "current_revision_id")
