"""Disposable confined SQL and in-memory Redis: real stage commits, cancellation, cleanup."""

import asyncio
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from fakeredis.aioredis import FakeRedis
from redis.exceptions import RedisError
from redis_fixtures import service_ca
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from accord.command import compliance_app, worker
from accord.command.audit import verify_chain
from accord.command.models import Event
from accord.config import DatabaseTransport, Environment, Settings
from accord.personas import runtime_role
from accord.telemetry.emitter import emit
from accord.telemetry.envelope import make_event
from sql_roles.test_runtime_journeys import workload_session


def confined_engine(url: str, role: str, disposed: asyncio.Event) -> AsyncEngine:
    engine = create_async_engine(url, poolclass=NullPool)

    @event.listens_for(engine.sync_engine, "connect")
    def assume(connection: Any, record: Any) -> None:
        previous = connection.autocommit
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(f'SET SESSION AUTHORIZATION "{role}"')
        cursor.close()
        connection.autocommit = previous

    @event.listens_for(engine.sync_engine, "engine_disposed")
    def closed(engine: Any) -> None:
        disposed.set()

    return engine


async def await_stage(task: asyncio.Task[tuple[int, int, int]], entered: asyncio.Event) -> None:
    waiter = asyncio.create_task(entered.wait())
    try:
        done, _ = await asyncio.wait({task, waiter}, timeout=5, return_when=asyncio.FIRST_COMPLETED)
        if task in done:
            await task  # Preserve the full underlying SQL failure before cancellation assertions.
        if not entered.is_set():
            raise TimeoutError("synthetic SQL stage was not reached")
    finally:
        waiter.cancel()
        await asyncio.gather(waiter, return_exceptions=True)


async def test_cancelled_pass_rolls_back_active_sql_but_preserves_ingestion_commit(
    role_db: Any, role_database_url: str, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    envelope = make_event(category="persona", action="persona.version_read", outcome="success")
    await emit(fake_redis, envelope)
    pending = uuid4().hex
    entered, disposed = asyncio.Event(), asyncio.Event()
    engine = confined_engine(role_database_url, role_db.roles["compliance"], disposed)
    monkeypatch.setattr(worker, "get_redis", lambda: fake_redis)
    monkeypatch.setattr(worker, "create_runtime_engine", lambda _: engine)

    async def block_sealing(session: AsyncSession) -> int:
        session.add(
            Event(
                event_id=pending,
                ts=datetime.now(UTC),
                actor_type="system",
                category="persona",
                action="persona.version_read",
                outcome="success",
                severity="info",
            )
        )
        await session.flush()
        entered.set()
        await asyncio.Event().wait()
        return 0

    monkeypatch.setattr(worker, "seal_new", block_sealing)
    task = asyncio.create_task(worker.run_once())
    try:
        await await_stage(task, entered)
    finally:
        if not task.done():
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, 5)
    assert disposed.is_set()
    async with workload_session(role_database_url, role_db.roles["compliance"]) as session:
        assert await session.scalar(select(Event.event_id).where(Event.event_id == pending)) is None
        assert (
            await session.scalar(
                select(Event.event_id).where(Event.event_id == envelope["event_id"])
            )
            == envelope["event_id"]
        )
    from accord.config import get_settings

    assert await fake_redis.get(get_settings().telemetry_stream + ":cursor") is not None


async def test_factory_progress_during_redis_outage_preserves_audit_detection_retention(
    role_db: Any,
    role_database_url: str,
    fake_redis: FakeRedis,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await seed_expired(role_database_url, role_db.roles["api"])
    settings = configured(tmp_path)
    monkeypatch.setattr("accord.command.compliance_config.sys.platform", "linux")
    monkeypatch.setenv("CLOUD_RUN_WORKER_POOL", "synthetic-compliance")
    monkeypatch.setattr(compliance_app, "get_settings", lambda: settings)
    monkeypatch.setattr(compliance_app, "get_redis", lambda: fake_redis)
    monkeypatch.setattr(worker, "get_redis", lambda: fake_redis)
    monkeypatch.setattr(fake_redis, "get", AsyncMock(side_effect=RedisError("synthetic offline")))
    disposed = asyncio.Event()
    monkeypatch.setattr(
        worker,
        "create_runtime_engine",
        lambda _: confined_engine(role_database_url, role_db.roles["compliance"], disposed),
    )

    def maker() -> AbstractAsyncContextManager[AsyncSession]:
        return workload_session(role_database_url, role_db.roles["compliance"])

    monkeypatch.setattr(runtime_role, "_get_sessionmaker", lambda: maker)
    monkeypatch.setattr("accord.command.compliance_app.connection._engine", None)
    app = compliance_app.create_compliance_app()
    async with app.router.lifespan_context(app):
        await assert_progress(app)
        async with workload_session(role_database_url, role_db.roles["compliance"]) as session:
            valid, broken, count = await verify_chain(session)
            assert valid and broken is None and count == 1
            assert (
                await session.scalar(
                    select(Event.event_id).where(Event.action == "persona.version_saved")
                )
                is None
            )
    assert disposed.is_set() and app.state.compliance.health() == "stopping"


async def seed_expired(url: str, role: str) -> None:
    workspace = uuid4()
    async with workload_session(url, role) as api:
        api.add(
            Event(
                event_id=uuid4().hex,
                ts=datetime.now(UTC) - timedelta(days=366),
                actor_type="system",
                tenant_id=workspace,
                category="persona",
                action="persona.version_saved",
                outcome="success",
                severity="info",
                source="server",
                metadata_={},
            )
        )
        await api.commit()


def configured(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        environment=Environment.PRODUCTION,
        secret_key="synthetic-worker-settings",
        database_transport=DatabaseTransport.CLOUD_SQL_PROXY,
        database_url="postgresql+asyncpg://accord_compliance:synthetic@127.0.0.1:5432/appdb",
        redis_url="rediss://synthetic-redis:6378/0",
        redis_ca_cert_path=str(service_ca(tmp_path)),
    )


async def assert_progress(app: Any) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200 and response.json()["scope"] == "worker_pass_progress"
