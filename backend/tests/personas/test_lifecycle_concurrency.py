"""Disposable SQL only: performer-wide status, bounded history and concurrent intent safety."""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from accord.personas import lifecycle_reads as reads
from accord.personas import lifecycle_service as service
from accord.personas.lifecycle_contracts import (
    AppendLifecycle,
    Concern,
    LifecycleHistory,
    LifecycleReceipt,
    Response,
    Subject,
)
from accord.personas.repository import ConflictError
from personas.test_lifecycle_sql import prepared
from personas.workflow_fixtures import human


async def report(session: AsyncSession, workspace: UUID, version: UUID) -> LifecycleReceipt:
    return await service.append(
        session,
        workspace,
        human("viewer"),
        AppendLifecycle(
            version_id=version,
            request_id=uuid4(),
            content=Concern(kind="concern", category="rights", statement="Synthetic concern"),
        ),
    )


async def respond(
    session: AsyncSession,
    workspace: UUID,
    case: LifecycleReceipt,
    decision: str,
    previous: UUID | None = None,
) -> LifecycleReceipt:
    content = Response.model_validate(
        {
            "kind": "response",
            "concern_id": case.id,
            "decision": decision,
            "statement": "Synthetic independent response",
        }
    )
    return await service.append(
        session,
        workspace,
        human("reviewer"),
        AppendLifecycle(
            version_id=case.version_id,
            request_id=uuid4(),
            expected_previous_id=previous,
            content=content,
        ),
    )


async def test_hidden_case_and_unrelated_suspensions_remain_effective(
    session: AsyncSession,
    workspace: UUID,
) -> None:
    command = await prepared(session, workspace)
    first, second = await report(session, workspace, command.version_id), await report(
        session, workspace, command.version_id
    )
    a, b = await respond(session, workspace, first, "suspended"), await respond(
        session, workspace, second, "suspended"
    )
    for _ in range(21):
        await report(session, workspace, command.version_id)
    subject = Subject(version_id=command.version_id)
    status = await reads.read(session, workspace, human("viewer"), subject)
    assert status.suspended and all(
        case.report.id not in (first.id, second.id) for case in status.concerns
    )
    page = await reads.history(
        session, workspace, human("reviewer"), LifecycleHistory(version_id=command.version_id)
    )
    assert page.next_before_ordinal is not None
    older = await reads.history(
        session,
        workspace,
        human("reviewer"),
        LifecycleHistory(version_id=command.version_id, before_ordinal=page.next_before_ordinal),
    )
    assert any(case.report.id == first.id and case.response == a for case in older.concerns)
    await respond(session, workspace, first, "resolved", a.id)
    assert (await reads.read(session, workspace, human("viewer"), subject)).suspended
    await respond(session, workspace, second, "resolved", b.id)
    assert not (await reads.read(session, workspace, human("viewer"), subject)).suspended


async def test_same_request_concurrency_returns_one_and_competing_replacements_conflict(
    session: AsyncSession,
    workspace: UUID,
    db_engine: AsyncEngine,
) -> None:
    command = await prepared(session, workspace)
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def submit(command: AppendLifecycle) -> LifecycleReceipt | ConflictError:
        async with maker() as local:
            try:
                return await service.append(local, workspace, human("creator-a"), command)
            except ConflictError as exc:
                return exc

    first, replay = await asyncio.gather(submit(command), submit(command))
    assert isinstance(first, LifecycleReceipt) and replay == first
    alternatives = [
        command.model_copy(update={"request_id": uuid4(), "expected_previous_id": first.id})
        for _ in range(2)
    ]
    results = await asyncio.gather(*(submit(c) for c in alternatives))
    assert sum(isinstance(row, LifecycleReceipt) for row in results) == 1
    assert sum(isinstance(row, ConflictError) for row in results) == 1
