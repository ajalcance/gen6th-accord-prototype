"""Disconnected transaction orchestration harness; PostgreSQL remains a separate lane."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import job_service, job_worker
from accord.personas.face_contracts import FaceResult
from accord.personas.job_models import FaceJob, FaceJobTransition
from accord.personas.job_repository import receipt
from accord.personas.job_runtime import JobRuntime
from personas.test_face_processing import SyntheticProviders
from personas.test_photo_storage import FixtureWrapper


def runtime(row: FaceJob) -> JobRuntime:
    return JobRuntime(
        row.workspace_id,
        row.config_id,
        FixtureWrapper(),
        SyntheticProviders().providers(),
        AsyncMock(),
    )


def face_result(row: FaceJob) -> FaceResult:
    return FaceResult(
        workspace_id=row.workspace_id,
        version_id=row.version_id,
        portrait_id=row.portrait_id,
        request_id=row.request_id,
        generation_id=uuid4(),
        parent_id=None,
        source_sha256="a" * 64,
        width=200,
        height=100,
        detector="synthetic-detector",
        recorded_at=datetime.now(UTC),
        faces=(),
        selected=None,
        state="no_face",
        reasons=(),
        representation=None,
    )


def prepare(
    monkeypatch: pytest.MonkeyPatch,
    session: AsyncSession,
    row: FaceJob,
    initial: FaceJobTransition,
) -> tuple[list[FaceJobTransition], dict[str, Mock]]:
    events = [initial]

    def add(value: object) -> None:
        if isinstance(value, FaceJobTransition):
            events.append(value)

    monkeypatch.setattr(session, "add", Mock(side_effect=add))
    monkeypatch.setattr(session, "flush", AsyncMock())
    mocks: dict[str, Mock] = {}

    async def latest(*args: object) -> FaceJobTransition:
        return events[-1]

    for module in (job_service, job_worker):
        for name in ("job_lock", "owned", "internal_row"):
            mock = AsyncMock(return_value=row)
            monkeypatch.setattr(module, name, mock)
            mocks[module.__name__.rsplit(".", 1)[-1] + "." + name] = mock
        monkeypatch.setattr(module, "latest", latest)
        monkeypatch.setattr(module, "observation", Mock())
    monkeypatch.setattr(job_service, "authorize", AsyncMock())
    monkeypatch.setattr(job_service, "reference", AsyncMock())
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())

    async def inspect(*args: object) -> object:
        return receipt(row, events[-1])

    monkeypatch.setattr(job_service, "inspect", inspect)
    return events, mocks
