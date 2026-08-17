"""Persist C20 checkpoint provenance on GDD/GameSpec/Release (line-114 wiring).

The C20 primitives slice (0011) added run workspace provenance; this slice wires
the primitives into the lifecycle gates so a confirmed GDD/GameSpec, a promoted
PlayableVersion's Release, and the publish carry a real immutable git commit.

Adds a nullable ``git_commit`` (String(128)) to:
- ``game_design_revisions`` — set when the GDD is confirmed (CheckpointService.confirm_gdd)
- ``game_spec_revisions``     — set when the GameSpec is confirmed (CheckpointService.confirm_gamespec)
- ``releases``               — set at publish time (CheckpointService.publish), a publish-time
  snapshot so a Release resolves to a commit without only transitive resolution.

Nullable so pre-C20 rows and tests that do not checkpoint stay valid
(backward compatible). ``playable_versions.git_commit`` already exists (C02).
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_c20_checkpoint"
down_revision = "0011_c13_workspace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("game_design_revisions", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("git_commit", sa.String(128), nullable=True))
    with op.batch_alter_table("game_spec_revisions", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("git_commit", sa.String(128), nullable=True))
    with op.batch_alter_table("releases", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("git_commit", sa.String(128), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("releases", recreate="always") as batch_op:
        batch_op.drop_column("git_commit")
    with op.batch_alter_table("game_spec_revisions", recreate="always") as batch_op:
        batch_op.drop_column("git_commit")
    with op.batch_alter_table("game_design_revisions", recreate="always") as batch_op:
        batch_op.drop_column("git_commit")
