"""Provider faults never produce a clean scan or a software wrapping key."""

import base64
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import SecretStr, ValidationError

from accord.personas.photo_contracts import PhotoChange, PhotoRejectedError, PhotoUnavailableError
from accord.personas.photo_scanner import ClamdScanner, definition_receipt
from accord.personas.photo_vault import VaultKeyWrapper
from accord.personas.service import SaveCommand, fingerprint


def version(age: timedelta = timedelta()) -> bytes:
    date = (datetime.now(UTC) - age).strftime("%a %b %d %H:%M:%S %Y")
    return f"ClamAV 1.4.3/12345/{date}\x00".encode("ascii")


def test_stale_or_ambiguous_definitions_are_unavailable() -> None:
    assert definition_receipt(version()).definitions == "12345"
    for response in (b"invalid", version(timedelta(days=3)), version(-timedelta(hours=1))):
        with pytest.raises(PhotoUnavailableError):
            definition_receipt(response)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "verdict,expected",
    [
        (b"stream: OK\x00", None),
        (b"stream: synthetic FOUND\x00", PhotoRejectedError),
        (b"stream: ERROR\x00", PhotoUnavailableError),
        (b"OK\x00", PhotoUnavailableError),
    ],
)
async def test_scanner_requires_exact_complete_verdict(
    monkeypatch: pytest.MonkeyPatch, verdict: bytes, expected: type[Exception] | None
) -> None:
    scanner = ClamdScanner()
    replies = iter((version(), verdict, version()))

    async def command(_command: bytes, _data: bytes | None = None) -> bytes:
        return next(replies)

    monkeypatch.setattr(scanner, "command", command)
    if expected is None:
        assert (await scanner.scan(b"synthetic")).definitions == "12345"
    else:
        with pytest.raises(expected):
            await scanner.scan(b"synthetic")


@pytest.mark.asyncio
async def test_wrapping_requires_derived_nonexportable_persistent_key_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrapper = VaultKeyWrapper(
        "http://127.0.0.1:8200", SecretStr(uuid4().hex), "accord-portraits", development=True
    )
    paths: list[str] = []

    async def reply(path: str, _payload: dict[str, str] | None = None) -> dict[str, object]:
        paths.append(path)
        return {"type": "aes256-gcm96", "derived": False}

    monkeypatch.setattr(wrapper, "request", reply)
    with pytest.raises(PhotoUnavailableError):
        await wrapper.wrap(bytes(32), b"context")
    assert paths == ["keys/accord-portraits"]


@pytest.mark.asyncio
async def test_key_result_and_context_are_validated(monkeypatch: pytest.MonkeyPatch) -> None:
    wrapper = VaultKeyWrapper("https://127.0.0.1:8200", SecretStr(uuid4().hex), "accord-portraits")

    async def reply(path: str, payload: dict[str, str] | None = None) -> dict[str, object]:
        if path.startswith("keys/"):
            return {
                "type": "aes256-gcm96",
                "derived": True,
                "exportable": False,
                "allow_plaintext_backup": False,
                "deletion_allowed": False,
            }
        assert payload and payload["context"] == base64.b64encode(b"context").decode()
        return {
            "ciphertext": "vault:v1:c3ludGhldGlj",
            "plaintext": base64.b64encode(bytes(32)).decode(),
        }

    monkeypatch.setattr(wrapper, "request", reply)
    key_id, wrapped = await wrapper.wrap(bytes(32), b"context")
    assert await wrapper.unwrap(key_id, wrapped, b"context") == bytes(32)
    with pytest.raises(PhotoUnavailableError):
        await wrapper.unwrap("different-key", wrapped, b"context")


def test_photo_intent_and_legacy_replay_contract() -> None:
    with pytest.raises(ValidationError):
        PhotoChange(action="attach")
    with pytest.raises(ValidationError):
        PhotoChange(action="remove", upload_id=uuid4())
    command = SaveCommand.model_validate(
        {
            "request_id": uuid4(),
            "content": {
                "name": "Synthetic",
                "biography": "Fictional",
                "human_contribution": "Illustration",
                "ai_disclosure": "None",
            },
        }
    )
    from pydantic import BaseModel

    from accord.personas.contracts import PersonaDraft

    class Legacy(BaseModel):
        request_id: object
        content: PersonaDraft
        persona_id: object = None
        expected_revision: int = 0

    assert fingerprint(command) == fingerprint(Legacy(**command.model_dump(exclude={"photo"})))
    assert fingerprint(command) != fingerprint(
        command.model_copy(update={"photo": PhotoChange(action="remove")})
    )
