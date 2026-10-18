"""Immutable fictional campaign offers, asset bindings and independent decisions."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005campaigns"
down_revision: str | Sequence[str] | None = "0004reviews"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen SQL; do not import runtime models or policy helpers.
TABLES: tuple[str, ...] = (
    "persona_fixture_assets",
    "persona_campaign_offers",
    "persona_campaign_assets",
    "persona_campaign_decisions",
)
STATEMENTS: tuple[str, ...] = (
    """CREATE TABLE persona_fixture_assets (
        id UUID NOT NULL PRIMARY KEY,
        workspace_id UUID NOT NULL,
        version_id UUID NOT NULL,
        digest VARCHAR(64) NOT NULL,
        label VARCHAR(80) NOT NULL,
        fixture BOOLEAN NOT NULL,
        UNIQUE (workspace_id, version_id, id),
        FOREIGN KEY (workspace_id, version_id) REFERENCES persona_versions (workspace_id, id),
        CHECK (fixture = true AND length(trim(label)) > 0),
        CHECK (digest ~ '^[0-9a-f]{64}$')
    )""",
    """CREATE TABLE persona_campaign_offers (
        id UUID NOT NULL PRIMARY KEY,
        workspace_id UUID NOT NULL,
        version_id UUID NOT NULL,
        review_id UUID NOT NULL,
        owner_ref VARCHAR(64) NOT NULL,
        recipient_ref VARCHAR(64) NOT NULL,
        request_id UUID NOT NULL,
        fingerprint VARCHAR(64) NOT NULL,
        name VARCHAR(80) NOT NULL,
        purpose VARCHAR(500) NOT NULL,
        conditions VARCHAR(500) NOT NULL,
        starts_at TIMESTAMP WITH TIME ZONE NOT NULL,
        ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
        recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
        event_id VARCHAR(32) NOT NULL UNIQUE,
        fixture BOOLEAN NOT NULL,
        UNIQUE (workspace_id, id),
        UNIQUE (workspace_id, version_id, id),
        UNIQUE (workspace_id, owner_ref, request_id),
        FOREIGN KEY (workspace_id, version_id, review_id) REFERENCES persona_reviews
            (workspace_id, version_id, id),
        FOREIGN KEY (workspace_id, owner_ref) REFERENCES persona_workspace_members
            (workspace_id, actor_ref),
        FOREIGN KEY (workspace_id, recipient_ref) REFERENCES persona_workspace_members
            (workspace_id, actor_ref),
        CHECK (fixture = true AND owner_ref <> recipient_ref),
        CHECK (ends_at > starts_at AND ends_at <= starts_at + interval '366 days'),
        CHECK (length(trim(name)) > 0 AND length(trim(purpose)) > 0
            AND length(trim(conditions)) > 0)
    )""",
    """CREATE TABLE persona_campaign_assets (
        workspace_id UUID NOT NULL,
        campaign_id UUID NOT NULL,
        asset_id UUID NOT NULL,
        version_id UUID NOT NULL,
        PRIMARY KEY (workspace_id, campaign_id, asset_id),
        FOREIGN KEY (workspace_id, version_id, campaign_id) REFERENCES persona_campaign_offers
            (workspace_id, version_id, id),
        FOREIGN KEY (workspace_id, version_id, asset_id) REFERENCES persona_fixture_assets
            (workspace_id, version_id, id)
    )""",
    """CREATE TABLE persona_campaign_decisions (
        id UUID NOT NULL PRIMARY KEY,
        workspace_id UUID NOT NULL,
        campaign_id UUID NOT NULL,
        ordinal INTEGER NOT NULL,
        actor_ref VARCHAR(64) NOT NULL,
        request_id UUID NOT NULL,
        fingerprint VARCHAR(64) NOT NULL,
        decision VARCHAR(24) NOT NULL,
        statement VARCHAR(500) NOT NULL,
        recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
        event_id VARCHAR(32) NOT NULL UNIQUE,
        fixture BOOLEAN NOT NULL,
        UNIQUE (workspace_id, actor_ref, request_id),
        UNIQUE (campaign_id, ordinal),
        FOREIGN KEY (workspace_id, campaign_id) REFERENCES persona_campaign_offers
            (workspace_id, id),
        FOREIGN KEY (workspace_id, actor_ref) REFERENCES persona_workspace_members
            (workspace_id, actor_ref),
        CHECK (ordinal >= 1 AND fixture = true),
        CHECK (decision IN ('accepted', 'changes_requested', 'revoked')),
        CHECK (length(trim(statement)) > 0)
    )""",
)


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(sa.text(statement))
    for name in TABLES:
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
    for name in reversed(TABLES):
        op.drop_table(name)
