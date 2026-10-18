"""Cold event expiry must preserve unsealed evidence and immutable versions."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.audit import seal_new, verify_chain
from accord.command.consumer import purge_expired
from accord.command.detection import evaluate_once
from accord.command.models import Event
from accord.personas.models import Version
from accord.personas.service import load, save
from personas.conftest import command


async def test_pending_event_survives_retention_then_sealed_event_expires(
    session: AsyncSession,
    workspace: UUID,
) -> None:
    intent = command()
    saved = await save(session, workspace, "creator-a", intent)
    async with session.begin():
        await session.execute(update(Event).values(ts=datetime.now(UTC) - timedelta(days=365)))
    assert await purge_expired(session) == 0
    assert await seal_new(session) == 1
    assert await purge_expired(session) == 0
    assert await evaluate_once(session) == 1
    assert await purge_expired(session) == 1
    assert await session.scalar(select(func.count()).select_from(Version)) == 1
    await session.rollback()
    assert await save(session, workspace, "creator-a", intent) == saved
    assert await load(session, workspace, "viewer", saved.persona_id) == saved
    assert await verify_chain(session) == (True, None, 1)
