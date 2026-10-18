"""Private evidence quarantine with independent encrypted-payload retention."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007evidence"
down_revision: str | Sequence[str] | None = "0006detection"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen SQL: never import changing runtime models or policy helpers.
STATEMENTS: tuple[str, ...] = (
    """CREATE TABLE persona_private_evidence (
        id UUID NOT NULL,
        workspace_id UUID NOT NULL,
        version_id UUID NOT NULL,
        owner_ref VARCHAR(64) NOT NULL,
        request_id UUID NOT NULL,
        fingerprint VARCHAR(64) NOT NULL,
        media_type VARCHAR(24) NOT NULL,
        byte_length INTEGER NOT NULL,
        sha256 VARCHAR(64) NOT NULL,
        recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        PRIMARY KEY (id),
        UNIQUE (workspace_id, id),
        UNIQUE (workspace_id, owner_ref, request_id),
        FOREIGN KEY(workspace_id, version_id) REFERENCES persona_versions (workspace_id, id),
        FOREIGN KEY(workspace_id, owner_ref)
            REFERENCES persona_workspace_members (workspace_id, actor_ref),
        CHECK (byte_length BETWEEN 1 AND 10485760),
        CHECK (sha256 ~ '^[0-9a-f]{64}$'),
        CHECK (media_type IN ('image/png', 'image/jpeg', 'text/plain')),
        CHECK (expires_at = recorded_at + interval '7 days')
    )""",
    """CREATE TABLE private_evidence_payloads (
        evidence_id UUID NOT NULL,
        workspace_id UUID NOT NULL,
        ciphertext BYTEA NOT NULL,
        nonce BYTEA NOT NULL,
        key_id VARCHAR(120) NOT NULL,
        wrapped_key BYTEA NOT NULL,
        PRIMARY KEY (evidence_id),
        FOREIGN KEY(workspace_id, evidence_id)
            REFERENCES persona_private_evidence (workspace_id, id),
        CHECK (octet_length(ciphertext) BETWEEN 17 AND 10485776),
        CHECK (octet_length(nonce) = 12),
        CHECK (octet_length(wrapped_key) BETWEEN 1 AND 4096 AND length(key_id) > 0)
    )""",
    """CREATE TABLE persona_evidence_inspections (
        evidence_id UUID NOT NULL,
        workspace_id UUID NOT NULL,
        verdict VARCHAR(16) NOT NULL,
        engine VARCHAR(80) NOT NULL,
        definitions VARCHAR(80) NOT NULL,
        inspected_at TIMESTAMP WITH TIME ZONE NOT NULL,
        PRIMARY KEY (evidence_id),
        FOREIGN KEY(workspace_id, evidence_id)
            REFERENCES persona_private_evidence (workspace_id, id),
        CHECK (verdict IN ('clean', 'rejected')),
        CHECK (length(trim(engine)) > 0 AND length(trim(definitions)) > 0)
    )""",
    'ALTER TABLE "persona_private_evidence" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "persona_private_evidence" FORCE ROW LEVEL SECURITY',
    """CREATE POLICY tenant_scope ON "persona_private_evidence"
        USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
        WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
    """,
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_private_evidence"
        FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
    'ALTER TABLE "private_evidence_payloads" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "private_evidence_payloads" FORCE ROW LEVEL SECURITY',
    """CREATE POLICY private_payload_scope ON "private_evidence_payloads"
        USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
        WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
    """,
    'ALTER TABLE "persona_evidence_inspections" ENABLE ROW LEVEL SECURITY',
    'ALTER TABLE "persona_evidence_inspections" FORCE ROW LEVEL SECURITY',
    """CREATE POLICY tenant_scope ON "persona_evidence_inspections"
        USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
        WITH CHECK (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid)
    """,
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_evidence_inspections"
        FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
    """CREATE FUNCTION accord_evidence_payload_expiry() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE expires TIMESTAMP WITH TIME ZONE;
    BEGIN
        IF TG_OP <> 'DELETE' THEN
            RAISE EXCEPTION 'encrypted payload is immutable';
        END IF;
        SELECT expires_at INTO expires FROM persona_private_evidence
            WHERE id = OLD.evidence_id AND workspace_id = OLD.workspace_id;
        IF expires IS NULL OR expires > clock_timestamp() THEN
            RAISE EXCEPTION 'encrypted payload has not expired';
        END IF;
        RETURN OLD;
    END;
    $$""",
    """CREATE TRIGGER payload_expiry BEFORE UPDATE OR DELETE
    ON private_evidence_payloads FOR EACH ROW EXECUTE FUNCTION accord_evidence_payload_expiry()""",
)


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(sa.text(statement))


def downgrade() -> None:
    op.drop_table("persona_evidence_inspections")
    op.drop_table("private_evidence_payloads")
    op.execute(sa.text("DROP FUNCTION accord_evidence_payload_expiry()"))
    op.drop_table("persona_private_evidence")
