"""Bounded reconciliation keeps uncompleted durable intents for a later machine invocation."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import job_worker
from personas.job_test_support import runtime
from personas.runtime_fixtures import job_rows


@pytest.mark.asyncio
@pytest.mark.parametrize("timeout", [False, True])
async def test_reconcile_filters_queued_before_limit_and_reports_partial_timeout(
    monkeypatch: pytest.MonkeyPatch,
    timeout: bool,
) -> None:
    row, _ = job_rows()
    active, jobs = runtime(row), (uuid4(), uuid4())
    dispatch = AsyncMock(side_effect=[True, TimeoutError()] if timeout else [True, False])
    monkeypatch.setattr(job_worker, "dispatch_one", dispatch)
    monkeypatch.setattr(job_worker, "observation", Mock())
    async with AsyncSession() as session:
        monkeypatch.setattr(session, "execute", AsyncMock())
        scalars = AsyncMock(return_value=jobs)
        monkeypatch.setattr(session, "scalars", scalars)
        result = await job_worker.reconcile(session, active, "verified-workload")
    assert result == {"examined": 2, "dispatched": 1}
    assert all(call.args[1] == row.workspace_id for call in dispatch.await_args_list)
    assert scalars.await_args is not None
    query = str(scalars.await_args.args[0])
    assert "persona_face_job_transitions.state" in query
    assert query.rindex("WHERE") < query.rindex("LIMIT")
