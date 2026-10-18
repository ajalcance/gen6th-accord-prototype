"""Real PostgreSQL durable delivery, thresholds, trust, recovery and tenancy."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from accord.command import detection
from accord.command.detection import evaluate_once
from accord.command.detection_models import DetectionReceipt
from accord.command.models import Event
from accord.personas.detection_health import observe_detection_backlog
from accord.personas.repository import AccessDeniedError


def event(workspace: UUID, **changes: object) -> Event:
    values: dict[str, object] = dict(
        event_id=uuid4().hex,
        tenant_id=workspace,
        ts=datetime.now(UTC),
        actor_type="user",
        category="persona",
        action="persona.version_saved",
        outcome="success",
        severity="info",
        source="server",
    )
    return Event(**(values | changes))


async def test_delivery_replay_and_thresholds(session: AsyncSession, workspace: UUID) -> None:
    when = datetime.now(UTC)
    session.add_all([event(workspace, ts=when) for _ in range(100)])
    await session.commit()
    assert await evaluate_once(session) == 100
    assert await evaluate_once(session) == 0
    receipts = list(await session.scalars(select(DetectionReceipt)))
    assert len(receipts) == 100
    assert all(
        row.findings == [{"rule_id": "persona-write-surge", "count": 100, "severity": "warn"}]
        for row in receipts
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"source": "client"},
        {"source": "unknown"},
        {"tenant_id": None},
        {"category": "command"},
        {"action": "persona.unknown"},
    ],
)
async def test_untrusted_or_unregistered_events_are_not_evaluated(
    session: AsyncSession, workspace: UUID, changes: dict[str, object]
) -> None:
    session.add(event(workspace, **changes))
    await session.commit()
    assert await evaluate_once(session) == 0
    assert await session.scalar(select(func.count()).select_from(DetectionReceipt)) == 0


async def test_batch_limit_drains_without_skipping(session: AsyncSession, workspace: UUID) -> None:
    session.add_all([event(workspace) for _ in range(101)])
    await session.commit()
    assert await evaluate_once(session) == 100
    assert await evaluate_once(session) == 1
    assert await evaluate_once(session) == 0
    assert await session.scalar(select(func.count()).select_from(DetectionReceipt)) == 101


async def test_tenant_and_source_cannot_force_findings(
    session: AsyncSession, workspace: UUID
) -> None:
    session.add_all([event(uuid4(), outcome="failure") for _ in range(30)])
    session.add_all([event(workspace, source="client", severity="critical") for _ in range(100)])
    session.add(event(workspace, severity="critical"))
    await session.commit()
    assert await evaluate_once(session) == 31
    receipts = list(await session.scalars(select(DetectionReceipt)))
    ours = [row for row in receipts if row.workspace_id == workspace]
    assert len(ours) == 1 and ours[0].findings == [
        {"rule_id": "critical-catchall", "count": 1, "severity": "critical"}
    ]
    assert all(not row.findings for row in receipts if row.workspace_id != workspace)


async def test_failure_rolls_back_batch_and_retries(
    session: AsyncSession, workspace: UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    session.add_all([event(workspace, severity="critical") for _ in range(2)])
    await session.commit()
    original = detection.count_window
    calls = 0

    async def unavailable(*_args: object) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            return 2
        raise RuntimeError("fixture failure")

    monkeypatch.setattr(detection, "count_window", unavailable)
    with pytest.raises(RuntimeError):
        await evaluate_once(session)
    assert await session.scalar(select(func.count()).select_from(DetectionReceipt)) == 0
    await session.rollback()
    monkeypatch.setattr(detection, "count_window", original)
    assert await evaluate_once(session) == 2


async def test_concurrent_workers_emit_once(db_engine: AsyncEngine, workspace: UUID) -> None:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as seed:
        seed.add(event(workspace, severity="critical"))
        await seed.commit()

    async def run() -> int:
        async with maker() as session:
            return await evaluate_once(session)

    assert sorted(await asyncio.gather(run(), run())) == [0, 1]


async def test_late_event_and_window_boundary(session: AsyncSession, workspace: UUID) -> None:
    when = datetime.now(UTC) - timedelta(days=365)
    session.add(event(workspace, ts=when - timedelta(seconds=300), outcome="failure"))
    session.add_all([event(workspace, ts=when, outcome="failure") for _ in range(29)])
    await session.commit()
    assert await evaluate_once(session) == 30
    late = event(workspace, ts=when, outcome="failure")
    session.add(late)
    await session.commit()
    assert await evaluate_once(session) == 1
    receipt = await session.get(DetectionReceipt, late.event_id)
    assert receipt is not None and not receipt.window_within_retention
    assert receipt.findings == [{"rule_id": "failure-surge", "count": 30, "severity": "warn"}]


async def test_backlog_authorization_and_observation(
    session: AsyncSession, workspace: UUID
) -> None:
    session.add(event(workspace))
    session.add(event(uuid4()))
    await session.commit()
    result = await observe_detection_backlog(session, workspace, "viewer")
    assert result.pending_events == 1 and result.oldest_pending_at is not None
    assert await evaluate_once(session) == 3
    result = await observe_detection_backlog(session, workspace, "viewer")
    assert result.pending_events == 0
    with pytest.raises(AccessDeniedError):
        await observe_detection_backlog(session, uuid4(), "viewer")
