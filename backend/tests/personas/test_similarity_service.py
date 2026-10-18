"""Fresh authorization/expiry/catalogue proofs with disconnected SQL; not RLS acceptance."""

import base64
from collections.abc import AsyncIterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import fakeredis.aioredis
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import similarity_service as service
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.similarity_cache import RedisQueryStore
from accord.personas.similarity_contracts import SearchCommand
from accord.personas.similarity_query import SimilarityRuntime, load_query, prepare_query
from accord.personas.workflow_contracts import WorkflowActor
from personas.similarity_fixtures import candidate, policy, upload
from personas.test_face_processing import SyntheticProviders, face
from personas.test_photo_storage import FixtureInspector, FixtureWrapper


def runtime(providers: SyntheticProviders | None = None) -> SimilarityRuntime:
    return SimilarityRuntime(
        FixtureInspector(),
        FixtureWrapper(),
        (providers or SyntheticProviders()).providers(),
        RedisQueryStore(fakeredis.aioredis.FakeRedis()),
        policy(),
    )


async def query(active: SimilarityRuntime, workspace: UUID, actor: WorkflowActor) -> SearchCommand:
    command = upload()
    receipt = await prepare_query(
        active, workspace, actor.actor_ref, command, base64.b64decode(command.data)
    )
    return SearchCommand(query_id=receipt.query_id, request_id=uuid4(), face_index=0)


def trusted(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    authorize = AsyncMock()
    monkeypatch.setattr(service, "authorize_actor", authorize)
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    monkeypatch.setattr(service, "observation", Mock())
    return authorize


@pytest.mark.asyncio
async def test_membership_denial_and_runtime_absence_precede_consuming_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor, consumed = WorkflowActor(actor_ref="fixture", kind="human"), False

    async def body() -> AsyncIterator[bytes]:
        nonlocal consumed
        consumed = True
        yield b"invalid"

    auth = trusted(monkeypatch)
    auth.side_effect = AccessDeniedError("denied")
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await service.prepare(session, uuid4(), actor, body(), runtime())
    assert not consumed
    auth.side_effect = None
    async with AsyncSession() as session:
        with pytest.raises(RuntimeError):
            await service.prepare(session, uuid4(), actor, body(), None)
    assert not consumed


@pytest.mark.asyncio
async def test_renewed_membership_denial_after_model_call_prevents_candidate_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active, workspace, actor = runtime(), uuid4(), WorkflowActor(actor_ref="fixture", kind="human")
    command = await query(active, workspace, actor)
    auth = trusted(monkeypatch)
    auth.side_effect = [None, AccessDeniedError("revoked")]
    pool = AsyncMock()
    monkeypatch.setattr(service, "pool", pool)
    active = replace(
        active,
        policy=policy(
            decoder_version=(
                await load_query(active, workspace, actor.actor_ref, command.query_id)
            ).receipt.decoder_version
        ),
    )
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await service.search(session, workspace, actor, command, active)
    pool.assert_not_called()


@pytest.mark.asyncio
async def test_empty_incompatible_abstention_and_candidates_have_distinct_states(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active, workspace, actor = runtime(), uuid4(), WorkflowActor(actor_ref="fixture", kind="human")
    command = await query(active, workspace, actor)
    capture = await load_query(active, workspace, actor.actor_ref, command.query_id)
    active = replace(active, policy=policy(decoder_version=capture.receipt.decoder_version))
    trusted(monkeypatch)
    rows = AsyncMock(return_value=[])
    scored = AsyncMock(return_value=[])
    monkeypatch.setattr(service, "pool", rows)
    monkeypatch.setattr(service, "score_references", scored)
    monkeypatch.setattr(service, "pool_binding", lambda rows: ())
    async with AsyncSession() as session:
        assert (
            await service.search(session, workspace, actor, command, active)
        ).state == "empty_catalogue"
    rows.return_value = [object()]
    async with AsyncSession() as session:
        assert (
            await service.search(session, workspace, actor, command, active)
        ).state == "no_compatible_references"
    scored.return_value = [candidate(workspace, 0.7)]
    async with AsyncSession() as session:
        assert (
            await service.search(session, workspace, actor, command, active)
        ).state == "no_confident_match"
    scored.return_value = [candidate(workspace, 0.99)]
    async with AsyncSession() as session:
        page = await service.search(session, workspace, actor, command, active)
        assert page.state == "candidate_review" and page.items[0].face_cosine == 0.99
        assert not any(
            type(row).__name__ in {"Portrait", "PortraitCapture", "VersionReference"}
            for row in session.new
        )


@pytest.mark.asyncio
async def test_quality_blocks_before_encoder_and_catalogue(monkeypatch: pytest.MonkeyPatch) -> None:
    providers = SyntheticProviders((face(width=32),))
    active, workspace, actor = (
        runtime(providers),
        uuid4(),
        WorkflowActor(actor_ref="fixture", kind="human"),
    )
    command = await query(active, workspace, actor)
    trusted(monkeypatch)
    rows = AsyncMock()
    monkeypatch.setattr(service, "pool", rows)
    async with AsyncSession() as session:
        page = await service.search(session, workspace, actor, command, active)
    assert page.state == "quality_blocked" and page.reasons == ("small_face",)
    assert not providers.calls
    rows.assert_not_called()


@pytest.mark.asyncio
async def test_incompatible_query_generation_cannot_reach_catalogue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active, workspace, actor = runtime(), uuid4(), WorkflowActor(actor_ref="fixture", kind="human")
    command = await query(active, workspace, actor)
    active = replace(active, policy=policy(model="different-reviewed-model"))
    trusted(monkeypatch)
    rows = AsyncMock()
    monkeypatch.setattr(service, "pool", rows)
    async with AsyncSession() as session:
        with pytest.raises(RuntimeError, match="incompatible"):
            await service.search(session, workspace, actor, command, active)
    rows.assert_not_called()


@pytest.mark.asyncio
async def test_catalogue_changes_and_final_calibration_expiry_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active, workspace, actor = runtime(), uuid4(), WorkflowActor(actor_ref="fixture", kind="human")
    command = await query(active, workspace, actor)
    capture = await load_query(active, workspace, actor.actor_ref, command.query_id)
    active = replace(active, policy=policy(decoder_version=capture.receipt.decoder_version))
    trusted(monkeypatch)
    monkeypatch.setattr(service, "pool", AsyncMock(return_value=[]))
    monkeypatch.setattr(service, "score_references", AsyncMock(return_value=[]))
    # Distinct snapshots simulate a head/reference-generation change during decryption.
    snapshots = iter([("before",), ("after",)])
    monkeypatch.setattr(service, "pool_binding", lambda rows: next(snapshots))
    async with AsyncSession() as session:
        with pytest.raises(ConflictError):
            await service.search(session, workspace, actor, command, active)
    expired = replace(
        active,
        policy=policy(
            reviewed_at=datetime.now(UTC) - timedelta(hours=2),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        ),
    )
    async with AsyncSession() as session:
        readiness = await service.readiness(session, workspace, actor, expired)
        assert readiness.state == "calibration_expired"
        with pytest.raises(RuntimeError):
            await service.search(session, workspace, actor, command, expired)
