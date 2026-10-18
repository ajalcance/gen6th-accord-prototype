"""Persona fixture persistence and PostgreSQL protections (ADR-0024).

Revision ID: 0003personas
Revises: 0002source
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003personas"
down_revision: str | Sequence[str] | None = "0002source"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen DDL: future model edits must add a new migration.
STATEMENTS: tuple[str, ...] = (
    "CREATE INDEX ix_events_tenant_category_source_ts ON events (tenant_id, category, source, ts)",
    """CREATE TABLE persona_workspace_members (
	workspace_id UUID NOT NULL,
	actor_ref VARCHAR(64) NOT NULL,
	role VARCHAR(16) NOT NULL,
	PRIMARY KEY (workspace_id, actor_ref),
	CHECK (role IN ('creator', 'reviewer', 'viewer'))
)""",
    """CREATE TABLE personas (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	owner_ref VARCHAR(64) NOT NULL,
	head_revision INTEGER NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (workspace_id, id),
	FOREIGN KEY(workspace_id, owner_ref) REFERENCES persona_workspace_members
        (workspace_id, actor_ref),
	CHECK (head_revision >= 1)
)""",
    """CREATE TABLE persona_versions (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	persona_id UUID NOT NULL,
	revision INTEGER NOT NULL,
	creator_ref VARCHAR(64) NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	name VARCHAR(80) NOT NULL,
	biography VARCHAR(500) NOT NULL,
	human_contribution VARCHAR(500) NOT NULL,
	ai_disclosure VARCHAR(500) NOT NULL,
	fixture BOOLEAN NOT NULL,
	event_id VARCHAR(32) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(workspace_id, persona_id) REFERENCES personas (workspace_id, id),
	UNIQUE (workspace_id, id),
	UNIQUE (persona_id, revision),
	CHECK (revision >= 1 AND fixture = true),
	CHECK (length(trim(name)) > 0 AND length(trim(biography)) > 0),
	CHECK (length(trim(human_contribution)) > 0 AND length(trim(ai_disclosure)) > 0),
	UNIQUE (event_id)
)""",
    """CREATE TABLE persona_write_receipts (
	workspace_id UUID NOT NULL,
	actor_ref VARCHAR(64) NOT NULL,
	request_id UUID NOT NULL,
	fingerprint VARCHAR(64) NOT NULL,
	version_id UUID NOT NULL,
	PRIMARY KEY (workspace_id, actor_ref, request_id),
	UNIQUE (version_id),
	FOREIGN KEY(workspace_id, version_id) REFERENCES persona_versions (workspace_id, id),
	FOREIGN KEY(workspace_id, actor_ref) REFERENCES persona_workspace_members
        (workspace_id, actor_ref)
)""",
    """ALTER TABLE "persona_workspace_members" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "persona_workspace_members" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "persona_workspace_members"
USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """ALTER TABLE "personas" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "personas" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "personas"
USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """ALTER TABLE "persona_versions" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "persona_versions" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "persona_versions"
USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """ALTER TABLE "persona_write_receipts" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "persona_write_receipts" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "persona_write_receipts"
USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """CREATE FUNCTION accord_persona_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'persona versions and replay receipts are immutable';
END;
$$""",
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_versions"
FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_write_receipts"
FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
)


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(sa.text(statement))


def downgrade() -> None:
    for name in (
        "persona_write_receipts",
        "persona_versions",
        "personas",
        "persona_workspace_members",
    ):
        op.drop_table(name)
    op.execute(sa.text("DROP FUNCTION accord_persona_immutable()"))
    op.drop_index("ix_events_tenant_category_source_ts", table_name="events")
