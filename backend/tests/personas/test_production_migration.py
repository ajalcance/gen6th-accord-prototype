"""Offline migration evidence only; SQL constraints and rollback need owner/CI execution."""

from personas.test_migration_sql import render_upgrade


def test_production_migration_extends_immutable_offers_without_rewriting_history() -> None:
    sql = render_upgrade()
    assert "0014production" in sql
    assert "ADD COLUMN production JSONB" in sql
    assert "ck_campaign_production_bound" in sql
    assert "jsonb_typeof(production) = 'object'" in sql
    assert "octet_length(production::text) <= 8192" in sql
    assert "UPDATE persona_campaign_offers" not in sql
