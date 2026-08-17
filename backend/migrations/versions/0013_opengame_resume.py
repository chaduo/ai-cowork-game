"""Persist the OpenGame session id so a waiting run can be resumed (line-115).

A `waiting_for_input` run pauses the OpenGame provider session. When the blocking
decision is resolved, the platform resumes that session via `opengame --resume
<session_id>`. The session id is captured from the run's first `system` event
(its `session_id` field) and persisted on the `Run` so the resume can find it
across the resolve boundary (and across a refresh/restart).

Nullable: pre-line-115 runs and Fake/test runs have no OpenGame session and stay
valid; a waiting run that has no session id cannot be resumed (the continuation
path surfaces that as a `session_not_resumable` failure rather than silently
sticking).
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_opengame_resume"
down_revision = "0011_c13_workspace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("runs", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("opengame_session_id", sa.String(120), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("runs", recreate="always") as batch_op:
        batch_op.drop_column("opengame_session_id")
