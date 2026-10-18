"""Encrypted, expiring Redis OIDC state and sessions; no process-memory fallback."""

import base64
import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from redis.asyncio import Redis


class BrowserStore:
    def __init__(self, redis: Redis, key: str, context: str) -> None:
        try:
            raw = bytes.fromhex(key)
        except ValueError as exc:
            raise ValueError("session encryption key must be 32-byte hex") from exc
        if len(raw) != 32:
            raise ValueError("session encryption key must be 32-byte hex")
        self.redis, self.cipher, self.context = redis, AESGCM(raw), context

    def address(self, kind: str, handle: str) -> str:
        return f"accord:oidc:{kind}:{handle}"

    async def put(self, kind: str, handle: str, body: dict[str, Any], seconds: int) -> None:
        address = self.address(kind, handle)
        nonce = os.urandom(12)
        associated = f"{self.context}:{address}".encode()
        plaintext = json.dumps(body, separators=(",", ":")).encode()
        ciphertext = nonce + self.cipher.encrypt(nonce, plaintext, associated)
        if not await self.redis.set(
            address, base64.urlsafe_b64encode(ciphertext).decode(), nx=True, ex=seconds
        ):
            raise RuntimeError("identity state could not be stored")

    async def read(self, kind: str, handle: str, *, consume: bool = False) -> dict[str, Any] | None:
        address = self.address(kind, handle)
        encoded = await self.redis.getdel(address) if consume else await self.redis.get(address)
        if encoded is None:
            return None
        raw = base64.urlsafe_b64decode(encoded)
        associated = f"{self.context}:{address}".encode()
        body = json.loads(self.cipher.decrypt(raw[:12], raw[12:], associated))
        if not isinstance(body, dict):
            raise ValueError("identity state is invalid")
        return body

    async def remove(self, handle: str) -> None:
        await self.redis.delete(self.address("session", handle))
