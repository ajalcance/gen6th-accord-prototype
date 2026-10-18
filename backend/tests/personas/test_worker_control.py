"""Pure orchestration tests; database effects are checked separately on PostgreSQL."""

import asyncio
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from redis.asyncio import Redis
from redis.exceptions import ConnectionError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command import worker


@pytest.mark.parametrize("outage", [False, True])
async def test_worker_seals_after_ingestion_outage(
    monkeypatch: pytest.MonkeyPatch, outage: bool
) -> None:
    consume = AsyncMock(return_value=3, side_effect=ConnectionError() if outage else None)
    seal = AsyncMock(return_value=2)
    purge = AsyncMock(return_value=1)
    session = AsyncMock(spec=AsyncSession)
    evaluate = AsyncMock(return_value=4)
    monkeypatch.setattr(worker, "consume_once", consume)
    monkeypatch.setattr(worker, "seal_new", seal)
    monkeypatch.setattr(worker, "evaluate_once", evaluate)
    monkeypatch.setattr(worker, "purge_expired", purge)
    result = await worker.process_once(cast(Redis, object()), session)
    assert result == (0 if outage else 3, 2, 1)
    assert session.rollback.await_count == int(outage)
    seal.assert_awaited_once_with(session)
    evaluate.assert_awaited_once_with(session)
    purge.assert_awaited_once_with(session)


async def test_worker_does_not_swallow_database_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(worker, "consume_once", AsyncMock(side_effect=SQLAlchemyError()))
    seal = AsyncMock()
    monkeypatch.setattr(worker, "seal_new", seal)
    with pytest.raises(SQLAlchemyError):
        await worker.process_once(cast(Redis, object()), AsyncMock(spec=AsyncSession))
    seal.assert_not_awaited()


async def test_detection_failure_prevents_retention(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(worker, "consume_once", AsyncMock(return_value=0))
    monkeypatch.setattr(worker, "seal_new", AsyncMock(return_value=0))
    monkeypatch.setattr(worker, "evaluate_once", AsyncMock(side_effect=SQLAlchemyError()))
    purge = AsyncMock()
    monkeypatch.setattr(worker, "purge_expired", purge)
    with pytest.raises(SQLAlchemyError):
        await worker.process_once(cast(Redis, object()), AsyncMock(spec=AsyncSession))
    purge.assert_not_awaited()


async def test_worker_error_logs_exclude_exception_details(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(
        worker, "get_settings", lambda: SimpleNamespace(log_level="info", command_poll_seconds=1)
    )
    monkeypatch.setattr(worker, "setup_logging", lambda _level: None)
    monkeypatch.setattr(
        worker, "run_once", AsyncMock(side_effect=RuntimeError("fixture-private-detail"))
    )

    async def stop(_seconds: int) -> None:
        raise asyncio.CancelledError()

    monkeypatch.setattr(worker, "asyncio", SimpleNamespace(sleep=stop))
    with pytest.raises(asyncio.CancelledError):
        await worker.main()
    assert "worker pass failed (RuntimeError)" in caplog.messages
    assert all("fixture-private-detail" not in message for message in caplog.messages)
