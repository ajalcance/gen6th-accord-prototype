"""Transaction faults must not leave partial content or evidence."""

from uuid import UUID

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from accord.command.models import Event
from accord.personas.models import Persona, Version, WriteReceipt
from accord.personas.service import load, save
from personas.conftest import command


def fail_receipt(session: Session, _context: object, _instances: object) -> None:
    if any(isinstance(row, WriteReceipt) for row in session.new):
        raise RuntimeError("injected receipt storage failure")


def fail_rejection(session: Session, _context: object, _instances: object) -> None:
    if any(isinstance(row, Event) for row in session.new):
        raise RuntimeError("fixture-private-detail")


async def test_late_failure_rolls_back_creation(session: AsyncSession, workspace: UUID) -> None:
    event.listen(session.sync_session, "before_flush", fail_receipt)
    try:
        with pytest.raises(RuntimeError, match="receipt storage"):
            await save(session, workspace, "creator-a", command())
    finally:
        event.remove(session.sync_session, "before_flush", fail_receipt)
    for model in (Persona, Version, Event, WriteReceipt):
        assert await session.scalar(select(func.count()).select_from(model)) == 0


async def test_late_failure_preserves_previous_head(session: AsyncSession, workspace: UUID) -> None:
    first = await save(session, workspace, "creator-a", command())
    event.listen(session.sync_session, "before_flush", fail_receipt)
    try:
        with pytest.raises(RuntimeError):
            await save(
                session,
                workspace,
                "creator-a",
                command(
                    "Failed edit",
                    persona_id=first.persona_id,
                    expected_revision=1,
                ),
            )
    finally:
        event.remove(session.sync_session, "before_flush", fail_receipt)
    assert await load(session, workspace, "creator-a", first.persona_id) == first
    assert await session.scalar(select(func.count()).select_from(Version)) == 1


async def test_failed_rejection_is_bounded_operational_failure(
    session: AsyncSession, workspace: UUID, caplog: pytest.LogCaptureFixture
) -> None:
    intent = command()
    event.listen(session.sync_session, "before_flush", fail_rejection)
    try:
        with pytest.raises(RuntimeError):
            await save(session, workspace, "viewer", intent)
    finally:
        event.remove(session.sync_session, "before_flush", fail_rejection)
    assert f"persona rejection recording failed (request_id={intent.request_id})" in caplog.messages
    assert all("fixture-private-detail" not in message for message in caplog.messages)
    assert await session.scalar(select(func.count()).select_from(Event)) == 0
    assert await session.scalar(select(func.count()).select_from(Persona)) == 0
