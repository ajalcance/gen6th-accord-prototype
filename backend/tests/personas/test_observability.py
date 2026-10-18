"""Receipt observations before sealing, after sealing and after cold-store expiry."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.audit import seal_new, verify_chain
from accord.command.consumer import purge_expired
from accord.command.detection import evaluate_once
from accord.command.models import Event
from accord.personas.observability import inspect_evidence
from accord.personas.repository import AccessDeniedError
from accord.personas.service import save
from personas.conftest import command


async def test_observe_committed_and_audited_receipt(
    session: AsyncSession, workspace: UUID
) -> None:
    intent = command()
    version = await save(session, workspace, "creator-a", intent)
    pending = await inspect_evidence(session, workspace, "viewer", version.persona_id)
    assert pending.write_request_id == intent.request_id
    assert pending.version_id == version.version_id and pending.revision == version.revision
    assert pending.audit_state == "pending" and pending.cold_event_present
    assert pending.audit_sequence is None and pending.audit_entry_hash is None
    assert pending.observation_request_id != intent.request_id
    assert await seal_new(session) == 2
    recorded = await inspect_evidence(session, workspace, "viewer", version.persona_id)
    assert recorded.event_id == pending.event_id
    assert recorded.audit_state == "entry_present" and recorded.audit_sequence is not None
    assert recorded.audit_entry_hash is not None
    assert (await verify_chain(session))[0]


async def test_evidence_survives_cold_event_expiry(session: AsyncSession, workspace: UUID) -> None:
    version = await save(session, workspace, "creator-a", command())
    assert await seal_new(session) == 1
    event = await session.scalar(select(Event).where(Event.action == "persona.version_saved"))
    assert event is not None
    event.ts = datetime.now(UTC) - timedelta(days=366)
    await session.commit()
    assert await evaluate_once(session) == 1
    assert await purge_expired(session) == 1
    await session.rollback()
    evidence = await inspect_evidence(session, workspace, "viewer", version.persona_id)
    assert evidence.audit_state == "entry_present" and not evidence.cold_event_present


async def test_unavailable_evidence_fails_without_read_event(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await save(session, workspace, "creator-a", command())
    await session.execute(delete(Event))
    await session.commit()
    with pytest.raises(RuntimeError, match="unavailable"):
        await inspect_evidence(session, workspace, "viewer", version.persona_id)
    assert (await session.scalars(select(Event))).all() == []


async def test_evidence_denies_cross_workspace(session: AsyncSession, workspace: UUID) -> None:
    version = await save(session, workspace, "creator-a", command())
    with pytest.raises(AccessDeniedError):
        await inspect_evidence(session, uuid4(), "viewer", version.persona_id)


async def test_mismatched_server_event_fails(session: AsyncSession, workspace: UUID) -> None:
    version = await save(session, workspace, "creator-a", command())
    event = await session.scalar(select(Event).where(Event.action == "persona.version_saved"))
    assert event is not None
    event.source = "client"
    await session.commit()
    with pytest.raises(RuntimeError, match="committed server observation"):
        await inspect_evidence(session, workspace, "viewer", version.persona_id)
