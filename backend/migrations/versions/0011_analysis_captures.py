"""Add encrypted analysis provenance and immutable reference approval; never backfill identities."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011captures"
down_revision: str | Sequence[str] | None = "0010portraits"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATEMENTS: tuple[str, ...] = (
    """CREATE TABLE persona_portrait_captures (
      portrait_id UUID NOT NULL PRIMARY KEY,
      workspace_id UUID NOT NULL,
      source_width INTEGER NOT NULL, source_height INTEGER NOT NULL,
      orientation INTEGER NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL,
      sha256 VARCHAR(64) NOT NULL, recipe VARCHAR(40) NOT NULL,
      decoder_version VARCHAR(40) NOT NULL, scanner_engine VARCHAR(80) NOT NULL,
      scanner_definitions VARCHAR(80) NOT NULL, recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
      ciphertext BYTEA NOT NULL, nonce BYTEA NOT NULL, key_id VARCHAR(120) NOT NULL,
      wrapped_key BYTEA NOT NULL,
      UNIQUE (workspace_id, portrait_id),
      FOREIGN KEY (workspace_id, portrait_id) REFERENCES persona_portraits (workspace_id, id),
      CHECK (source_width BETWEEN 1 AND 4096 AND source_height BETWEEN 1 AND 4096
             AND source_width * source_height <= 8000000),
      CHECK (orientation BETWEEN 1 AND 8 AND width BETWEEN 1 AND 1024
             AND height BETWEEN 1 AND 1024),
      CHECK (sha256 ~ '^[0-9a-f]{64}$' AND recipe = 'rgba-png-1024-v1'),
      CHECK (length(trim(decoder_version)) > 0 AND length(trim(scanner_engine)) > 0
             AND length(trim(scanner_definitions)) > 0),
      CHECK (octet_length(ciphertext) BETWEEN 17 AND 5242896 AND octet_length(nonce) = 12),
      CHECK (octet_length(wrapped_key) BETWEEN 1 AND 4096 AND length(key_id) > 0)
    )""",
    """CREATE TABLE persona_version_references (
      version_id UUID NOT NULL, portrait_id UUID NOT NULL, workspace_id UUID NOT NULL,
      position INTEGER NOT NULL,
      PRIMARY KEY (version_id, portrait_id),
      UNIQUE (workspace_id, version_id, position),
      FOREIGN KEY (workspace_id, version_id) REFERENCES persona_versions (workspace_id, id),
      FOREIGN KEY (workspace_id, portrait_id)
        REFERENCES persona_portrait_captures (workspace_id, portrait_id),
      CHECK (position BETWEEN 1 AND 8)
    )""",
)
TABLES = ("persona_portrait_captures", "persona_version_references")


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(sa.text(statement))
    for table in TABLES:
        op.execute(sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f"""CREATE POLICY tenant_scope ON "{table}"
          USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
          WITH CHECK (workspace_id =
            NULLIF(current_setting('accord.workspace_id', true), '')::uuid)"""))
        op.execute(sa.text(f"""CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "{table}"
          FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()"""))


def downgrade() -> None:
    op.execute(sa.text("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user
                     AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'capture rollback requires an all-tenant migration role';
      END IF;
    END $$"""))
    op.execute(
        sa.text(
            "LOCK TABLE persona_portrait_captures, persona_version_references "
            "IN ACCESS EXCLUSIVE MODE"
        )
    )
    op.execute(sa.text("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM persona_portrait_captures)
         OR EXISTS (SELECT 1 FROM persona_version_references) THEN
        RAISE EXCEPTION 'capture rollback refuses populated history';
      END IF;
    END $$"""))
    for table in reversed(TABLES):
        op.drop_table(table)
