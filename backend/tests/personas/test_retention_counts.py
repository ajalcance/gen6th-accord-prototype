"""Retention counts remain exact when a persona commits during the purge."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Executable, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from accord.command.consumer import purge_expired
from accord.command.models import Event
from accord.personas.service import save
from personas.conftest import command


async def test_purge_counts_only_its_deletions(
    session: AsyncSession,
    db_engine: AsyncEngine,
    workspace: UUID,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session.add_all(
        [
            Event(
                event_id=uuid4().hex,
                ts=datetime.now(UTC) - timedelta(days=366),
                actor_type="system",
                tenant_id=workspace,
                category="client",
                action="client.error",
                outcome="failure",
                severity="info",
                source="client",
            )
            for _ in range(2)
        ]
    )
    await session.commit()
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    original = session.scalar
    first_count = True

    async def count_then_commit(statement: Executable, **kwargs: Any) -> Any:
        nonlocal first_count
        count = await original(statement, **kwargs)
        if first_count:
            first_count = False
            async with maker() as concurrent:
                await save(concurrent, workspace, "creator-a", command())
        return count

    monkeypatch.setattr(session, "scalar", count_then_commit)
    assert await purge_expired(session) == 2
    assert await session.scalar(select(func.count()).select_from(Event)) == 1
