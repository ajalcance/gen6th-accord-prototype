"""Immutable encrypted face generations; owner activation and rollback review required."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012faces"
down_revision: str | Sequence[str] | None = "0011captures"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE persona_version_references ADD CONSTRAINT "
            "uq_reference_face_subject UNIQUE (workspace_id, version_id, portrait_id)"
        )
    )
    op.execute(sa.text("""CREATE TABLE persona_face_generations (
      id UUID PRIMARY KEY, workspace_id UUID NOT NULL, version_id UUID NOT NULL,
      portrait_id UUID NOT NULL, request_id UUID NOT NULL, actor_ref VARCHAR(160) NOT NULL,
      fingerprint VARCHAR(64) NOT NULL, recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
      ciphertext BYTEA NOT NULL, nonce BYTEA NOT NULL, key_id VARCHAR(120) NOT NULL,
      wrapped_key BYTEA NOT NULL, UNIQUE (workspace_id, request_id),
      FOREIGN KEY (workspace_id, version_id, portrait_id) REFERENCES
        persona_version_references (workspace_id, version_id, portrait_id),
      CHECK (fingerprint ~ '^[0-9a-f]{64}$' AND length(actor_ref) > 0),
      CHECK (octet_length(ciphertext) BETWEEN 17 AND 131088 AND octet_length(nonce) = 12),
      CHECK (octet_length(wrapped_key) BETWEEN 1 AND 4096 AND length(key_id) > 0)
    )"""))
    op.execute(
        sa.text(
            "CREATE INDEX ix_face_subject_generation ON persona_face_generations "
            "(workspace_id, version_id, portrait_id, recorded_at)"
        )
    )
    op.execute(sa.text('ALTER TABLE "persona_face_generations" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text('ALTER TABLE "persona_face_generations" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text("""CREATE POLICY tenant_scope ON "persona_face_generations"
      USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
      WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""")
    )
    op.execute(sa.text("""CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE
      ON persona_face_generations FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()"""))


def downgrade() -> None:
    op.execute(sa.text("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user
                     AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'face rollback requires an all-tenant migration role';
      END IF;
    END $$"""))
    op.execute(sa.text("LOCK TABLE persona_face_generations IN ACCESS EXCLUSIVE MODE"))
    op.execute(sa.text("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM persona_face_generations) THEN
        RAISE EXCEPTION 'face rollback refuses populated history';
      END IF;
    END $$"""))
    op.drop_table("persona_face_generations")
    op.execute(
        sa.text("ALTER TABLE persona_version_references DROP CONSTRAINT uq_reference_face_subject")
    )
