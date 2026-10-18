"""Retention preserves supporting windows but never retains clients for detection."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.audit import seal_new
from accord.command.consumer import purge_expired
from accord.command.detection import evaluate_once
from accord.command.models import Event
from personas.test_detection import event


async def test_pending_window_preserves_support_only(
    session: AsyncSession, workspace: UUID
) -> None:
    when = datetime.now(UTC) - timedelta(days=365)
    support = event(workspace, ts=when - timedelta(seconds=1))
    client = event(workspace, ts=when, source="client", action="client.error")
    session.add_all([support, client])
    await session.commit()
    assert await evaluate_once(session) == 1
    pending = event(workspace, ts=when)
    session.add(pending)
    await session.commit()
    assert await seal_new(session) == 3
    assert await purge_expired(session) == 1
    assert set(
        await session.scalars(select(Event.event_id).where(Event.category == "persona"))
    ) == {
        support.event_id,
        pending.event_id,
    }
    await session.rollback()
    assert await evaluate_once(session) == 1
    assert await purge_expired(session) == 2
