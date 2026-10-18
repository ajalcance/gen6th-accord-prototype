"""Frozen migration and metadata guarantees; offline proof is separate from SQL execution."""

from typing import cast

from sqlalchemy import Table, UniqueConstraint

from accord.personas.asset_models import AssetEnrollment
from accord.personas.issuance_models import (
    PassportIssuance,
    PassportPublication,
    PassportUnpublication,
)
from personas.test_migration_sql import render_upgrade


def test_asset_passport_migration_has_forced_rls_immutable_records_and_uniqueness() -> None:
    sql = " ".join(render_upgrade().split())
    assert "0016passports" in sql
    for model in (AssetEnrollment, PassportIssuance, PassportPublication, PassportUnpublication):
        assert f"CREATE TABLE {model.__tablename__}" in sql
        assert f'ALTER TABLE "{model.__tablename__}" FORCE ROW LEVEL SECURITY' in sql
        assert f'BEFORE UPDATE OR DELETE ON "{model.__tablename__}"' in sql
    assert "UNIQUE (workspace_id, campaign_id, acceptance_id)" in sql
    assert "UNIQUE (workspace_id, version_id, evidence_id)" in sql
    assert "REFERENCES persona_campaign_decisions (workspace_id, campaign_id, id)" in sql
    assert "REFERENCES persona_private_evidence (workspace_id, version_id, id)" in sql
    table = cast(Table, PassportIssuance.__table__)
    assert any(
        tuple(column.name for column in constraint.columns)
        == ("workspace_id", "campaign_id", "acceptance_id")
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    )
