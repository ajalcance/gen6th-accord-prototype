"""AES-GCM envelope encryption with an injected, owner-configured key wrapper.

No default key, environment loader, software KMS or cloud activation. A wrapper failure
propagates and prevents the storage transaction from committing.
"""

import json
import os
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from accord.personas.evidence_contracts import MAX_EVIDENCE_BYTES


class KeyWrapper(Protocol):
    async def wrap(self, key: bytes, context: bytes) -> tuple[str, bytes]:
        """Return a non-secret key version identifier and authenticated wrapped key."""
        ...

    async def unwrap(self, key_id: str, wrapped: bytes, context: bytes) -> bytes:
        """Reject unknown/retired keys and context mismatch; never return a fallback."""
        ...


@dataclass(frozen=True)
class SealedEvidence:
    ciphertext: bytes
    nonce: bytes
    key_id: str
    wrapped_key: bytes


def binding(workspace_id: UUID, version_id: UUID, evidence_id: UUID, digest: str) -> bytes:
    return json.dumps(
        [
            "accord-private-evidence-v1",
            str(workspace_id),
            str(version_id),
            str(evidence_id),
            digest,
        ],
        separators=(",", ":"),
    ).encode("ascii")


async def seal(data: bytes, context: bytes, wrapper: KeyWrapper) -> SealedEvidence:
    if not 1 <= len(data) <= MAX_EVIDENCE_BYTES:
        raise ValueError("evidence size is outside the allowed range")
    key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    key_id, wrapped = await wrapper.wrap(key, context)
    if not key_id or len(key_id) > 120 or not wrapped or len(wrapped) > 4096:
        raise ValueError("invalid wrapping result")
    return SealedEvidence(AESGCM(key).encrypt(nonce, data, context), nonce, key_id, wrapped)


async def unseal(sealed: SealedEvidence, context: bytes, wrapper: KeyWrapper) -> bytes:
    if len(sealed.nonce) != 12 or not 17 <= len(sealed.ciphertext) <= MAX_EVIDENCE_BYTES + 16:
        raise ValueError("invalid encrypted evidence")
    key = await wrapper.unwrap(sealed.key_id, sealed.wrapped_key, context)
    if len(key) != 32:
        raise ValueError("invalid evidence key")
    return AESGCM(key).decrypt(sealed.nonce, sealed.ciphertext, context)
