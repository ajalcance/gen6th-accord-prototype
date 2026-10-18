"""Exercise the prepared SQL on a migrated disposable database, with unique global roles."""

import asyncio
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import postgres_server
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

ROOT = Path(__file__).resolve().parents[3]


@dataclass
class RoleDatabase:
    connection: Any
    roles: dict[str, str]
    substitutions: dict[str, str]
    operator: str

    def script(self, filename: str) -> str:
        source = (ROOT / "deploy/google" / filename).read_text()
        for original, replacement in self.substitutions.items():
            source = source.replace(original, replacement)
        return source

    async def assume(self, workload: str, workspace: str | None = None) -> None:
        # Identifiers are generated here, never accepted from requests or environment values.
        await self.connection.execute(f'SET SESSION AUTHORIZATION "{self.roles[workload]}"')
        if workspace is not None:
            await self.connection.execute(
                "SELECT set_config('accord.workspace_id', $1, true)", workspace
            )


@pytest.fixture
def role_database_url(postgres_server_url: str) -> Iterator[str]:
    name = postgres_server.unique_name()
    asyncio.run(postgres_server.create_database(postgres_server_url, name))
    url = postgres_server.database_url(postgres_server_url, name)
    config = Config(str(ROOT / "backend/alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "backend/migrations"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    try:
        command.upgrade(config, "0018lifecycle")
        yield url
    finally:
        asyncio.run(postgres_server.drop_database(postgres_server_url, name))


@pytest_asyncio.fixture
async def prepared_roles(role_database_url: str) -> AsyncIterator[RoleDatabase]:
    engine = create_async_engine(role_database_url, poolclass=NullPool)
    roles = {name: f"test_{name}_{uuid4().hex}" for name in ("api", "reference", "compliance")}
    async with engine.connect() as connection:
        raw = await connection.get_raw_connection()
        driver = raw.driver_connection
        assert driver is not None
        operator = await driver.fetchval("SELECT current_user")
        database = await driver.fetchval("SELECT current_database()")
        substitutions = {f"accord_{name}": role for name, role in roles.items()}
        substitutions.update({"'accord_migrator'": f"'{operator}'", "'appdb'": f"'{database}'"})
        # appdb occurs once as an identifier, and once as a quoted precondition value.
        substitutions["DATABASE appdb"] = f'DATABASE "{database}"'
        fixture = RoleDatabase(driver, roles, substitutions, operator)
        try:
            await driver.execute(fixture.script("sql-runtime-roles.sql"))
            yield fixture
        finally:
            await driver.execute("ROLLBACK")
            for role in roles.values():
                await driver.execute(f'DROP OWNED BY "{role}"')
                await driver.execute(f'DROP ROLE "{role}"')
    await engine.dispose()


@pytest_asyncio.fixture
async def role_db(prepared_roles: RoleDatabase) -> AsyncIterator[RoleDatabase]:
    await prepared_roles.connection.execute(prepared_roles.script("sql-runtime-grants.sql"))
    await prepared_roles.connection.execute("BEGIN")
    try:
        yield prepared_roles
    finally:
        await prepared_roles.connection.execute("ROLLBACK")
