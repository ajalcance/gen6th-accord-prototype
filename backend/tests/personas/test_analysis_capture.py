"""Actual Pillow pixels, hostile worker output and fail-closed third safety scan."""

import io
import json
from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from PIL import Image
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.capture_contracts import CaptureMetadata, CaptureQuery, ReferenceChange
from accord.personas.capture_models import PortraitCapture
from accord.personas.capture_reads import capture_profile
from accord.personas.capture_storage import capture_context, store_capture, validate_capture
from accord.personas.evidence_crypto import SealedEvidence, unseal
from accord.personas.photo_contracts import PhotoRejectedError, PhotoUnavailableError
from accord.personas.photo_decoder import DecodedPhoto, decode_pixels, decode_worker_result
from accord.personas.photo_inspector import InspectedPhoto, PillowClamdInspector
from accord.personas.photo_models import Portrait
from accord.personas.photo_scanner import ScanReceipt
from accord.personas.repository import AccessDeniedError
from personas.test_photo_decoder import image_bytes
from personas.test_photo_storage import FixtureWrapper


def inspected() -> InspectedPhoto:
    scan = ScanReceipt("synthetic-scanner", "synthetic-definitions")
    return InspectedPhoto(
        decode_pixels(image_bytes(width=2048, height=1024), "image/png"), scan, scan, "a" * 64, scan
    )


def test_analysis_is_independent_metadata_free_and_never_upscaled() -> None:
    value = inspected().pixels
    assert (value.width, value.height) == (320, 160)
    assert (value.source_width, value.source_height) == (2048, 1024)
    assert (value.analysis_width, value.analysis_height) == (1024, 512)
    assert value.analysis != value.thumbnail
    with Image.open(io.BytesIO(value.analysis)) as image:
        assert image.mode == "RGBA" and image.size == (1024, 512) and not image.info
    small = decode_pixels(image_bytes(width=32, height=16), "image/png")
    assert (small.analysis_width, small.analysis_height) == (32, 16)


def test_orientation_is_applied_and_preserved_as_source_provenance() -> None:
    output = io.BytesIO()
    image = Image.new("RGB", (600, 300))
    exif = image.getexif()
    exif[274] = 6
    image.save(output, format="JPEG", exif=exif)
    result = decode_pixels(output.getvalue(), "image/jpeg")
    assert (result.source_width, result.source_height, result.orientation) == (600, 300, 6)
    assert (result.analysis_width, result.analysis_height) == (300, 600)
    assert (result.width, result.height) == (160, 320)
    with Image.open(io.BytesIO(result.analysis)) as clean:
        assert not clean.info and not clean.getexif()


@pytest.mark.parametrize(
    "change", [{0: 2.0}, {1: True}, {3: 4097}, {5: 9}, {6: 1025}, {8: 1}, {9: ""}]
)
def test_invalid_worker_protocol_cannot_create_a_capture(change: dict[int, object]) -> None:
    result = inspected().pixels
    header: list[object] = [2, 320, 160, 2048, 1024, 1, 1024, 512, len(result.thumbnail), "12.3.0"]
    for index, value in change.items():
        header[index] = value
    with pytest.raises(RuntimeError):
        decode_worker_result(json.dumps(header).encode(), result.thumbnail + result.analysis)


@pytest.mark.asyncio
async def test_all_three_parts_must_pass_inspection(monkeypatch: pytest.MonkeyPatch) -> None:
    pixels = inspected().pixels
    calls: list[bytes] = []

    async def decode(_data: bytes, _media: object) -> DecodedPhoto:
        return pixels

    class Scanner:
        async def scan(self, data: bytes) -> ScanReceipt:
            calls.append(data)
            if data == pixels.analysis:
                raise PhotoRejectedError("synthetic analysis rejection")
            return ScanReceipt("synthetic", "fresh")

    monkeypatch.setattr("accord.personas.photo_inspector.decode_photo", decode)
    with pytest.raises(PhotoRejectedError):
        await PillowClamdInspector(Scanner()).inspect(b"source", "image/png")
    assert calls == [b"source", pixels.thumbnail, pixels.analysis]
    with pytest.raises(PhotoUnavailableError):
        validate_capture(replace(inspected(), analysis_scan=None))


def test_wrapping_context_binds_source_processing_dimensions_and_scanner() -> None:
    row = Portrait(id=uuid4(), workspace_id=uuid4(), sha256="a" * 64, recorded_at=datetime.now(UTC))
    value = inspected()
    context = capture_context(row, "b" * 64, value)
    changed = replace(value, pixels=replace(value.pixels, orientation=6))
    assert context != capture_context(row, "b" * 64, changed)
    assert b"rgba-png-1024-v1" in context and b"synthetic-definitions" in context


@pytest.mark.parametrize(
    "payload", [{}, {"upload_id": uuid4(), "version_id": uuid4()}, {"actor_ref": "forged"}]
)
def test_capture_subject_must_be_explicit_and_exclusive(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        CaptureQuery.model_validate(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "keep", "upload_ids": [uuid4()]},
        {"action": "replace", "upload_ids": [uuid4()] * 2},
        {"action": "replace", "upload_ids": [uuid4() for _ in range(9)]},
    ],
)
def test_reference_set_is_bounded_explicit_and_unique(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ReferenceChange.model_validate(payload)
    assert ReferenceChange(action="replace").upload_ids == ()


def test_capture_contract_rejects_naive_timestamp_and_excess_pixels() -> None:
    payload = dict(
        portrait_id=uuid4(),
        source_sha256="a" * 64,
        source_width=32,
        source_height=16,
        orientation=1,
        width=32,
        height=16,
        sha256="b" * 64,
        recipe="rgba-png-1024-v1",
        decoder_version="12.3.0",
        recorded_at=datetime.now(UTC),
    )
    assert CaptureMetadata.model_validate(payload).width == 32
    for change in (
        {"recorded_at": "2026-10-05T12:00:00"},
        {"source_width": 4096, "source_height": 4096},
    ):
        with pytest.raises(ValidationError):
            CaptureMetadata.model_validate(payload | change)


@pytest.mark.asyncio
async def test_encrypted_analysis_is_bound_to_its_exact_capture_context() -> None:
    value, wrapper = inspected(), FixtureWrapper()
    photo = Portrait(
        id=uuid4(), workspace_id=uuid4(), sha256="a" * 64, recorded_at=datetime.now(UTC)
    )
    async with AsyncSession() as session:
        await store_capture(session, photo, value, wrapper)
        row = next(item for item in session.new if isinstance(item, PortraitCapture))
        envelope = SealedEvidence(row.ciphertext, row.nonce, row.key_id, row.wrapped_key)
        context = capture_context(photo, row.sha256, value)
        assert await unseal(envelope, context, wrapper) == value.pixels.analysis
        assert row.ciphertext != value.pixels.analysis
        with pytest.raises(AssertionError):
            await unseal(envelope, context + b"changed", wrapper)


@pytest.mark.asyncio
async def test_capture_authorization_precedes_subject_or_metadata_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deny = AsyncMock(side_effect=AccessDeniedError("synthetic denial"))
    read = AsyncMock()
    monkeypatch.setattr("accord.personas.capture_reads.authorize", deny)
    monkeypatch.setattr("accord.personas.capture_reads.capture_subject", read)
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await capture_profile(
                session, uuid4(), "synthetic-human", CaptureQuery(upload_id=uuid4())
            )
    read.assert_not_awaited()
