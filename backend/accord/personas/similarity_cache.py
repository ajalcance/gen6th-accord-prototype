"""Injected Redis ephemeral storage. Absolute expiry, actor binding and clear tombstones."""

import base64
import hashlib
import json
import math
from datetime import datetime
from typing import Protocol
from uuid import UUID

from redis.asyncio import Redis

from accord.personas.evidence_crypto import KeyWrapper, SealedEvidence, seal, unseal

MAX_CACHE_BYTES = 14000000
CLOSED = b"closed"


class QueryStore(Protocol):
    async def get(self, key: str) -> bytes | None: ...

    async def put_once(self, key: str, data: bytes, expires: datetime) -> None: ...

    async def close(self, keys: tuple[str, ...], expires: datetime) -> None: ...


class RedisQueryStore:
    def __init__(self, client: Redis) -> None:
        self.client = client

    async def get(self, key: str) -> bytes | None:
        raw = await self.client.get(key)
        if raw is None:
            return None
        if isinstance(raw, str):
            raw = raw.encode("ascii")
        if not isinstance(raw, bytes) or len(raw) > MAX_CACHE_BYTES:
            raise RuntimeError("invalid query storage")
        return raw

    async def put_once(self, key: str, data: bytes, expires: datetime) -> None:
        if not 1 <= len(data) <= MAX_CACHE_BYTES:
            raise RuntimeError("query storage bound exceeded")
        await self.client.set(key, data, nx=True, pxat=math.floor(expires.timestamp() * 1000))

    async def close(self, keys: tuple[str, ...], expires: datetime) -> None:
        async with self.client.pipeline(transaction=True) as pipe:
            pipe.set(keys[0], CLOSED, pxat=math.floor(expires.timestamp() * 1000))
            pipe.delete(*keys[1:])
            await pipe.execute()


def query_key(workspace: UUID, actor: str, query: UUID, part: int = 0) -> str:
    context = json.dumps([str(workspace), actor, str(query)], separators=(",", ":")).encode()
    digest = hashlib.sha256(context).hexdigest()
    return f"accord:similarity:v1:{{{digest}}}:{part}"


async def encrypt_payload(payload: dict[str, object], key: str, wrapper: KeyWrapper) -> bytes:
    data = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()
    sealed = await seal(data, key.encode(), wrapper)
    return json.dumps(
        {
            "ciphertext": base64.b64encode(sealed.ciphertext).decode(),
            "nonce": base64.b64encode(sealed.nonce).decode(),
            "key_id": sealed.key_id,
            "wrapped_key": base64.b64encode(sealed.wrapped_key).decode(),
        },
        separators=(",", ":"),
    ).encode()


async def decrypt_payload(data: bytes, key: str, wrapper: KeyWrapper) -> dict[str, object]:
    if not 1 <= len(data) <= MAX_CACHE_BYTES:
        raise RuntimeError("invalid sealed query size")
    try:
        raw = json.loads(data)
        if not isinstance(raw, dict) or set(raw) != {
            "ciphertext",
            "nonce",
            "key_id",
            "wrapped_key",
        }:
            raise ValueError("invalid sealed query")
        sealed = SealedEvidence(
            base64.b64decode(raw["ciphertext"], validate=True),
            base64.b64decode(raw["nonce"], validate=True),
            raw["key_id"],
            base64.b64decode(raw["wrapped_key"], validate=True),
        )
        result = json.loads(await unseal(sealed, key.encode(), wrapper))
        if not isinstance(result, dict):
            raise ValueError("invalid query payload")
        return result
    except (ValueError, TypeError, KeyError) as exc:
        raise RuntimeError("query storage integrity unavailable") from exc
