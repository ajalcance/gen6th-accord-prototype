"""KMS context/CRC transport and explicit retained key routing; no key is installed."""

import base64
from unittest.mock import AsyncMock

import pytest

from accord.personas.evidence_crypto import seal, unseal
from accord.personas.google_keys import GoogleKeyWrapper, RetainedKeyWrapper, key_alias
from accord.personas.passport_google import crc32c
from personas.runtime_fixtures import config


@pytest.mark.asyncio
async def test_kms_wrap_and_unwrap_bind_context_and_preserve_small_storage_identifiers() -> None:
    transport = AsyncMock()
    version = config().wrapping_version
    key, context, ciphertext = b"k" * 32, b"specific-context", b"synthetic-wrapped-data"
    transport.post.side_effect = [
        {
            "name": version,
            "verifiedPlaintextCrc32c": True,
            "verifiedAdditionalAuthenticatedDataCrc32c": True,
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "ciphertextCrc32c": str(crc32c(ciphertext)),
        },
        {"plaintext": base64.b64encode(key).decode(), "plaintextCrc32c": str(crc32c(key))},
    ]
    wrapper = GoogleKeyWrapper(version, (), transport)
    identity, encrypted = await wrapper.wrap(key, context)
    assert identity == key_alias(version) and len(identity) <= 120
    assert await wrapper.unwrap(identity, encrypted, context) == key
    request = transport.post.call_args_list[0].args[2]
    assert request["additionalAuthenticatedData"] == base64.b64encode(context).decode()
    assert request["plaintextCrc32c"] == str(crc32c(key))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "changes",
    [
        {"name": "other"},
        {"verifiedPlaintextCrc32c": False},
        {"verifiedAdditionalAuthenticatedDataCrc32c": False},
        {"ciphertextCrc32c": "0"},
        {"ciphertext": "!"},
        {"ciphertextCrc32c": True},
    ],
)
async def test_corrupt_kms_wrapping_never_commits_a_key(changes: dict[str, object]) -> None:
    transport = AsyncMock()
    version = config().wrapping_version
    transport.post.return_value = {
        "name": version,
        "verifiedPlaintextCrc32c": True,
        "verifiedAdditionalAuthenticatedDataCrc32c": True,
        "ciphertext": "eA==",
        "ciphertextCrc32c": str(crc32c(b"x")),
        **changes,
    }
    with pytest.raises((RuntimeError, ValueError)):
        await GoogleKeyWrapper(version, (), transport).wrap(b"k" * 32, b"context")


@pytest.mark.asyncio
async def test_unknown_kms_keys_do_not_route_to_legacy_and_context_stays_authenticated() -> None:
    current, legacy = AsyncMock(), AsyncMock()
    wrapper = RetainedKeyWrapper(current, legacy)
    current.unwrap.side_effect = RuntimeError("unknown retained key")
    with pytest.raises(RuntimeError):
        await wrapper.unwrap("gcp-kms-v1:" + "c" * 64, b"wrapped", b"context")
    legacy.unwrap.assert_not_called()
    await wrapper.unwrap("reviewed-legacy", b"wrapped", b"context")
    legacy.unwrap.assert_awaited_once_with("reviewed-legacy", b"wrapped", b"context")


@pytest.mark.asyncio
async def test_actual_aes_gcm_envelope_rejects_changed_context_with_kms_transport() -> None:
    material: dict[bytes, bytes] = {}
    transport = AsyncMock()
    version = config().wrapping_version

    async def respond(url: str, project: str, request: dict[str, str]) -> dict[str, object]:
        context = base64.b64decode(request["additionalAuthenticatedData"])
        if url.endswith(":encrypt"):
            material[context] = base64.b64decode(request["plaintext"])
            return {
                "name": version,
                "verifiedPlaintextCrc32c": True,
                "verifiedAdditionalAuthenticatedDataCrc32c": True,
                "ciphertext": "eA==",
                "ciphertextCrc32c": str(crc32c(b"x")),
            }
        key = material[context]
        return {"plaintext": base64.b64encode(key).decode(), "plaintextCrc32c": str(crc32c(key))}

    transport.post.side_effect = respond
    wrapper = GoogleKeyWrapper(version, (), transport)
    packet = await seal(b"private-evidence", b"original", wrapper)
    assert await unseal(packet, b"original", wrapper) == b"private-evidence"
    with pytest.raises(KeyError):
        await unseal(packet, b"changed", wrapper)
