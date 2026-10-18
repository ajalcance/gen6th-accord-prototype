"""Ephemeral cache lifecycle with fake Redis and real encryption/metadata stripping."""

import base64
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import fakeredis.aioredis
import pytest
from fastapi import HTTPException

from accord.personas.repository import ConflictError
from accord.personas.similarity_cache import (
    CLOSED,
    RedisQueryStore,
    decrypt_payload,
    encrypt_payload,
    query_key,
)
from accord.personas.similarity_query import (
    SimilarityRuntime,
    available,
    load_query,
    prepare_query,
    query_vectors,
)
from personas.similarity_fixtures import policy, upload
from personas.test_face_processing import SyntheticProviders
from personas.test_photo_storage import FixtureInspector, FixtureWrapper


@pytest.mark.asyncio
async def test_encrypted_query_replay_selection_clear_and_actor_workspace_isolation() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    store, wrapper, providers = RedisQueryStore(redis), FixtureWrapper(), SyntheticProviders()
    runtime = SimilarityRuntime(FixtureInspector(), wrapper, providers.providers(), store, policy())
    workspace, actor, command = uuid4(), "synthetic-human", upload()
    receipt = await prepare_query(
        runtime, workspace, actor, command, base64.b64decode(command.data)
    )
    key = query_key(workspace, actor, command.request_id)
    raw, ttl = await store.get(key), await redis.ttl(key)
    assert raw and b"synthetic-detector" not in raw and 0 < ttl <= 600
    assert not providers.calls
    assert (
        await prepare_query(runtime, workspace, actor, command, base64.b64decode(command.data))
        == receipt
    )
    assert await redis.ttl(key) <= ttl
    capture = await load_query(runtime, workspace, actor, receipt.query_id)
    info, vectors = await query_vectors(runtime, workspace, actor, capture, 0)
    assert info.dimensions == 2 and vectors == ((0.6, 0.8), (0.6, 0.8))
    await query_vectors(runtime, workspace, actor, capture, 0)
    assert len(providers.calls) == 2
    for other_workspace, other_actor in [(uuid4(), actor), (workspace, "different-human")]:
        with pytest.raises(HTTPException) as denied:
            await load_query(runtime, other_workspace, other_actor, receipt.query_id)
        assert denied.value.status_code == 410
    keys = tuple(query_key(workspace, actor, receipt.query_id, part) for part in range(11))
    await store.close(keys, datetime.now(UTC) + timedelta(minutes=10))
    assert await store.get(key) == CLOSED and await store.get(keys[1]) is None
    with pytest.raises(HTTPException):
        await prepare_query(runtime, workspace, actor, command, base64.b64decode(command.data))
    await redis.aclose()


@pytest.mark.asyncio
async def test_clear_tombstone_blocks_late_prepare_and_absolute_expiry() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    store = RedisQueryStore(redis)
    workspace, query = uuid4(), uuid4()
    keys = tuple(query_key(workspace, "fixture", query, part) for part in range(11))
    assert len({key.rsplit(":", 1)[0] for key in keys}) == 1
    expires = datetime.now(UTC) + timedelta(seconds=60)
    await store.close(keys, expires)
    await store.put_once(keys[0], b"late-result", expires)
    assert await store.get(keys[0]) == CLOSED
    await store.put_once(keys[1], b"fixture", datetime.now(UTC) - timedelta(seconds=1))
    assert await store.get(keys[1]) is None
    await redis.aclose()


@pytest.mark.asyncio
async def test_changed_prepare_intent_and_context_tampering_rejected() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    wrapper = FixtureWrapper()
    runtime = SimilarityRuntime(
        FixtureInspector(),
        wrapper,
        SyntheticProviders().providers(),
        RedisQueryStore(redis),
        policy(),
    )
    workspace, command = uuid4(), upload()
    await prepare_query(runtime, workspace, "fixture", command, base64.b64decode(command.data))
    with pytest.raises(ConflictError):
        await prepare_query(
            runtime,
            workspace,
            "fixture",
            command.model_copy(update={"media_type": "image/jpeg"}),
            base64.b64decode(command.data),
        )
    raw = await encrypt_payload({"private": "fixture"}, "owned-context", wrapper)
    assert await decrypt_payload(raw, "owned-context", wrapper) == {"private": "fixture"}
    with pytest.raises(AssertionError):
        await decrypt_payload(raw, "foreign-context", wrapper)
    await redis.aclose()


def test_no_runtime_or_calibration_or_expired_policy_can_activate() -> None:
    with pytest.raises(RuntimeError):
        available(None)
    runtime = SimilarityRuntime(
        FixtureInspector(),
        FixtureWrapper(),
        SyntheticProviders().providers(),
        RedisQueryStore(fakeredis.aioredis.FakeRedis()),
    )
    with pytest.raises(RuntimeError):
        available(runtime)


@pytest.mark.asyncio
async def test_no_face_query_remains_unselected_without_encoding() -> None:
    redis, providers = fakeredis.aioredis.FakeRedis(), SyntheticProviders(())
    runtime = SimilarityRuntime(
        FixtureInspector(),
        FixtureWrapper(),
        providers.providers(),
        RedisQueryStore(redis),
        policy(),
    )
    command = upload()
    receipt = await prepare_query(
        runtime, uuid4(), "fixture", command, base64.b64decode(command.data)
    )
    assert receipt.state == "no_face" and receipt.faces == () and not providers.calls
    await redis.aclose()
