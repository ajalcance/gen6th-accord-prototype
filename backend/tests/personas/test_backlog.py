"""Backlog counts honor membership, workspace, source, audit presence and timing."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.audit import seal_new
from accord.command.models import Event
from accord.personas.health import observe_backlog
from accord.personas.repository import AccessDeniedError
from accord.personas.service import save
from personas.conftest import command


async def test_backlog_before_and_after_sealing(session: AsyncSession, workspace: UUID) -> None:
    version = await save(session, workspace, "creator-a", command())
    before = await observe_backlog(session, workspace, "viewer")
    assert before.pending_events == 1 and before.oldest_pending_at == version.recorded_at
    observation = await session.scalar(
        select(Event).where(Event.correlation_id == str(before.observation_request_id))
    )
    assert observation is not None and observation.action == "persona.workspace_observed"
    assert observation.metadata_ == {"pending_events": 1} and observation.actor_id == "viewer"
    await session.rollback()
    assert await seal_new(session) == 2
    after = await observe_backlog(session, workspace, "viewer")
    assert after.pending_events == 0 and after.oldest_pending_at is None


async def test_backlog_excludes_client_and_other_workspace(
    session: AsyncSession, workspace: UUID
) -> None:
    await save(session, workspace, "creator-a", command())
    event = await session.scalar(select(Event))
    assert event is not None
    event.source = "client"
    await session.commit()
    result = await observe_backlog(session, workspace, "viewer")
    assert result.pending_events == 0
    observation = await session.scalar(select(Event).where(Event.source == "server"))
    assert observation is not None
    observation.tenant_id = uuid4()
    await session.commit()
    result = await observe_backlog(session, workspace, "viewer")
    assert result.pending_events == 0


async def test_backlog_missing_membership_is_denied(session: AsyncSession, workspace: UUID) -> None:
    with pytest.raises(AccessDeniedError):
        await observe_backlog(session, workspace, "absent-member")
