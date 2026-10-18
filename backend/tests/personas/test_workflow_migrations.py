"""Frozen review/campaign migrations must enforce more than metadata parity."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Connection, Table, func, select, text
from sqlalchemy.exc import DBAPIError
from test_migrations import _inspect
from test_migrations import empty_database as empty_database
from test_migrations import migrated_database as migrated_database

from accord.personas.campaign_policy import CAMPAIGN_TABLES
from accord.personas.review_policy import REVIEW_TABLES
from personas.review_migration_fixtures import seed_review

WORKFLOW_TABLES: tuple[Table, ...] = (*REVIEW_TABLES, *CAMPAIGN_TABLES)


def seed_offer(
    connection: Connection, workspace: UUID, version: UUID, review: UUID
) -> tuple[UUID, UUID]:
    asset, offer = uuid4(), uuid4()
    now = datetime.now(UTC)
    connection.execute(
        CAMPAIGN_TABLES[0]
        .insert()
        .values(
            id=asset,
            workspace_id=workspace,
            version_id=version,
            digest="b" * 64,
            label="Fictional original portrait",
        )
    )
    connection.execute(
        CAMPAIGN_TABLES[1]
        .insert()
        .values(
            id=offer,
            workspace_id=workspace,
            version_id=version,
            review_id=review,
            owner_ref="fixture-creator",
            recipient_ref="fixture-recipient",
            request_id=uuid4(),
            fingerprint="c" * 64,
            name="Fictional campaign",
            purpose="Fictional editorial use",
            conditions="No sublicensing",
            starts_at=now,
            ends_at=now + timedelta(days=30),
            recorded_at=now,
            event_id=uuid4().hex,
        )
    )
    return asset, offer


def seed_workflow(connection: Connection) -> UUID:
    workspace, version, review = seed_review(connection)
    asset, offer = seed_offer(connection, workspace, version, review)
    connection.execute(
        CAMPAIGN_TABLES[2]
        .insert()
        .values(
            workspace_id=workspace,
            campaign_id=offer,
            version_id=version,
            asset_id=asset,
        )
    )
    connection.execute(
        CAMPAIGN_TABLES[3]
        .insert()
        .values(
            id=uuid4(),
            workspace_id=workspace,
            campaign_id=offer,
            ordinal=1,
            actor_ref="fixture-recipient",
            request_id=uuid4(),
            fingerprint="d" * 64,
            decision="accepted",
            statement="Fictional recipient acceptance",
            recorded_at=datetime.now(UTC),
            event_id=uuid4().hex,
        )
    )
    return workspace


@pytest.mark.parametrize("table_index", range(len(WORKFLOW_TABLES)))
@pytest.mark.parametrize("operation", ["update", "delete"])
def test_migrated_workflow_records_are_immutable(
    migrated_database: str, table_index: int, operation: str
) -> None:
    def mutate(connection: Connection) -> None:
        workspace = seed_workflow(connection)
        table = WORKFLOW_TABLES[table_index]
        connection.execute(
            table.delete()
            if operation == "delete"
            else table.update().values(workspace_id=workspace)
        )

    with pytest.raises(DBAPIError, match="immutable"):
        _inspect(migrated_database, mutate)


def test_migrated_workflow_rls_scopes_every_populated_table(migrated_database: str) -> None:
    def read(connection: Connection) -> tuple[list[int], list[int], list[int]]:
        workspace = seed_workflow(connection)
        connection.execute(text("SET LOCAL ROLE pg_read_all_data"))

        def counts() -> list[int]:
            return [
                int(connection.scalar(select(func.count()).select_from(table)) or 0)
                for table in WORKFLOW_TABLES
            ]

        missing = counts()
        connection.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(uuid4())}
        )
        other = counts()
        connection.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(workspace)}
        )
        return missing, other, counts()

    assert _inspect(migrated_database, read) == ([0] * 5, [0] * 5, [1] * 5)


@pytest.mark.parametrize("table_index", range(len(WORKFLOW_TABLES)))
@pytest.mark.parametrize("with_scope", [False, True], ids=["missing-context", "other-workspace"])
def test_migrated_workflow_rls_rejects_insert(
    migrated_database: str, table_index: int, with_scope: bool
) -> None:
    def insert(connection: Connection) -> None:
        seed_workflow(connection)
        table = WORKFLOW_TABLES[table_index]
        values: dict[str, Any] = dict(connection.execute(select(table)).mappings().one())
        connection.execute(text("SET LOCAL ROLE pg_write_all_data"))
        if with_scope:
            connection.execute(
                text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(uuid4())}
            )
        connection.execute(table.insert().values(**values))

    with pytest.raises(DBAPIError, match="row-level security"):
        _inspect(migrated_database, insert)
