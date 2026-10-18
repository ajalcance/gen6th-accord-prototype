"""Redis outage cannot prevent sealing transactionally committed persona events."""

from uuid import UUID

import pytest
from fakeredis.aioredis import FakeRedis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command import worker
from accord.command.audit import verify_chain
from accord.personas.service import save
from personas.conftest import command


async def test_durable_persona_seals_during_redis_outage(
    session: AsyncSession, workspace: UUID, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    await save(session, workspace, "creator-a", command())

    async def unavailable(_redis: Redis, _session: AsyncSession) -> int:
        raise ConnectionError("fixture outage")

    monkeypatch.setattr(worker, "consume_once", unavailable)
    assert await worker.process_once(fake_redis, session) == (0, 1, 0)
    assert await verify_chain(session) == (True, None, 1)
