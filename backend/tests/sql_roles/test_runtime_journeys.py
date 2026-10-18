"""Run real API/job and compliance services through the prepared effective privileges."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from fakeredis.aioredis import FakeRedis
from personas.test_job_database import setup_job
from personas.workflow_fixtures import human
from sqlalchemy import event, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from accord.command.audit import seal_new, verify_chain
from accord.command.consumer import purge_expired
from accord.command.detection import evaluate_once
from accord.command.models import Event
from accord.command.worker import process_once
from accord.personas import job_service, job_worker
from accord.personas.models import WorkspaceMember
from accord.personas.runtime_role import ROLE_QUERY
from accord.personas.task_google import TaskReference


@asynccontextmanager
async def workload_session(url: str, role: str) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(url, poolclass=NullPool)

    @event.listens_for(engine.sync_engine, "connect")
    def assume(connection: Any, record: Any) -> None:
        previous = connection.autocommit
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(f'SET SESSION AUTHORIZATION "{role}"')
        cursor.close()
        connection.autocommit = previous

    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            yield session
    finally:
        await engine.dispose()


async def seed_member(url: str) -> UUID:
    workspace = uuid4()
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with async_sessionmaker(engine)() as session:
            session.add(
                WorkspaceMember(workspace_id=workspace, actor_ref="creator-a", role="creator")
            )
            await session.commit()
    finally:
        await engine.dispose()
    return workspace


async def test_api_enqueue_reference_completion_and_exact_replay(
    role_db: Any, role_database_url: str
) -> None:
    workspace = await seed_member(role_database_url)
    async with workload_session(role_database_url, role_db.roles["api"]) as api:
        intent, runtime = await setup_job(api, workspace)
        queued = await job_service.enqueue(api, workspace, human("creator-a"), intent, runtime)
        assert queued.state == "queued"
        assert isinstance(runtime.dispatcher, AsyncMock)
        runtime.dispatcher.dispatch.side_effect = None
    ref = TaskReference(workspace_id=workspace, job_id=queued.job_id, dispatch_id=queued.job_id)
    async with workload_session(role_database_url, role_db.roles["reference"]) as worker:
        assert await worker.scalar(text(ROLE_QUERY)) is False
        await worker.rollback()
        assert await job_worker.reconcile(worker, runtime, "synthetic-workload") == {
            "examined": 1,
            "dispatched": 1,
        }
        await job_worker.execute(worker, ref, runtime, "synthetic-workload")
        await job_worker.execute(worker, ref, runtime, "synthetic-workload")
    async with workload_session(role_database_url, role_db.roles["api"]) as api:
        result = await job_service.enqueue(api, workspace, human("creator-a"), intent, runtime)
        assert result.state == "succeeded" and result.attempts == 1


async def test_compliance_services_seal_evaluate_and_retain_until_ready(
    role_db: Any, role_database_url: str, fake_redis: FakeRedis
) -> None:
    workspace = uuid4()
    async with workload_session(role_database_url, role_db.roles["api"]) as api:
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
    async with workload_session(role_database_url, role_db.roles["compliance"]) as worker:
        assert await purge_expired(worker) == 0
        assert await seal_new(worker) == 1
        assert await purge_expired(worker) == 0
        assert await evaluate_once(worker) == 1
        assert await purge_expired(worker) == 1
        valid, broken, count = await verify_chain(worker)
        assert valid and broken is None and count == 1
        await worker.rollback()
        stored, sealed, purged = await process_once(fake_redis, worker)
        assert stored == 0 and sealed >= 1 and purged == 0
        assert await worker.scalar(select(Event.event_id).limit(1)) is not None
