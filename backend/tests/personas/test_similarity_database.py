"""Owner/CI PostgreSQL acceptance lane; no claim that collection executes these tests."""

import base64
from dataclasses import replace
from uuid import UUID, uuid4

import fakeredis.aioredis
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.face_contracts import FaceCommand
from accord.personas.face_service import process
from accord.personas.photo_intake import intake
from accord.personas.photo_models import Portrait
from accord.personas.repository import AccessDeniedError
from accord.personas.service import save
from accord.personas.similarity_cache import RedisQueryStore
from accord.personas.similarity_contracts import SearchCommand
from accord.personas.similarity_query import SimilarityRuntime, load_query, prepare_query
from accord.personas.similarity_repository import pool
from accord.personas.similarity_service import search
from accord.personas.workflow_contracts import WorkflowActor
from personas.conftest import command
from personas.similarity_fixtures import policy, upload
from personas.test_face_processing import SyntheticProviders
from personas.test_photo_storage import FixtureInspector, FixtureWrapper, body


async def enrolled(
    session: AsyncSession, workspace: UUID, runtime: SimilarityRuntime
) -> FaceCommand:
    receipt = await intake(
        session, workspace, "creator-a", body(upload()), runtime.inspector, runtime.wrapper
    )
    version = await save(
        session,
        workspace,
        "creator-a",
        command(photo={"action": "attach", "upload_id": receipt.id}),
    )
    detection = FaceCommand(
        version_id=version.version_id, portrait_id=receipt.id, request_id=uuid4()
    )
    result = await process(
        session, workspace, "creator-a", detection, runtime.wrapper, runtime.faces
    )
    selected = detection.model_copy(
        update={"request_id": uuid4(), "generation_id": result.generation_id, "face_index": 0}
    )
    await process(session, workspace, "creator-a", selected, runtime.wrapper, runtime.faces)
    return detection


async def setup_query(workspace: UUID) -> tuple[SimilarityRuntime, SearchCommand]:
    runtime = SimilarityRuntime(
        FixtureInspector(),
        FixtureWrapper(),
        SyntheticProviders().providers(),
        RedisQueryStore(fakeredis.aioredis.FakeRedis()),
        policy(),
    )
    command = upload()
    await prepare_query(runtime, workspace, "viewer", command, base64.b64decode(command.data))
    capture = await load_query(runtime, workspace, "viewer", command.request_id)
    runtime = replace(runtime, policy=policy(decoder_version=capture.receipt.decoder_version))
    return runtime, SearchCommand(query_id=command.request_id, request_id=uuid4(), face_index=0)


@pytest.mark.asyncio
async def test_latest_generation_prevents_using_superseded_representations_and_queries_never_enroll(
    session: AsyncSession, workspace: UUID
) -> None:
    runtime, query = await setup_query(workspace)
    detected = await enrolled(session, workspace, runtime)
    actor = WorkflowActor(actor_ref="viewer", kind="human")
    result = await search(session, workspace, actor, query, runtime)
    assert (
        result.state == "candidate_review" and result.items[0].portrait_id == detected.portrait_id
    )
    await process(
        session,
        workspace,
        "creator-a",
        detected.model_copy(update={"request_id": uuid4()}),
        runtime.wrapper,
        runtime.faces,
    )
    unavailable = await search(session, workspace, actor, query, runtime)
    assert unavailable.state == "no_compatible_references"
    assert unavailable.reference_count == 1 and unavailable.compatible_count == 0
    async with session.begin():
        assert await session.scalar(select(func.count()).select_from(Portrait)) == 1


@pytest.mark.asyncio
async def test_current_head_history_scope_and_foreign_workspace_exclusion(
    session: AsyncSession, workspace: UUID
) -> None:
    runtime, query = await setup_query(workspace)
    detected = await enrolled(session, workspace, runtime)
    async with session.begin():
        old = (await pool(session, workspace, "current"))[0][0]
    await save(
        session, workspace, "creator-a", command(persona_id=old.persona_id, expected_revision=1)
    )
    actor = WorkflowActor(actor_ref="viewer", kind="human")
    current = await search(session, workspace, actor, query, runtime)
    history = await search(
        session, workspace, actor, query.model_copy(update={"scope": "history"}), runtime
    )
    assert current.state == "no_compatible_references"
    assert history.items[0].version.version_id == detected.version_id
    async with session.begin():
        assert await pool(session, uuid4(), "history") == []
    with pytest.raises(AccessDeniedError):
        await search(session, uuid4(), actor, query, runtime)
