"""Review race, rollback and database immutability tests on PostgreSQL."""

import asyncio
from uuid import UUID

import pytest
from sqlalchemy import delete, event, func, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session

from accord.command.models import Event
from accord.personas.repository import ConflictError
from accord.personas.review_models import ReviewRecord
from accord.personas.reviews import record_review
from accord.personas.workflow_contracts import ReviewCommand
from personas.workflow_fixtures import draft_for_review, human, review_intent


async def concurrent_review(
    engine: AsyncEngine, workspace: UUID, actor_ref: str, intent: ReviewCommand
) -> object:
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        try:
            return await record_review(session, workspace, human(actor_ref), intent)
        except ConflictError as exc:
            return exc


async def test_concurrent_reviews_use_compare_and_swap(
    db_engine: AsyncEngine, session: AsyncSession, workspace: UUID
) -> None:
    version = await draft_for_review(session, workspace)
    results = await asyncio.wait_for(
        asyncio.gather(
            concurrent_review(
                db_engine, workspace, "reviewer-a", review_intent(version.version_id)
            ),
            concurrent_review(
                db_engine, workspace, "reviewer-b", review_intent(version.version_id)
            ),
        ),
        timeout=10,
    )
    assert sum(isinstance(row, ConflictError) for row in results) == 1
    assert await session.scalar(select(func.count()).select_from(ReviewRecord)) == 1


async def test_concurrent_exact_review_retry_is_one_decision(
    db_engine: AsyncEngine, session: AsyncSession, workspace: UUID
) -> None:
    version = await draft_for_review(session, workspace)
    intent = review_intent(version.version_id)
    results = await asyncio.wait_for(
        asyncio.gather(
            concurrent_review(db_engine, workspace, "reviewer-a", intent),
            concurrent_review(db_engine, workspace, "reviewer-a", intent),
        ),
        timeout=10,
    )
    assert results[0] == results[1]
    assert await session.scalar(select(func.count()).select_from(ReviewRecord)) == 1


def fail_review(session: Session, _context: object, _instances: object) -> None:
    if any(isinstance(row, ReviewRecord) for row in session.new):
        raise RuntimeError("injected decision storage failure")


async def test_failed_review_rolls_back_decision_and_event(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await draft_for_review(session, workspace)
    event.listen(session.sync_session, "before_flush", fail_review)
    try:
        with pytest.raises(RuntimeError, match="decision storage"):
            await record_review(
                session, workspace, human("reviewer-a"), review_intent(version.version_id)
            )
    finally:
        event.remove(session.sync_session, "before_flush", fail_review)
    assert await session.scalar(select(func.count()).select_from(ReviewRecord)) == 0
    assert await session.scalar(select(func.count()).select_from(Event)) == 1


@pytest.mark.parametrize("operation", ["update", "delete"])
async def test_review_history_is_immutable(
    session: AsyncSession, workspace: UUID, operation: str
) -> None:
    version = await draft_for_review(session, workspace)
    await record_review(session, workspace, human("reviewer-a"), review_intent(version.version_id))
    with pytest.raises(DBAPIError, match="immutable"):
        async with session.begin():
            await session.execute(
                delete(ReviewRecord)
                if operation == "delete"
                else update(ReviewRecord).values(statement="Changed fixture")
            )


async def test_review_rls_hides_missing_and_other_scope(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await draft_for_review(session, workspace)
    receipt = await record_review(
        session, workspace, human("reviewer-a"), review_intent(version.version_id)
    )
    async with session.begin():
        await session.execute(text("SET LOCAL ROLE pg_read_all_data"))
        assert list(await session.scalars(select(ReviewRecord))) == []
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(UUID(int=1))}
        )
        assert list(await session.scalars(select(ReviewRecord))) == []
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(workspace)}
        )
        assert [row.id for row in await session.scalars(select(ReviewRecord))] == [receipt.id]
