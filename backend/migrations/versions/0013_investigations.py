"""Encrypted immutable exact-version analysis history; activation requires owner review."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013investigation"
down_revision: str | Sequence[str] | None = "0012faces"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("""CREATE TABLE persona_investigations (
      id UUID PRIMARY KEY, workspace_id UUID NOT NULL, version_id UUID NOT NULL,
      portrait_id UUID NOT NULL, request_id UUID NOT NULL, actor_ref VARCHAR(160) NOT NULL,
      ordinal INTEGER NOT NULL, fingerprint VARCHAR(64) NOT NULL,
      recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
      ciphertext BYTEA NOT NULL, nonce BYTEA NOT NULL, key_id VARCHAR(120) NOT NULL,
      wrapped_key BYTEA NOT NULL, UNIQUE (workspace_id, actor_ref, request_id),
      UNIQUE (workspace_id, version_id, ordinal),
      UNIQUE (workspace_id, version_id, id),
      FOREIGN KEY (workspace_id, version_id, portrait_id) REFERENCES
        persona_version_references (workspace_id, version_id, portrait_id),
      CHECK (ordinal >= 1 AND fingerprint ~ '^[0-9a-f]{64}$' AND length(actor_ref) > 0),
      CHECK (octet_length(ciphertext) BETWEEN 17 AND 65552 AND octet_length(nonce) = 12),
      CHECK (octet_length(wrapped_key) BETWEEN 1 AND 4096 AND length(key_id) > 0)
    )"""))
    op.execute(sa.text('ALTER TABLE "persona_investigations" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text('ALTER TABLE "persona_investigations" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text("""CREATE POLICY tenant_scope ON "persona_investigations"
      USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
      WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""")
    )
    op.execute(sa.text("""CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE
      ON "persona_investigations" FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()"""))
    review_requests()


def review_requests() -> None:
    op.execute(sa.text("""CREATE TABLE persona_investigation_review_requests (
      id UUID PRIMARY KEY, workspace_id UUID NOT NULL, version_id UUID NOT NULL,
      investigation_id UUID NOT NULL, request_id UUID NOT NULL, ordinal INTEGER NOT NULL,
      requester_ref VARCHAR(160) NOT NULL, requested_at TIMESTAMP WITH TIME ZONE NOT NULL,
      UNIQUE (workspace_id, requester_ref, request_id), UNIQUE (workspace_id, version_id, ordinal),
      FOREIGN KEY (workspace_id, version_id, investigation_id) REFERENCES
        persona_investigations (workspace_id, version_id, id),
      CHECK (ordinal >= 1 AND length(requester_ref) > 0)
    )"""))
    op.execute(
        sa.text('ALTER TABLE "persona_investigation_review_requests" ENABLE ROW LEVEL SECURITY')
    )
    op.execute(
        sa.text('ALTER TABLE "persona_investigation_review_requests" FORCE ROW LEVEL SECURITY')
    )
    op.execute(
        sa.text("""CREATE POLICY tenant_scope ON "persona_investigation_review_requests"
      USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
      WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""")
    )
    op.execute(sa.text("""CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE
      ON "persona_investigation_review_requests" FOR EACH ROW
      EXECUTE FUNCTION accord_persona_immutable()"""))


def downgrade() -> None:
    op.execute(sa.text("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user
                     AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'investigation rollback requires an all-tenant migration role';
      END IF;
    END $$"""))
    op.execute(
        sa.text(
            "LOCK TABLE persona_investigations, persona_investigation_review_requests "
            "IN ACCESS EXCLUSIVE MODE"
        )
    )
    op.execute(sa.text("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM persona_investigations) THEN
        RAISE EXCEPTION 'investigation rollback refuses populated history';
      END IF;
    END $$"""))
    op.drop_table("persona_investigation_review_requests")
    op.drop_table("persona_investigations")
