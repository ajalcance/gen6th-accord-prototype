"""Real record contracts; refuse populated sample stores rather than relabel history."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008realrecords"
down_revision: str | Sequence[str] | None = "0007evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CHECKS = (
    ("persona_versions", "ck_persona_versions_revision", "revision >= 1"),
    ("persona_reviews", "ck_persona_reviews_ordinal", "ordinal >= 1"),
    ("persona_assets", "ck_persona_assets_label", "length(trim(label)) > 0"),
    ("persona_campaign_offers", "ck_persona_campaign_parties", "owner_ref <> recipient_ref"),
    ("persona_campaign_decisions", "ck_persona_campaign_ordinal", "ordinal >= 1"),
)


def require_empty() -> None:
    # Counts must see every tenant despite forced RLS; a confined role cannot certify emptiness.
    op.execute(sa.text("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user
                     AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'record transition requires an all-tenant migration role';
      END IF;
    END $$"""))
    op.execute(sa.text("""LOCK TABLE persona_versions, persona_reviews, persona_assets,
                         persona_campaign_offers, persona_campaign_decisions
                         IN ACCESS EXCLUSIVE MODE"""))
    op.execute(sa.text("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM persona_versions)
        OR EXISTS (SELECT 1 FROM persona_reviews)
        OR EXISTS (SELECT 1 FROM persona_assets)
        OR EXISTS (SELECT 1 FROM persona_campaign_offers)
        OR EXISTS (SELECT 1 FROM persona_campaign_decisions) THEN
        RAISE EXCEPTION 'record transition refuses populated history; archive review required';
      END IF;
    END $$"""))


def upgrade() -> None:
    op.rename_table("persona_fixture_assets", "persona_assets")
    require_empty()
    for table, name, condition in CHECKS:
        # PostgreSQL removes only CHECKs referencing this column; all other protections stay.
        op.drop_column(table, "fixture")
        op.create_check_constraint(name, table, condition)


def downgrade() -> None:
    require_empty()
    for table, name, condition in CHECKS:
        op.drop_constraint(name, table, type_="check")
        op.add_column(table, sa.Column("fixture", sa.Boolean(), nullable=False))
        old_table = "persona_fixture_assets" if table == "persona_assets" else table
        op.create_check_constraint(f"{old_table}_check", table, f"{condition} AND fixture = true")
    op.rename_table("persona_assets", "persona_fixture_assets")
