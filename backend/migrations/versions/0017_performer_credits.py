"""Append-only version annotations; prepare only until owner-approved activation."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017credits"
down_revision: str | Sequence[str] | None = "0016passports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("""CREATE TABLE persona_credit_profiles (
      id UUID PRIMARY KEY, workspace_id UUID NOT NULL, version_id UUID NOT NULL,
      request_id UUID NOT NULL, ordinal INTEGER NOT NULL, declared_by VARCHAR(64) NOT NULL,
      recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, fingerprint VARCHAR(64) NOT NULL,
      content JSONB NOT NULL, UNIQUE (workspace_id, declared_by, request_id),
      UNIQUE (workspace_id, version_id, ordinal), UNIQUE (workspace_id, version_id, id),
      FOREIGN KEY (workspace_id, version_id) REFERENCES persona_versions (workspace_id, id),
      CHECK (ordinal >= 1 AND fingerprint ~ '^[0-9a-f]{64}$'),
      CHECK (jsonb_typeof(content) = 'object' AND octet_length(content::text) <= 12000)
    )"""))
    op.execute(sa.text("""CREATE TABLE persona_credit_confirmations (
      id UUID PRIMARY KEY, workspace_id UUID NOT NULL, version_id UUID NOT NULL,
      profile_id UUID NOT NULL, request_id UUID NOT NULL, credit_index INTEGER NOT NULL,
      actor_ref VARCHAR(64) NOT NULL, fingerprint VARCHAR(64) NOT NULL,
      recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
      UNIQUE (workspace_id, actor_ref, request_id), UNIQUE (workspace_id, profile_id, credit_index),
      FOREIGN KEY (workspace_id, version_id, profile_id) REFERENCES
        persona_credit_profiles (workspace_id, version_id, id),
      FOREIGN KEY (workspace_id, actor_ref) REFERENCES
        persona_workspace_members (workspace_id, actor_ref),
      CHECK (credit_index BETWEEN 0 AND 11 AND fingerprint ~ '^[0-9a-f]{64}$')
    )"""))
    for name in ("persona_credit_profiles", "persona_credit_confirmations"):
        op.execute(sa.text(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY'))
        op.execute(
            sa.text(
                f'CREATE POLICY tenant_scope ON "{name}" '
                "USING (workspace_id = "
                "NULLIF(current_setting('accord.workspace_id', true), '')::uuid) "
                "WITH CHECK (workspace_id = "
                "NULLIF(current_setting('accord.workspace_id', true), '')::uuid)"
            )
        )
        op.execute(
            sa.text(
                f'CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "{name}" '
                "FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()"
            )
        )


def downgrade() -> None:
    op.execute(sa.text("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user
                     AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'credit rollback requires an all-tenant migration role';
      END IF;
    END $$"""))
    op.execute(
        sa.text(
            "LOCK TABLE persona_credit_profiles, persona_credit_confirmations "
            "IN ACCESS EXCLUSIVE MODE"
        )
    )
    op.execute(sa.text("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM persona_credit_profiles)
         OR EXISTS (SELECT 1 FROM persona_credit_confirmations) THEN
        RAISE EXCEPTION 'credit rollback refuses populated history';
      END IF;
    END $$"""))
    op.drop_table("persona_credit_confirmations")
    op.drop_table("persona_credit_profiles")
