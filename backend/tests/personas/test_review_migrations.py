"""Migration 0004's immutable review protection must execute on PostgreSQL."""

from uuid import uuid4

import pytest
from sqlalchemy import Connection, func, select, text
from sqlalchemy.exc import DBAPIError
from test_migrations import _inspect
from test_migrations import empty_database as empty_database
from test_migrations import migrated_database as migrated_database

from accord.personas.review_policy import REVIEW_TABLES
from personas.review_migration_fixtures import seed_review


@pytest.mark.parametrize("operation", ["update", "delete"])
def test_migrated_review_rejects_changes(migrated_database: str, operation: str) -> None:
    def mutate(connection: Connection) -> None:
        workspace, _version, _review = seed_review(connection)
        table = REVIEW_TABLES[0]
        connection.execute(
            table.delete()
            if operation == "delete"
            else table.update().values(workspace_id=workspace)
        )

    with pytest.raises(DBAPIError, match="immutable"):
        _inspect(migrated_database, mutate)


def test_migrated_review_scopes_populated_reads(migrated_database: str) -> None:
    def read(connection: Connection) -> tuple[int, int, int]:
        workspace, _version, _review = seed_review(connection)
        connection.execute(text("SET LOCAL ROLE pg_read_all_data"))

        def count() -> int:
            return int(connection.scalar(select(func.count()).select_from(REVIEW_TABLES[0])) or 0)

        missing = count()
        connection.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(uuid4())}
        )
        other = count()
        connection.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(workspace)}
        )
        return missing, other, count()

    assert _inspect(migrated_database, read) == (0, 0, 1)
