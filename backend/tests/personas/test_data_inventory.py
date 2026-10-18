"""Owner inventory proves all-tenant emptiness, without rewriting any history."""

from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from accord.db.base import Base

ROOT = Path(__file__).resolve().parents[3]
SOURCE = (ROOT / "deploy" / "accord-data-inventory.sql").read_text()
INVENTORY = SOURCE[SOURCE.index("DO $inventory$") : SOURCE.index("ROLLBACK;")]


@pytest.mark.asyncio
async def test_inventory_explicitly_handles_uninitialized_database(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    async with db_engine.connect() as connection:
        await connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        await connection.execute(text(INVENTORY))


@pytest.mark.asyncio
async def test_empty_inventory_requires_read_only_transaction(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as connection:
        await connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        await connection.execute(text(INVENTORY))
        with pytest.raises(DBAPIError, match="read-only transaction"):
            await connection.execute(text("CREATE TABLE inventory_write_probe (id integer)"))


@pytest.mark.asyncio
async def test_inventory_refuses_writable_transaction(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as connection:
        with pytest.raises(DBAPIError, match="requires a read-only transaction"):
            await connection.execute(text(INVENTORY))


@pytest.mark.asyncio
@pytest.mark.parametrize("materialized", [False, True])
async def test_inventory_sees_other_schema_rows_and_preserves_them(
    db_engine: AsyncEngine, materialized: bool
) -> None:
    async with db_engine.begin() as connection:
        await connection.execute(text("CREATE SCHEMA pglegacy_inventory"))
        if materialized:
            await connection.execute(
                text(
                    "CREATE MATERIALIZED VIEW pglegacy_inventory.records AS SELECT true AS fixture"
                )
            )
        else:
            await connection.execute(
                text("CREATE TABLE pglegacy_inventory.records (fixture boolean)")
            )
            await connection.execute(text("INSERT INTO pglegacy_inventory.records VALUES (true)"))
    async with db_engine.connect() as connection:
        await connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        with pytest.raises(DBAPIError, match="populated store requires provenance review"):
            await connection.execute(text(INVENTORY))
    async with db_engine.connect() as connection:
        count = await connection.scalar(text("SELECT count(*) FROM pglegacy_inventory.records"))
        assert count == 1


@pytest.mark.asyncio
async def test_inventory_refuses_external_sources_without_reading_them(
    db_engine: AsyncEngine,
) -> None:
    async with db_engine.begin() as connection:
        await connection.execute(text("CREATE FOREIGN DATA WRAPPER inventory_source NO HANDLER"))
        await connection.execute(
            text("CREATE SERVER inventory_source FOREIGN DATA WRAPPER inventory_source")
        )
        await connection.execute(
            text("CREATE FOREIGN TABLE external_records (fixture boolean) SERVER inventory_source")
        )
    async with db_engine.connect() as connection:
        await connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        with pytest.raises(DBAPIError, match="requires provenance review; no remote rows read"):
            await connection.execute(text(INVENTORY))


@pytest.mark.asyncio
async def test_inventory_cannot_certify_emptiness_through_rls(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as connection:
        await connection.execute(text("CREATE ROLE inventory_reader NOSUPERUSER NOBYPASSRLS"))
    try:
        async with db_engine.connect() as connection:
            await connection.execute(
                text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            )
            await connection.execute(text("SET LOCAL ROLE inventory_reader"))
            with pytest.raises(DBAPIError, match="requires an all-tenant operator"):
                await connection.execute(text(INVENTORY))
    finally:
        async with db_engine.begin() as connection:
            await connection.execute(text("DROP ROLE inventory_reader"))
