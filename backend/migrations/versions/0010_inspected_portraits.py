"""Inspected encrypted portraits; no destructive rollback of populated photo history."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010portraits"
down_revision: str | Sequence[str] | None = "0009identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen SQL, deliberately independent of changing runtime models.
STATEMENTS: tuple[str, ...] = (
    """CREATE TABLE persona_portraits (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	owner_ref VARCHAR(64) NOT NULL,
	request_id UUID NOT NULL,
	fingerprint VARCHAR(64) NOT NULL,
	media_type VARCHAR(24) NOT NULL,
	sha256 VARCHAR(64) NOT NULL,
	thumbnail_sha256 VARCHAR(64) NOT NULL,
	byte_length INTEGER NOT NULL,
	width INTEGER NOT NULL,
	height INTEGER NOT NULL,
	engine VARCHAR(80) NOT NULL,
	definitions VARCHAR(80) NOT NULL,
	derivative_definitions VARCHAR(80) NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (workspace_id, id),
	UNIQUE (workspace_id, owner_ref, request_id),
	FOREIGN KEY(workspace_id, owner_ref)
        REFERENCES persona_workspace_members (workspace_id, actor_ref),
	CHECK (media_type IN ('image/png', 'image/jpeg')),
	CHECK (byte_length BETWEEN 1 AND 10485760),
	CHECK (width BETWEEN 1 AND 320 AND height BETWEEN 1 AND 320),
	CHECK (sha256 ~ '^[0-9a-f]{64}$' AND thumbnail_sha256 ~ '^[0-9a-f]{64}$'),
	CHECK (expires_at = recorded_at + interval '24 hours'),
	CHECK (length(trim(engine)) > 0
        AND length(trim(definitions)) > 0
        AND length(trim(derivative_definitions)) > 0)
)""",
    """CREATE TABLE persona_portrait_payloads (
	portrait_id UUID NOT NULL,
	part VARCHAR(16) NOT NULL,
	workspace_id UUID NOT NULL,
	ciphertext BYTEA NOT NULL,
	nonce BYTEA NOT NULL,
	key_id VARCHAR(120) NOT NULL,
	wrapped_key BYTEA NOT NULL,
	PRIMARY KEY (portrait_id, part),
	FOREIGN KEY(workspace_id, portrait_id) REFERENCES persona_portraits (workspace_id, id),
	CHECK (part IN ('original', 'thumbnail')),
	CHECK (octet_length(ciphertext) BETWEEN 17 AND 10485776),
	CHECK (part != 'thumbnail' OR octet_length(ciphertext) <= 1048592),
	CHECK (octet_length(nonce) = 12),
	CHECK (octet_length(wrapped_key) BETWEEN 1 AND 4096 AND length(key_id) > 0)
)""",
    """CREATE TABLE persona_version_portraits (
	version_id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	portrait_id UUID NOT NULL,
	PRIMARY KEY (version_id),
	FOREIGN KEY(workspace_id, version_id) REFERENCES persona_versions (workspace_id, id),
	FOREIGN KEY(workspace_id, portrait_id) REFERENCES persona_portraits (workspace_id, id)
)""",
    """ALTER TABLE "persona_portraits" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "persona_portraits" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "persona_portraits"
        USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
        WITH CHECK (workspace_id =
            NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_portraits"
        FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
    """ALTER TABLE "persona_portrait_payloads" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "persona_portrait_payloads" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "persona_portrait_payloads"
        USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
        WITH CHECK (workspace_id =
            NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_portrait_payloads"
        FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
    """ALTER TABLE "persona_version_portraits" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "persona_version_portraits" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "persona_version_portraits"
        USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
        WITH CHECK (workspace_id =
            NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_version_portraits"
        FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
)


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(sa.text(statement))


def downgrade() -> None:
    op.execute(sa.text("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user
                     AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'portrait rollback requires an all-tenant migration role';
      END IF;
    END $$"""))
    op.execute(
        sa.text(
            "LOCK TABLE persona_portraits, persona_portrait_payloads, "
            "persona_version_portraits IN ACCESS EXCLUSIVE MODE"
        )
    )
    op.execute(sa.text("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM persona_portraits) THEN
        RAISE EXCEPTION 'portrait rollback refuses populated history';
      END IF;
    END $$"""))
    for name in ("persona_version_portraits", "persona_portrait_payloads", "persona_portraits"):
        op.drop_table(name)
