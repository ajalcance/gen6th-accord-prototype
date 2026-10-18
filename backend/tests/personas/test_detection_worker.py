"""Worker integration uses durable PostgreSQL despite a failed Redis ingestion leg."""

from typing import cast
from uuid import UUID

import pytest
from redis.asyncio import Redis
from redis.exceptions import ConnectionError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command import worker
from accord.command.detection_models import DetectionReceipt
from accord.command.models import AuditLog
from personas.test_detection import event


async def test_worker_evaluates_durable_events_during_redis_outage(
    session: AsyncSession, workspace: UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = event(workspace, severity="critical")
    session.add(source)
    await session.commit()

    async def offline(_redis: Redis, _session: AsyncSession) -> int:
        raise ConnectionError("fixture outage")

    monkeypatch.setattr(worker, "consume_once", offline)
    assert await worker.process_once(cast(Redis, object()), session) == (0, 1, 0)
    receipt = await session.get(DetectionReceipt, source.event_id)
    assert receipt is not None and receipt.findings[0]["rule_id"] == "critical-catchall"
    assert await session.scalar(select(AuditLog.event_id)) == source.event_id
    await session.rollback()
    assert await worker.process_once(cast(Redis, object()), session) == (0, 1, 0)
