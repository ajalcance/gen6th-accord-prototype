"""Non-SQL service ordering proof; independent SQL tests cover active tenant isolation."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.face_contracts import FaceCommand
from accord.personas.face_providers import Detection
from accord.personas.face_service import process, run_processing
from accord.personas.repository import AccessDeniedError
from personas.test_face_processing import SyntheticProviders


@pytest.mark.asyncio
async def test_membership_and_reference_denial_precede_decryption_and_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = FaceCommand(version_id=uuid4(), portrait_id=uuid4(), request_id=uuid4())
    deny = AsyncMock(side_effect=AccessDeniedError("denied"))
    decrypt, run = AsyncMock(), AsyncMock()
    monkeypatch.setattr("accord.personas.face_service.authorize", deny)
    monkeypatch.setattr("accord.personas.face_service.analysis_pixels", decrypt)
    monkeypatch.setattr("accord.personas.face_service.run_processing", run)
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await process(session, uuid4(), "creator-a", command, None, None)
    decrypt.assert_not_called()
    run.assert_not_called()
    monkeypatch.setattr("accord.personas.face_service.authorize", AsyncMock())
    monkeypatch.setattr("accord.personas.face_service.reference", deny)
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await process(session, uuid4(), "creator-a", command, None, None)
    decrypt.assert_not_called()
    run.assert_not_called()


@pytest.mark.asyncio
async def test_provider_errors_are_unavailable_not_empty_results() -> None:
    class Broken(SyntheticProviders):
        async def detect(self, pixels: bytes, width: int, height: int) -> Detection:
            raise ValueError("provider-detail")

    command = FaceCommand(version_id=uuid4(), portrait_id=uuid4(), request_id=uuid4())
    with pytest.raises(RuntimeError, match="face processing unavailable"):
        await run_processing(
            uuid4(), command, b"fixture", "a" * 64, 200, 100, None, Broken().providers()
        )
