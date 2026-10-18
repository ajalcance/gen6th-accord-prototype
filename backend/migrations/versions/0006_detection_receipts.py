"""Durable internal persona detection evaluations, independent of runtime metadata."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006detection"
down_revision: str | Sequence[str] | None = "0005campaigns"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "detection_receipts",
        sa.Column("event_id", sa.String(32), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rules_digest", sa.String(64), nullable=False),
        sa.Column("window_within_retention", sa.Boolean(), nullable=False),
        sa.Column("findings", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_detection_receipts_workspace_time",
        "detection_receipts",
        ["workspace_id", "evaluated_at"],
    )


def downgrade() -> None:
    op.drop_table("detection_receipts")
