"""Append-only version-bound fixture reviews, following persona persistence."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004reviews"
down_revision: str | Sequence[str] | None = "0003personas"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen independently of runtime models and policy helpers.
STATEMENTS: tuple[str, ...] = (
    """CREATE TABLE persona_reviews (
        id UUID NOT NULL PRIMARY KEY,
        workspace_id UUID NOT NULL,
        version_id UUID NOT NULL,
        ordinal INTEGER NOT NULL,
        reviewer_ref VARCHAR(64) NOT NULL,
        request_id UUID NOT NULL,
        fingerprint VARCHAR(64) NOT NULL,
        decision VARCHAR(24) NOT NULL,
        statement VARCHAR(500) NOT NULL,
        recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
        event_id VARCHAR(32) NOT NULL UNIQUE,
        fixture BOOLEAN NOT NULL,
        UNIQUE (workspace_id, id),
        UNIQUE (workspace_id, version_id, id),
        UNIQUE (workspace_id, reviewer_ref, request_id),
        UNIQUE (version_id, ordinal),
        FOREIGN KEY (workspace_id, version_id) REFERENCES persona_versions (workspace_id, id),
        FOREIGN KEY (workspace_id, reviewer_ref) REFERENCES persona_workspace_members
            (workspace_id, actor_ref),
        CHECK (ordinal >= 1 AND fixture = true),
        CHECK (decision IN ('approved', 'changes_requested')),
        CHECK (length(trim(statement)) > 0)
    )""",
    'ALTER TABLE "persona_reviews" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "persona_reviews" FORCE ROW LEVEL SECURITY',
    """CREATE POLICY tenant_scope ON "persona_reviews"
        USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
        WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
    """,
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_reviews"
        FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
)


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(sa.text(statement))


def downgrade() -> None:
    op.drop_table("persona_reviews")
