"""Pure boundary and real encryption tests; no database or scanner substitution claim."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from cryptography.exceptions import InvalidTag
from pydantic import ValidationError

from accord.personas.evidence_contracts import MAX_EVIDENCE_BYTES, effective_state
from accord.personas.evidence_crypto import binding, seal, unseal
from accord.personas.evidence_service import collect
from personas.private_evidence_fixtures import DATA, EphemeralTestWrapper, chunks, intent


async def test_encryption_roundtrip_and_fresh_keys_nonces() -> None:
    wrapper = EphemeralTestWrapper()
    context = binding(uuid4(), uuid4(), uuid4(), "a" * 64)
    first = await seal(DATA, context, wrapper)
    second = await seal(DATA, context, wrapper)
    assert DATA not in first.ciphertext and first != second
    assert first.nonce != second.nonce and first.wrapped_key != second.wrapped_key
    assert await unseal(first, context, wrapper) == DATA


@pytest.mark.parametrize("change", ["ciphertext", "nonce", "wrapped_key", "context", "key"])
async def test_tampering_and_context_substitution_fail_closed(change: str) -> None:
    wrapper = EphemeralTestWrapper()
    context = binding(uuid4(), uuid4(), uuid4(), "b" * 64)
    encrypted = await seal(DATA, context, wrapper)
    if change in {"ciphertext", "nonce", "wrapped_key"}:
        value = getattr(encrypted, change)
        encrypted = replace(encrypted, **{change: bytes([value[0] ^ 1]) + value[1:]})
    if change == "context":
        context += b"different workspace"
    if change == "key":
        wrapper = EphemeralTestWrapper()
    with pytest.raises(InvalidTag):
        await unseal(encrypted, context, wrapper)


async def test_chunked_intake_verifies_size_and_digest() -> None:
    expected = intent(uuid4())
    assert await collect(chunks(), expected) == DATA
    for data in (DATA[:-1], DATA + b"extra", DATA.upper()):
        with pytest.raises(ValueError):
            await collect(chunks(data), expected)


@pytest.mark.parametrize(
    "changes",
    [
        {"byte_length": 0},
        {"byte_length": MAX_EVIDENCE_BYTES + 1},
        {"byte_length": True},
        {"sha256": "unknown"},
        {"media_type": "image/svg+xml"},
        {"owner_ref": "creator"},
        {"path": "supplied-path"},
        {"verdict": "clean"},
    ],
)
def test_intent_rejects_unsafe_or_authority_fields(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        intent(uuid4(), **changes)


def test_expiry_dominates_a_clean_inspection() -> None:
    now = datetime.now(UTC)
    assert effective_state(now, now, "clean") == "expired"
    assert effective_state(now + timedelta(seconds=1), now, None) == "quarantined"
    assert effective_state(now + timedelta(seconds=1), now, "rejected") == "rejected"


async def test_missing_key_provider_does_not_store_plaintext() -> None:
    class UnavailableWrapper(EphemeralTestWrapper):
        async def wrap(self, key: bytes, context: bytes) -> tuple[str, bytes]:
            raise ConnectionError("key provider unavailable")

    with pytest.raises(ConnectionError):
        await seal(DATA, b"context", UnavailableWrapper())
