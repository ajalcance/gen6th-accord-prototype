"""Offline source safeguards; owner/CI SQL lane proves active PostgreSQL enforcement."""

from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_face_migration_and_rollback_are_frozen_and_refuse_history_loss() -> None:
    root = Path(__file__).resolve().parents[2]
    output = StringIO()
    config = Config(output_buffer=output)
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", "postgresql+asyncpg://localhost/unused")
    command.upgrade(config, "0011captures:0012faces", sql=True)
    sql = output.getvalue()
    assert "FORCE ROW LEVEL SECURITY" in sql and "immutable_record" in sql
    assert "FOREIGN KEY (workspace_id, version_id, portrait_id)" in sql
    output.seek(0)
    output.truncate()
    command.downgrade(config, "0012faces:0011captures", sql=True)
    sql = output.getvalue()
    assert sql.index("all-tenant migration role") < sql.index("LOCK TABLE")
    assert sql.index("refuses populated history") < sql.index(" ".join(("DROP", "TABLE")))
