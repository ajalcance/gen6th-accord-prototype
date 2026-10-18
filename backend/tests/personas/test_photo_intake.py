"""Bounded JSON contracts reject mismatches before any durable write."""

import base64
import hashlib
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest

from accord.personas.photo_contracts import PhotoRejectedError, PhotoUpload
from accord.personas.photo_intake import read_photo_intent


async def bytes_body(data: bytes) -> AsyncIterator[bytes]:
    for start in range(0, len(data), 65536):
        yield data[start : start + 65536]


def upload(data: bytes = b"synthetic") -> PhotoUpload:
    return PhotoUpload(
        request_id=uuid4(),
        media_type="image/png",
        byte_length=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        data=base64.b64encode(data).decode(),
    )


@pytest.mark.asyncio
async def test_exact_bytes_are_bound_to_declared_upload() -> None:
    value = upload()
    result, data = await read_photo_intent(bytes_body(value.model_dump_json().encode()))
    assert result == value and data == b"synthetic"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change",
    [
        {"byte_length": 1},
        {"sha256": "0" * 64},
        {"data": "not-base64"},
        {"media_type": "image/svg+xml"},
        {"owner_ref": "forged"},
    ],
)
async def test_mismatch_or_attribution_is_rejected(change: dict[str, object]) -> None:
    import json

    value = upload().model_dump(mode="json") | change
    with pytest.raises(PhotoRejectedError):
        await read_photo_intent(bytes_body(json.dumps(value).encode()))


@pytest.mark.asyncio
async def test_oversized_chunk_is_rejected_before_accumulation() -> None:
    async def excessive() -> AsyncIterator[bytes]:
        yield b"x" * 13982041
        raise AssertionError("reader must stop at the first oversized chunk")

    with pytest.raises(PhotoRejectedError, match="size"):
        await read_photo_intent(excessive())
