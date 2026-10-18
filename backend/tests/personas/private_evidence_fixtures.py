"""Ephemeral test-only key wrapper and content inspector. Neither is production wiring."""

import hashlib
import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import UUID, uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from accord.personas.evidence_contracts import EvidenceIntent, Inspection

DATA = b"Fictional creator evidence for an internal test."


class EphemeralTestWrapper:
    def __init__(self) -> None:
        self.key = AESGCM.generate_key(bit_length=256)

    async def wrap(self, key: bytes, context: bytes) -> tuple[str, bytes]:
        nonce = os.urandom(12)
        return "test-only-ephemeral", nonce + AESGCM(self.key).encrypt(nonce, key, context)

    async def unwrap(self, key_id: str, wrapped: bytes, context: bytes) -> bytes:
        if key_id != "test-only-ephemeral":
            raise ValueError("unknown key")
        return AESGCM(self.key).decrypt(wrapped[:12], wrapped[12:], context)


class FixtureContentInspector:
    async def inspect(self, data: bytes) -> Inspection:
        return Inspection(
            sha256=hashlib.sha256(data).hexdigest(),
            byte_length=len(data),
            detected_type="text/plain",
            verdict="clean",
            engine="test-only-no-malware-scanner",
            definitions="test-fixture",
            inspected_at=datetime.now(UTC),
        )


def intent(version_id: UUID, data: bytes = DATA, /, **changes: object) -> EvidenceIntent:
    return EvidenceIntent.model_validate(
        {
            "request_id": uuid4(),
            "version_id": version_id,
            "media_type": "text/plain",
            "byte_length": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            **changes,
        }
    )


async def chunks(data: bytes = DATA) -> AsyncGenerator[bytes, None]:
    yield data[:7]
    yield data[7:]
