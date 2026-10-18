"""Prepare lifecycle history; owner/CI executes accepted migrations separately."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018lifecycle"
down_revision: str | Sequence[str] | None = "0017credits"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_version_lifecycle_binding", "persona_versions", ["workspace_id", "persona_id", "id"]
    )
    op.execute(sa.text("""CREATE TABLE persona_lifecycle_records (
      id UUID PRIMARY KEY, workspace_id UUID NOT NULL, persona_id UUID NOT NULL,
      version_id UUID NOT NULL, request_id UUID NOT NULL, expected_previous_id UUID,
      target_id UUID, ordinal INTEGER NOT NULL, actor_ref VARCHAR(64) NOT NULL,
      kind VARCHAR(16) NOT NULL, requirement VARCHAR(16),
      recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, fingerprint VARCHAR(64) NOT NULL,
      content JSONB NOT NULL, evidence_digests JSONB NOT NULL,
      UNIQUE (workspace_id, actor_ref, request_id),
      UNIQUE (workspace_id, persona_id, ordinal), UNIQUE (workspace_id, persona_id, id),
      FOREIGN KEY (workspace_id, persona_id) REFERENCES personas (workspace_id, id),
      FOREIGN KEY (workspace_id, version_id) REFERENCES persona_versions (workspace_id, id),
      FOREIGN KEY (workspace_id, persona_id, version_id)
        REFERENCES persona_versions (workspace_id, persona_id, id),
      FOREIGN KEY (workspace_id, actor_ref)
        REFERENCES persona_workspace_members (workspace_id, actor_ref),
      FOREIGN KEY (workspace_id, persona_id, target_id)
        REFERENCES persona_lifecycle_records (workspace_id, persona_id, id),
      FOREIGN KEY (workspace_id, persona_id, expected_previous_id)
        REFERENCES persona_lifecycle_records (workspace_id, persona_id, id),
      CHECK (ordinal >= 1 AND fingerprint ~ '^[0-9a-f]{64}$'),
      CHECK (kind IN ('dossier', 'assessment', 'concern', 'response') AND content->>'kind' = kind),
      CHECK ((kind IN ('assessment', 'response')) = (target_id IS NOT NULL)),
      CHECK ((kind = 'assessment' AND requirement IS NOT NULL
        AND requirement IN ('operator', 'rights', 'content'))
        OR (kind <> 'assessment' AND requirement IS NULL)),
      CHECK (jsonb_typeof(content) = 'object' AND octet_length(content::text) <= 16000),
      CHECK (jsonb_typeof(evidence_digests) = 'object'
        AND octet_length(evidence_digests::text) <= 1500)
    )"""))
    op.execute(sa.text('ALTER TABLE "persona_lifecycle_records" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text('ALTER TABLE "persona_lifecycle_records" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text("""CREATE POLICY tenant_scope ON "persona_lifecycle_records"
      USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
      WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""")
    )
    op.execute(sa.text("""CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE
      ON "persona_lifecycle_records"
      FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()"""))


def downgrade() -> None:
    op.execute(sa.text("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user
        AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'lifecycle rollback requires an all-tenant migration role';
      END IF;
    END $$"""))
    op.execute(sa.text('LOCK TABLE "persona_lifecycle_records" IN ACCESS EXCLUSIVE MODE'))
    op.execute(sa.text("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM persona_lifecycle_records) THEN
        RAISE EXCEPTION 'lifecycle rollback refuses populated history';
      END IF;
    END $$"""))
    op.drop_table("persona_lifecycle_records")
    op.drop_constraint("uq_version_lifecycle_binding", "persona_versions", type_="unique")
