"""Portrait observations must reach durable detection without trusting browser claims."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.detection import evaluate_once
from accord.command.detection_models import DetectionReceipt
from personas.test_detection import event

PORTRAIT_ACTIONS = (
    "persona.portrait_uploaded",
    "persona.portrait_inspected",
    "persona.portrait_bound",
    "persona.portrait_read",
)


@pytest.mark.parametrize("action", PORTRAIT_ACTIONS)
async def test_portrait_detection_is_durable_server_only_and_tenant_scoped(
    session: AsyncSession, workspace: UUID, action: str
) -> None:
    other = uuid4()
    ours = event(workspace, action=action, severity="critical")
    theirs = event(other, action=action, severity="critical")
    client = [
        event(workspace, action=action, source="client", severity="critical") for _ in range(12)
    ]
    session.add_all([ours, theirs, *client])
    await session.commit()
    assert await evaluate_once(session) == 2
    assert await evaluate_once(session) == 0
    receipts = list(await session.scalars(select(DetectionReceipt)))
    assert {row.event_id for row in receipts} == {ours.event_id, theirs.event_id}
    assert {row.workspace_id for row in receipts} == {workspace, other}
    assert all(
        row.findings == [{"rule_id": "critical-catchall", "count": 1, "severity": "critical"}]
        for row in receipts
    )
