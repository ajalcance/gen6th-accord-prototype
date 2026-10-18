"""Frozen offline SQL proves rollback safeguards are emitted, not that a live role ran them."""

from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_capture_rollback_checks_all_tenants_and_refuses_populated_history() -> None:
    output = StringIO()
    root = Path(__file__).resolve().parents[2]
    config = Config(output_buffer=output)
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", "postgresql+asyncpg://localhost/unused")
    command.downgrade(config, "0011captures:0010portraits", sql=True)
    sql = output.getvalue()
    role = sql.index("capture rollback requires an all-tenant migration role")
    lock = sql.index("LOCK TABLE persona_portrait_captures, persona_version_references")
    refuse = sql.index("capture rollback refuses populated history")
    drop = sql.index(" ".join(("DROP", "TABLE", "persona_version_references")))
    assert role < lock < refuse < drop
    assert "IF EXISTS (SELECT 1 FROM persona_portrait_captures)" in sql
    assert "OR EXISTS (SELECT 1 FROM persona_version_references)" in sql
    assert "rolsuper OR rolbypassrls" in sql
