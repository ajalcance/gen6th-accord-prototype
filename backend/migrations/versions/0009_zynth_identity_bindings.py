"""Server-owned canonical identity bindings; no login grants or seeded memberships."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009identity"
down_revision: str | Sequence[str] | None = "0008realrecords"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATEMENTS = (
    """CREATE TABLE persona_identity_bindings (
      workspace_id UUID NOT NULL, issuer VARCHAR(512) NOT NULL, subject UUID NOT NULL,
      tenant_id UUID NOT NULL, actor_ref VARCHAR(64) NOT NULL,
      PRIMARY KEY (workspace_id, issuer, subject),
      UNIQUE (issuer, tenant_id, subject), UNIQUE (workspace_id, actor_ref),
      FOREIGN KEY (workspace_id, actor_ref) REFERENCES persona_workspace_members
        (workspace_id, actor_ref))""",
    'ALTER TABLE "persona_identity_bindings" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "persona_identity_bindings" FORCE ROW LEVEL SECURITY',
    """CREATE POLICY tenant_scope ON "persona_identity_bindings"
      USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
      WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """CREATE FUNCTION accord_identity_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN RAISE EXCEPTION 'identity bindings are immutable'; END; $$""",
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON persona_identity_bindings
      FOR EACH ROW EXECUTE FUNCTION accord_identity_immutable()""",
)


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(sa.text(statement))
    op.execute(sa.text("""CREATE FUNCTION accord_workspace_membership(w UUID, a VARCHAR)
      RETURNS VARCHAR LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
      DECLARE result VARCHAR;
      BEGIN
        IF w IS DISTINCT FROM NULLIF(current_setting('accord.workspace_id', true), '')::uuid THEN
          RETURN NULL;
        END IF;
        SELECT role INTO result FROM public.persona_workspace_members
          WHERE workspace_id = w AND actor_ref = a FOR UPDATE;
        RETURN result;
      END; $$"""))
    op.execute(
        sa.text("REVOKE ALL ON FUNCTION accord_workspace_membership(UUID, VARCHAR) FROM PUBLIC")
    )


def downgrade() -> None:
    op.execute(sa.text("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user
                     AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'identity rollback requires an all-tenant migration role';
      END IF;
    END $$"""))
    op.execute(sa.text("LOCK TABLE persona_identity_bindings IN ACCESS EXCLUSIVE MODE"))
    op.execute(sa.text("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM persona_identity_bindings) THEN
        RAISE EXCEPTION 'identity rollback refuses populated bindings';
      END IF;
    END $$"""))
    op.drop_table("persona_identity_bindings")
    op.execute(sa.text("DROP FUNCTION accord_identity_immutable()"))
    op.execute(sa.text("DROP FUNCTION accord_workspace_membership(UUID, VARCHAR)"))
