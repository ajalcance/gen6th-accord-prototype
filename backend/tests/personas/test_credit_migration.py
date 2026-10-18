"""Frozen migration rendering is source proof, not execution against PostgreSQL."""

from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_credit_migration_preserves_scope_and_refuses_populated_rollback() -> None:
    output = StringIO()
    config = Config(output_buffer=output)
    config.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[2] / "migrations")
    )
    config.set_main_option("sqlalchemy.url", "postgresql+asyncpg://localhost/unused")
    command.upgrade(config, "0016passports:0017credits", sql=True)
    sql = " ".join(output.getvalue().split())
    for name in ("persona_credit_profiles", "persona_credit_confirmations"):
        assert f"CREATE TABLE {name}" in sql
        assert f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY' in sql
        assert f'BEFORE UPDATE OR DELETE ON "{name}"' in sql
        assert f'CREATE POLICY tenant_scope ON "{name}"' in sql
    assert "REFERENCES persona_credit_profiles (workspace_id, version_id, id)" in sql
    assert "REFERENCES persona_workspace_members (workspace_id, actor_ref)" in sql
    assert "UNIQUE (workspace_id, profile_id, credit_index)" in sql
    assert "octet_length(content::text) <= 12000" in sql
    output.seek(0)
    output.truncate()
    command.downgrade(config, "0017credits:0016passports", sql=True)
    sql = output.getvalue()
    assert sql.index("all-tenant migration role") < sql.index("LOCK TABLE")
    assert sql.index("refuses populated history") < sql.index(" ".join(("DROP", "TABLE")))
