"""Concurrent requests against actual PostgreSQL row locks."""

import asyncio
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from accord.command.models import Event
from accord.personas.models import Version
from accord.personas.repository import ConflictError
from accord.personas.service import SaveCommand, save
from personas.conftest import command


async def write(engine: AsyncEngine, workspace: UUID, intent: SaveCommand) -> object:
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        try:
            return await save(session, workspace, "creator-a", intent)
        except ConflictError as exc:
            return exc


async def test_concurrent_exact_retry_commits_once(
    db_engine: AsyncEngine,
    session: AsyncSession,
    workspace: UUID,
) -> None:
    intent = command()
    results = await asyncio.wait_for(
        asyncio.gather(
            write(db_engine, workspace, intent),
            write(db_engine, workspace, intent),
        ),
        timeout=10,
    )
    assert results[0] == results[1]
    assert await session.scalar(select(func.count()).select_from(Version)) == 1
    assert await session.scalar(select(func.count()).select_from(Event)) == 1


async def test_concurrent_edits_have_one_winner(
    db_engine: AsyncEngine,
    session: AsyncSession,
    workspace: UUID,
) -> None:
    first = await save(session, workspace, "creator-a", command())
    results = await asyncio.wait_for(
        asyncio.gather(
            write(
                db_engine,
                workspace,
                command("Edit A", persona_id=first.persona_id, expected_revision=1),
            ),
            write(
                db_engine,
                workspace,
                command("Edit B", persona_id=first.persona_id, expected_revision=1),
            ),
        ),
        timeout=10,
    )
    assert sum(isinstance(result, ConflictError) for result in results) == 1
    revisions = list(await session.scalars(select(Version.revision).order_by(Version.revision)))
    assert revisions == [1, 2]
    assert (
        await session.scalar(
            select(func.count())
            .select_from(Event)
            .where(
                Event.action == "persona.version_saved",
            )
        )
        == 2
    )
    assert (
        await session.scalar(
            select(func.count())
            .select_from(Event)
            .where(
                Event.action == "persona.write_conflict",
            )
        )
        == 1
    )
