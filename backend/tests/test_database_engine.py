"""The suite runs on the database production runs on, or it does not pass (TA-015).

A fixture change that quietly swapped PostgreSQL for something lighter would leave every other
test green while proving nothing about row-level security, locking or migrations. This names
that failure instead of letting it hide.
"""

from __future__ import annotations

import re

import postgres_server
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def test_the_suite_runs_on_the_pinned_postgresql_major(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as connection:
        version = (await connection.execute(text("SHOW server_version"))).scalar_one()
    image = postgres_server.pinned_image()
    pinned_major = re.search(r":(\d+)", image)
    assert pinned_major, f"cannot read a major version from {image}"
    assert str(version).split(".")[0] == pinned_major.group(
        1
    ), f"tests ran on PostgreSQL {version}, but tests/postgres/Dockerfile pins {image}"


async def test_each_test_gets_its_own_database(db_engine: AsyncEngine) -> None:
    """Isolation (TA-014): a per-test database, never the shared template or the admin one."""
    async with db_engine.connect() as connection:
        name = (await connection.execute(text("SELECT current_database()"))).scalar_one()
    assert str(name).startswith("accord_test_"), f"a test ran in shared database {name!r}"
