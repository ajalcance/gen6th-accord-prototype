"""The PostgreSQL server the backend test suite runs against (TA-015, ADR-0016).

One server per test session, and a fresh database per test cloned from a template that holds
the schema, so no test can see another's rows and ordering never matters (TA-014).

Where the server comes from, in order:

1. ``ACCORD_TEST_DATABASE_URL``, if set: an existing server the caller owns (an asyncpg URL to
   a database the user may ``CREATE DATABASE`` from). Useful where Docker is unreachable, such
   as inside the agent's sandbox. The databases created here are dropped again.
2. Otherwise a throwaway container of the image pinned in ``tests/postgres/Dockerfile``.

There is no third option. If neither works the suite FAILS: a database test that skipped
because no database was available is a green tick that checked nothing.

Testcontainers' Ryuk reaper is turned off. It would pull ``testcontainers/ryuk`` by a movable
tag and hand it the Docker socket — a privileged image nobody pinned. Cleanup is the context
manager's job instead; a crashed run can leave a container behind, which is the cheaper failure.
"""

from __future__ import annotations

import os
import re
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

DOCKERFILE = Path(__file__).resolve().parent / "postgres" / "Dockerfile"
URL_ENV = "ACCORD_TEST_DATABASE_URL"
TEMPLATE_PREFIX = "accord_template_"


def pinned_image() -> str:
    """The image named by the FROM line, refused unless it is pinned by digest."""
    match = re.search(r"^FROM\s+(\S+)", DOCKERFILE.read_text(), re.M)
    if not match or "@sha256:" not in match.group(1):
        raise RuntimeError(f"{DOCKERFILE} must pin the test PostgreSQL image by digest")
    return match.group(1)


@contextmanager
def server_url() -> Iterator[str]:
    """An asyncpg URL to a server this session may create databases on."""
    given = os.environ.get(URL_ENV)
    if given:
        yield given
        return
    os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"
    from testcontainers.community.postgres import PostgresContainer

    with PostgresContainer(pinned_image(), driver="asyncpg") as container:
        yield container.get_connection_url()


def database_url(server: str, name: str) -> str:
    """The same server, a different database."""
    return make_url(server).set(database=name).render_as_string(hide_password=False)


def unique_name(prefix: str = "accord_test_") -> str:
    return prefix + uuid.uuid4().hex


async def create_database(server: str, name: str, template: str | None = None) -> None:
    await _admin(
        server, f'CREATE DATABASE "{name}"' + (f' TEMPLATE "{template}"' if template else "")
    )


async def drop_database(server: str, name: str) -> None:
    await _admin(server, f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


async def _admin(server: str, statement: str) -> None:
    """Run one statement outside a transaction: CREATE/DROP DATABASE cannot run inside one."""
    engine = create_async_engine(server, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            await connection.execute(text(statement))
    finally:
        await engine.dispose()
