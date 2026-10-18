"""Explicit asset enrollment and persisted private/public passport records."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016passports"
down_revision: str | Sequence[str] | None = "0015jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATEMENTS = (
    """ALTER TABLE persona_private_evidence ADD CONSTRAINT uq_private_evidence_version
UNIQUE (workspace_id, version_id, id)""",
    """ALTER TABLE persona_campaign_decisions ADD CONSTRAINT uq_campaign_decision_scope
UNIQUE (workspace_id, campaign_id, id)""",
    """CREATE TABLE persona_asset_enrollments ( asset_id UUID NOT NULL, workspace_id UUID NOT NULL,
version_id UUID NOT NULL, evidence_id UUID NOT NULL, owner_ref VARCHAR(64) NOT NULL,
request_id UUID NOT NULL, fingerprint VARCHAR(64) NOT NULL, permission_statement VARCHAR(500)
NOT NULL, recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, PRIMARY KEY (asset_id), UNIQUE
(workspace_id, owner_ref, request_id), UNIQUE (workspace_id, version_id, evidence_id), FOREIGN
KEY(workspace_id, version_id, asset_id) REFERENCES persona_assets (workspace_id, version_id,
id), FOREIGN KEY(workspace_id, version_id, evidence_id) REFERENCES persona_private_evidence
(workspace_id, version_id, id) )""",
    """CREATE TABLE persona_passport_issuances ( id UUID NOT NULL, workspace_id UUID NOT NULL,
campaign_id UUID NOT NULL, acceptance_id UUID NOT NULL, package JSONB NOT NULL, recorded_at
TIMESTAMP WITH TIME ZONE NOT NULL, PRIMARY KEY (id), UNIQUE (workspace_id, id), UNIQUE
(workspace_id, campaign_id, acceptance_id), FOREIGN KEY(workspace_id, campaign_id) REFERENCES
persona_campaign_offers (workspace_id, id), FOREIGN KEY(workspace_id, campaign_id, acceptance_id)
REFERENCES persona_campaign_decisions (workspace_id, campaign_id, id),
CHECK (jsonb_typeof(package) = 'object' AND
octet_length(package::text) <= 131072) )""",
    """CREATE TABLE persona_passport_publications ( id UUID NOT NULL, workspace_id UUID NOT NULL,
issuance_id UUID NOT NULL, owner_ref VARCHAR(64) NOT NULL, request_id UUID NOT NULL,
fingerprint VARCHAR(64) NOT NULL, fields JSONB NOT NULL, package JSONB NOT NULL, recorded_at
TIMESTAMP WITH TIME ZONE NOT NULL, PRIMARY KEY (id), UNIQUE (workspace_id, id), UNIQUE
(workspace_id, owner_ref, request_id), FOREIGN KEY(workspace_id, issuance_id) REFERENCES
persona_passport_issuances (workspace_id, id), CHECK (jsonb_typeof(fields) = 'array' AND
jsonb_array_length(fields) BETWEEN 2 AND 8), CHECK (jsonb_typeof(package) = 'object' AND
octet_length(package::text) <= 16384) )""",
    """CREATE TABLE persona_passport_unpublications ( publication_id UUID NOT NULL,
workspace_id UUID NOT NULL, owner_ref VARCHAR(64) NOT NULL,
recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
PRIMARY KEY (publication_id), FOREIGN KEY(workspace_id, publication_id) REFERENCES
persona_passport_publications (workspace_id, id) )""",
    """ALTER TABLE "persona_asset_enrollments" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "persona_asset_enrollments" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "persona_asset_enrollments" USING (workspace_id =
NULLIF(current_setting('accord.workspace_id', true), '')::uuid) WITH CHECK (workspace_id =
NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_asset_enrollments" FOR
EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
    """ALTER TABLE "persona_passport_issuances" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "persona_passport_issuances" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "persona_passport_issuances" USING (workspace_id =
NULLIF(current_setting('accord.workspace_id', true), '')::uuid) WITH CHECK (workspace_id =
NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_passport_issuances" FOR
EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
    """ALTER TABLE "persona_passport_publications" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "persona_passport_publications" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "persona_passport_publications" USING (workspace_id =
NULLIF(current_setting('accord.workspace_id', true), '')::uuid) WITH CHECK (workspace_id =
NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_passport_publications"
FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
    """ALTER TABLE "persona_passport_unpublications" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "persona_passport_unpublications" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "persona_passport_unpublications" USING (workspace_id =
NULLIF(current_setting('accord.workspace_id', true), '')::uuid) WITH CHECK (workspace_id =
NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_passport_unpublications"
FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
)

TABLES = (
    "persona_passport_unpublications",
    "persona_passport_publications",
    "persona_passport_issuances",
    "persona_asset_enrollments",
)


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(sa.text(statement))


def downgrade() -> None:
    op.execute(sa.text("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user
                     AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'passport rollback requires an all-tenant migration role';
      END IF;
    END $$"""))
    op.execute(sa.text("""LOCK TABLE persona_passport_unpublications,
      persona_passport_publications, persona_passport_issuances, persona_asset_enrollments
      IN ACCESS EXCLUSIVE MODE"""))
    op.execute(sa.text("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM persona_passport_unpublications)
        OR EXISTS (SELECT 1 FROM persona_passport_publications)
        OR EXISTS (SELECT 1 FROM persona_passport_issuances)
        OR EXISTS (SELECT 1 FROM persona_asset_enrollments) THEN
        RAISE EXCEPTION 'passport rollback refuses populated records';
      END IF;
    END $$"""))
    for name in TABLES:
        op.drop_table(name)
    op.drop_constraint("uq_campaign_decision_scope", "persona_campaign_decisions", type_="unique")
    op.drop_constraint("uq_private_evidence_version", "persona_private_evidence", type_="unique")
