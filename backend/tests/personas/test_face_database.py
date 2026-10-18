"""Owner/CI PostgreSQL lane: not executed by synthetic ASGI or arithmetic tests."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.capture_contracts import ReferenceChange
from accord.personas.face_contracts import FaceCommand, FaceSubject
from accord.personas.face_models import FaceGeneration
from accord.personas.face_service import process, profile
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import save
from personas.conftest import command
from personas.test_face_processing import SyntheticProviders
from personas.test_photo_storage import FixtureWrapper, staged


@pytest.mark.asyncio
async def test_exact_replay_changed_intent_owner_and_unbound_exclusion(
    session: AsyncSession, workspace: UUID
) -> None:
    db = session
    wrapper, providers = FixtureWrapper(), SyntheticProviders(())
    upload, portrait = await staged(db, workspace, wrapper)
    version = await save(
        db, workspace, "creator-a", command(photo={"action": "attach", "upload_id": portrait})
    )
    request = FaceCommand(version_id=version.version_id, portrait_id=portrait, request_id=uuid4())
    result = await process(db, workspace, "creator-a", request, wrapper, providers.providers())
    assert result.state == "no_face"
    assert await process(db, workspace, "creator-a", request, wrapper, None) == result
    with pytest.raises(ConflictError):
        await process(
            db,
            workspace,
            "creator-a",
            request.model_copy(update={"face_index": 0, "generation_id": result.generation_id}),
            wrapper,
            providers.providers(),
        )
    with pytest.raises(AccessDeniedError):
        await process(
            db,
            workspace,
            "creator-b",
            request.model_copy(update={"request_id": uuid4()}),
            wrapper,
            providers.providers(),
        )
    inspected = await profile(
        db,
        workspace,
        "viewer",
        FaceSubject(version_id=version.version_id, portrait_id=portrait),
        wrapper,
        None,
    )
    assert inspected.latest == result and inspected.provider_ready is False
    async with db.begin():
        assert len((await db.scalars(select(FaceGeneration))).all()) == 1


@pytest.mark.asyncio
async def test_face_processing_requires_explicit_version_reference(
    session: AsyncSession, workspace: UUID
) -> None:
    db = session
    wrapper = FixtureWrapper()
    _, portrait = await staged(db, workspace, wrapper)
    version = await save(
        db,
        workspace,
        "creator-a",
        command(references=ReferenceChange(action="replace", upload_ids=())),
    )
    with pytest.raises(AccessDeniedError):
        await process(
            db,
            workspace,
            "creator-a",
            FaceCommand(version_id=version.version_id, portrait_id=portrait, request_id=uuid4()),
            wrapper,
            SyntheticProviders(()).providers(),
        )
