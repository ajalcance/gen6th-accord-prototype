"""Actual PostgreSQL persistence, replay and rollback; never an in-memory DB."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.audit import seal_new, verify_chain
from accord.command.models import AuditLog, Event
from accord.personas.models import Persona, Version, WorkspaceMember, WriteReceipt
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import load, save
from personas.conftest import command


async def test_save_reload_and_seal(session: AsyncSession, workspace: UUID) -> None:
    intent = command()
    saved = await save(session, workspace, "creator-a", intent)
    assert saved.content == intent.content and saved.revision == 1
    assert saved.recorded_at.utcoffset() is not None
    loaded = await load(session, workspace, "viewer", saved.persona_id)
    assert loaded == saved
    events = (await session.scalars(select(Event).order_by(Event.ts))).all()
    assert {e.action for e in events} == {"persona.version_saved", "persona.version_read"}
    assert all(e.source == "server" and e.tenant_id == workspace for e in events)
    assert all(UUID(e.correlation_id) for e in events if e.correlation_id)
    assert all(e.correlation_id is not None for e in events)
    write = next(e for e in events if e.action == "persona.version_saved")
    assert write.actor_id == "creator-a" and write.correlation_id == str(intent.request_id)
    assert set(write.metadata_) == {"version_id", "revision"}
    await session.rollback()
    assert await seal_new(session) == 2
    assert await verify_chain(session) == (True, None, 2)
    assert all(row.compliance_tags for row in (await session.scalars(select(AuditLog))).all())


async def test_exact_retry_returns_same_receipt(session: AsyncSession, workspace: UUID) -> None:
    intent = command()
    first = await save(session, workspace, "creator-a", intent)
    second = await save(session, workspace, "creator-a", intent)
    assert first == second
    assert await session.scalar(select(func.count()).select_from(Version)) == 1
    assert await session.scalar(select(func.count()).select_from(Event)) == 1
    assert await session.scalar(select(func.count()).select_from(WriteReceipt)) == 1


async def test_changed_retry_is_rejected(session: AsyncSession, workspace: UUID) -> None:
    intent = command()
    await save(session, workspace, "creator-a", intent)
    with pytest.raises(ConflictError):
        await save(
            session, workspace, "creator-a", command("Different", request_id=intent.request_id)
        )
    assert await session.scalar(select(func.count()).select_from(Version)) == 1


async def test_new_version_preserves_history(session: AsyncSession, workspace: UUID) -> None:
    first = await save(session, workspace, "creator-a", command())
    second = await save(
        session,
        workspace,
        "creator-a",
        command(
            "Fictional revision two",
            persona_id=first.persona_id,
            expected_revision=1,
        ),
    )
    assert second.revision == 2 and second.version_id != first.version_id
    assert await load(session, workspace, "viewer", first.persona_id, revision=1) == first
    assert await load(session, workspace, "viewer", first.persona_id) == second
    with pytest.raises(ConflictError):
        await save(
            session,
            workspace,
            "creator-a",
            command(persona_id=first.persona_id, expected_revision=1),
        )


@pytest.mark.parametrize("actor", ["viewer", "absent-member", ""])
async def test_unauthorized_write_leaves_no_rows(
    session: AsyncSession,
    workspace: UUID,
    actor: str,
) -> None:
    with pytest.raises(AccessDeniedError):
        await save(session, workspace, actor, command())
    assert await session.scalar(select(func.count()).select_from(Persona)) == 0
    rejected = (await session.scalars(select(Event))).one()
    assert rejected.action == "persona.access_denied" and rejected.outcome == "denied"
    assert rejected.metadata_ == {}


async def test_cross_workspace_and_nonowner_denied(session: AsyncSession, workspace: UUID) -> None:
    first = await save(session, workspace, "creator-a", command())
    with pytest.raises(AccessDeniedError):
        await load(session, uuid4(), "creator-a", first.persona_id)
    with pytest.raises(AccessDeniedError):
        await save(
            session,
            workspace,
            "creator-b",
            command(persona_id=first.persona_id, expected_revision=1),
        )
    assert await load(session, workspace, "creator-a", first.persona_id) == first


async def test_invalid_create_rolls_back(session: AsyncSession, workspace: UUID) -> None:
    with pytest.raises(ValueError, match="revision zero"):
        await save(session, workspace, "creator-a", command(expected_revision=1))
    assert await session.scalar(select(func.count()).select_from(Persona)) == 0


async def test_role_change_denies_previously_allowed_replay(
    session: AsyncSession, workspace: UUID
) -> None:
    intent = command()
    first = await save(session, workspace, "creator-a", intent)
    await session.execute(
        update(WorkspaceMember)
        .where(WorkspaceMember.workspace_id == workspace, WorkspaceMember.actor_ref == "creator-a")
        .values(role="viewer")
    )
    await session.commit()
    with pytest.raises(AccessDeniedError):
        await save(session, workspace, "creator-a", intent)
    assert await load(session, workspace, "creator-a", first.persona_id) == first
