"""Optional immutable production scopes on existing exact-version campaign offers."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0014production"
down_revision: str | Sequence[str] | None = "0013investigation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("persona_campaign_offers", sa.Column("production", JSONB(), nullable=True))
    op.create_check_constraint(
        "ck_campaign_production_bound",
        "persona_campaign_offers",
        "production IS NULL OR (jsonb_typeof(production) = 'object' "
        "AND octet_length(production::text) <= 8192)",
    )


def downgrade() -> None:
    op.execute(sa.text("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user
                     AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'production rollback requires an all-tenant migration role';
      END IF;
    END $$"""))
    op.execute(sa.text("LOCK TABLE persona_campaign_offers IN ACCESS EXCLUSIVE MODE"))
    op.execute(sa.text("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM persona_campaign_offers WHERE production IS NOT NULL) THEN
        RAISE EXCEPTION 'production rollback refuses populated production scopes';
      END IF;
    END $$"""))
    op.drop_constraint("ck_campaign_production_bound", "persona_campaign_offers", type_="check")
    op.drop_column("persona_campaign_offers", "production")
