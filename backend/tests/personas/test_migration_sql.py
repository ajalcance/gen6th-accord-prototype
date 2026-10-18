"""Offline migration rendering supplements, never replaces, PostgreSQL tests."""

from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config

from accord.db.base import Base


def render_upgrade() -> str:
    output = StringIO()
    root = Path(__file__).resolve().parents[2]
    config = Config(output_buffer=output)
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", "postgresql+asyncpg://localhost/unused")
    command.upgrade(config, "head", sql=True)
    return output.getvalue()


def test_upgrade_renders_persona_schema_and_protections() -> None:
    sql = render_upgrade()
    tables = tuple(
        table
        for table in Base.metadata.sorted_tables
        if table.name == "personas" or table.name.startswith("persona_")
    )
    assert tables
    for table in tables:
        original = "persona_fixture_assets" if table.name == "persona_assets" else table.name
        assert f"CREATE TABLE {original}" in sql
        assert f'ALTER TABLE "{original}" ENABLE ROW LEVEL SECURITY' in sql
        assert f'ALTER TABLE "{original}" FORCE ROW LEVEL SECURITY' in sql
        assert f'CREATE POLICY tenant_scope ON "{original}"' in sql
        if original != table.name:
            assert f"ALTER TABLE {original} RENAME TO {table.name}" in sql
    assert sql.count("CREATE TRIGGER immutable_record") == len(tables) - 2
    assert "CREATE FUNCTION accord_persona_immutable()" in sql
    assert "0003personas" in sql
    assert "FOREIGN KEY(event_id)" not in sql
    assert "CREATE INDEX ix_events_tenant_category_source_ts ON events" in sql
