"""Frozen SQL rendering and model parity; actual PostgreSQL acceptance remains separate."""

from collections.abc import Callable
from io import StringIO
from pathlib import Path
from typing import cast

from alembic import command
from alembic.config import Config
from sqlalchemy import Table
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.schema import CreateTable

from accord.personas.lifecycle_models import LifecycleRecord


def test_lifecycle_scope_immutability_and_populated_rollback_are_frozen() -> None:
    output = StringIO()
    config = Config(output_buffer=output)
    config.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[2] / "migrations")
    )
    config.set_main_option("sqlalchemy.url", "postgresql+asyncpg://localhost/unused")
    command.upgrade(config, "0017credits:0018lifecycle", sql=True)
    sql = " ".join(output.getvalue().split())
    model = " ".join(
        str(
            CreateTable(cast(Table, LifecycleRecord.__table__)).compile(
                dialect=cast(Callable[[], Dialect], PGDialect)()
            )
        ).split()
    )
    for clause in (
        "persona_lifecycle_records",
        "workspace_id, persona_id, version_id",
        "workspace_id, persona_id, target_id",
        "workspace_id, actor_ref, request_id",
        "octet_length(content::text) <= 16000",
        "requirement IS NOT NULL",
    ):
        assert clause in sql and clause in model
    assert "FORCE ROW LEVEL SECURITY" in sql and "BEFORE UPDATE OR DELETE" in sql
    output.seek(0)
    output.truncate()
    command.downgrade(config, "0018lifecycle:0017credits", sql=True)
    sql = output.getvalue()
    assert sql.index("all-tenant migration role") < sql.index("LOCK TABLE")
    assert sql.index("refuses populated history") < sql.index(" ".join(("DROP", "TABLE")))
