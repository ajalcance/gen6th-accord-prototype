"""Real sealed-generation consumption against synthetic vectors; no model accuracy claims."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.exceptions import InvalidTag
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.capture_models import PortraitCapture
from accord.personas.face_contracts import FaceCommand
from accord.personas.face_models import FaceGeneration
from accord.personas.face_processing import detect_result, selected_result
from accord.personas.face_storage import store_result
from accord.personas.models import Version
from accord.personas.similarity_query import SimilarityRuntime
from accord.personas.similarity_ranking import score_references
from accord.personas.similarity_repository import pool
from personas.similarity_fixtures import candidate, policy
from personas.test_face_processing import image_bytes
from personas.test_similarity_service import runtime


async def reference(active: SimilarityRuntime) -> tuple[Version, PortraitCapture, FaceGeneration]:
    content = candidate(uuid4(), 0.9).version
    version = Version(
        id=content.version_id,
        persona_id=content.persona_id,
        workspace_id=content.workspace_id,
        revision=1,
        creator_ref=content.creator_ref,
        recorded_at=content.recorded_at,
        event_id=uuid4().hex,
        **content.content.model_dump(),
    )
    capture = PortraitCapture(
        portrait_id=uuid4(),
        workspace_id=content.workspace_id,
        width=200,
        height=100,
        sha256="a" * 64,
        decoder_version="synthetic-decoder",
        recipe="rgba-png-1024-v1",
    )
    command = FaceCommand(
        version_id=version.id, portrait_id=capture.portrait_id, request_id=uuid4()
    )
    parent = await detect_result(
        content.workspace_id, command, image_bytes(), capture.sha256, 200, 100, active.faces
    )
    command = command.model_copy(
        update={"request_id": uuid4(), "generation_id": parent.generation_id, "face_index": 0}
    )
    result, vectors = await selected_result(command, parent, image_bytes(), active.faces)
    async with AsyncSession() as session:
        await store_result(session, result, command, "synthetic-human", vectors, active.wrapper)
        row = next(row for row in session.new if isinstance(row, FaceGeneration))
    return version, capture, row


@pytest.mark.asyncio
async def test_only_compatible_sealed_references_rank_and_integrity_failure_is_not_empty() -> None:
    active = runtime()
    row = await reference(active)
    calibrated = policy(decoder_version="synthetic-decoder")
    query = ((0.6, 0.8), (-0.6, -0.8))
    scored = await score_references(active, [row], query, calibrated)
    assert scored[0].face_cosine == 1 and scored[0].whole_cosine == -1
    assert await score_references(active, [row], query, policy()) == []
    assert await score_references(active, [(row[0], row[1], None)], query, calibrated) == []
    row[1].sha256 = "b" * 64
    with pytest.raises(RuntimeError, match="integrity"):
        await score_references(active, [row], query, calibrated)


@pytest.mark.asyncio
async def test_cipher_or_vector_failure_prevents_a_partial_rank() -> None:
    active = runtime()
    row = await reference(active)
    row[2].ciphertext = row[2].ciphertext[:-1] + bytes([row[2].ciphertext[-1] ^ 1])
    with pytest.raises(InvalidTag):
        await score_references(
            active, [row], ((0.6, 0.8), (0.6, 0.8)), policy(decoder_version="synthetic-decoder")
        )


@pytest.mark.asyncio
async def test_oversized_reference_pool_is_unavailable_instead_of_partial() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = AsyncMock()
    result.all = lambda: [(None, None, None)] * 129
    session.execute.return_value = result
    with pytest.raises(RuntimeError, match="exceeds bounded"):
        await pool(session, uuid4(), "current")
