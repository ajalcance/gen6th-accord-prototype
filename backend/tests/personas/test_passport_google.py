"""Synthetic KMS transport and in-memory signatures; no workload credential loading."""

import base64
from unittest.mock import AsyncMock, Mock

import pytest

from accord.personas.passport_google import GooglePassportSigner, crc32c

KEY = (
    "projects/fixture-project/locations/global/keyRings/passport/"
    "cryptoKeys/signing/cryptoKeyVersions/1"
)


def response() -> dict[str, object]:
    signature = bytes(range(64))
    return {
        "name": KEY,
        "verifiedDataCrc32c": True,
        "signature": base64.b64encode(signature).decode(),
        "signatureCrc32c": str(crc32c(signature)),
    }


@pytest.mark.asyncio
async def test_kms_signs_domain_message_with_integrity_checks_and_immutable_resource() -> None:
    transport = Mock(post=AsyncMock(return_value=response()))
    signer = GooglePassportSigner(KEY, transport)
    data = b"domain-separated synthetic payload"
    assert await signer.sign(data) == bytes(range(64))
    args = transport.post.await_args.args
    assert args[:2] == (
        f"https://cloudkms.googleapis.com/v1/{KEY}:asymmetricSign",
        "fixture-project",
    )
    assert base64.b64decode(args[2]["data"]) == data and args[2]["dataCrc32c"] == str(crc32c(data))
    assert "digest" not in args[2]
    assert crc32c(b"123456789") == 0xE3069283


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field,value",
    [
        ("name", KEY + "2"),
        ("verifiedDataCrc32c", False),
        ("verifiedDataCrc32c", 1),
        ("signatureCrc32c", "0"),
        ("signatureCrc32c", 1),
        ("signature", "malformed"),
    ],
)
async def test_incomplete_or_corrupted_kms_result_is_unavailable(field: str, value: object) -> None:
    transport = Mock(post=AsyncMock(return_value={**response(), field: value}))
    with pytest.raises(RuntimeError):
        await GooglePassportSigner(KEY, transport).sign(b"synthetic")


@pytest.mark.parametrize(
    "key",
    [
        KEY.replace("/1", "/latest"),
        KEY.replace("/1", "/0"),
        "https://arbitrary.test/key",
        KEY + "/suffix",
    ],
)
def test_kms_config_rejects_alias_or_arbitrary_endpoint(key: str) -> None:
    with pytest.raises(ValueError):
        GooglePassportSigner(key, Mock())
