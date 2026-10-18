"""Shared test fixtures."""

from __future__ import annotations

import asyncio
import json
import secrets
from collections.abc import AsyncGenerator, Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import postgres_server
import pytest
import pytest_asyncio
from fakeredis.aioredis import FakeRedis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from accord.cache.redis import get_redis
from accord.db import models  # noqa: F401  (registers tables on Base.metadata)
from accord.db.base import Base
from accord.db.connection import get_db
from accord.main import create_app
from accord.personas.session_boundary import PersonaSession


@pytest.fixture(scope="session")
def postgres_server_url() -> Iterator[str]:
    """One PostgreSQL server for the whole session (see tests/postgres_server.py)."""
    with postgres_server.server_url() as url:
        yield url


async def _build_template(server: str, name: str) -> None:
    await postgres_server.create_database(server, name)
    engine = create_async_engine(postgres_server.database_url(server, name), poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def schema_template(postgres_server_url: str) -> Iterator[str]:
    """A database holding the models' schema, cloned per test — built once, not per test.

    `create_all`, not the migrations: tests/test_migrations.py proves the two agree, on this
    same engine, so building from the models here costs nothing in fidelity.
    """
    name = postgres_server.unique_name(postgres_server.TEMPLATE_PREFIX)
    asyncio.run(_build_template(postgres_server_url, name))
    yield name
    asyncio.run(postgres_server.drop_database(postgres_server_url, name))


@pytest_asyncio.fixture
async def db_engine(
    postgres_server_url: str, schema_template: str
) -> AsyncGenerator[AsyncEngine, None]:
    """A fresh PostgreSQL database per test, with every table, dropped afterwards."""
    name = postgres_server.unique_name()
    await postgres_server.create_database(postgres_server_url, name, template=schema_template)
    engine = create_async_engine(
        postgres_server.database_url(postgres_server_url, name), poolclass=NullPool
    )
    try:
        yield engine
    finally:
        await engine.dispose()
        await postgres_server.drop_database(postgres_server_url, name)


@pytest_asyncio.fixture
async def session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """A session bound to the shared engine, for seeding/asserting."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as db_session:
        yield db_session


@pytest_asyncio.fixture
async def fake_redis() -> AsyncGenerator[FakeRedis, None]:
    """A fresh in-memory Redis per test."""
    redis = FakeRedis(decode_responses=True)
    yield redis
    await redis.aclose()


async def stream_events(redis: FakeRedis) -> list[dict[str, Any]]:
    """Every envelope currently on the telemetry stream, oldest first.

    The one place the telemetry wire format (stream setting, the 'e' field, JSON payload) is
    encoded in the test suite — a change to the emitter's encoding is fixed here, once.
    """
    from accord.config import get_settings

    entries = await redis.xrange(get_settings().telemetry_stream) or []
    return [json.loads(fields["e"]) for _, fields in entries if fields]


_TEST_SESSIONS: dict[str, tuple[str, str]] = {}


class TestSessionProvider:
    """Explicit test-only authorization; never imported by the application."""

    async def verify(self, request: Any) -> PersonaSession | None:
        value = _TEST_SESSIONS.get(request.headers.get("authorization", ""))
        if value is None:
            return None
        now = datetime.now(UTC)
        return PersonaSession(
            actor_ref=value[0],
            session_id=value[1],
            kind="human",
            issued_at=now - timedelta(seconds=1),
            expires_at=now + timedelta(minutes=5),
        )


def auth_headers(sub: str = "user-123", sid: str = "sess-9") -> dict[str, str]:
    """Opaque handles accepted only by the explicitly injected test provider."""
    header = f"Bearer {secrets.token_urlsafe(24)}"
    _TEST_SESSIONS[header] = (sub, sid)
    return {"Authorization": header}


@pytest_asyncio.fixture
async def client(
    db_engine: AsyncEngine,
    fake_redis: FakeRedis,
) -> AsyncGenerator[AsyncClient, None]:
    """An HTTP client wired to the app, with the DB (and Redis) dependencies overridden."""
    app = create_app()
    app.state.session_verifier = TestSessionProvider()
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with maker() as db_session:
            yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_redis] = lambda: fake_redis
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
