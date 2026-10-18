"""Authorize before reading bounded JSON; inspect and encrypt before atomic durable intake."""

import asyncio
import base64
import binascii
import hashlib
from collections.abc import AsyncIterable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.capture_storage import store_capture, validate_capture
from accord.personas.evidence_crypto import KeyWrapper, seal
from accord.personas.photo_contracts import (
    PhotoReceipt,
    PhotoRejectedError,
    PhotoUnavailableError,
    PhotoUpload,
)
from accord.personas.photo_decoder import MAX_INPUT, MAX_OUTPUT
from accord.personas.photo_inspector import InspectedPhoto, PhotoInspector
from accord.personas.photo_models import Portrait, PortraitPayload
from accord.personas.photo_storage import photo_context, photo_event, photo_receipt
from accord.personas.repository import ConflictError, authorize
from accord.personas.service import fingerprint
from accord.personas.transactions import tracked_transaction


async def read_photo_intent(body: AsyncIterable[bytes]) -> tuple[PhotoUpload, bytes]:
    raw = bytearray()
    async with asyncio.timeout(30):
        async for chunk in body:
            if len(chunk) > 13982040 - len(raw):
                raise PhotoRejectedError("photo request exceeds size limit")
            raw.extend(chunk)
    try:
        command = PhotoUpload.model_validate_json(raw)
        data = base64.b64decode(command.data, validate=True)
    except (ValidationError, ValueError, binascii.Error) as exc:
        raise PhotoRejectedError("invalid photo request") from exc
    if len(data) != command.byte_length or hashlib.sha256(data).hexdigest() != command.sha256:
        raise PhotoRejectedError("photo content mismatch")
    return command, data


async def intake(
    session: AsyncSession,
    workspace: UUID,
    actor: str,
    body: AsyncIterable[bytes],
    inspector: PhotoInspector | None,
    wrapper: KeyWrapper | None,
) -> PhotoReceipt:
    request = uuid4()
    async with tracked_transaction(session, workspace, actor, request):
        await authorize(session, workspace, actor, write=True)
        if inspector is None or wrapper is None:
            raise PhotoUnavailableError("photo providers unavailable")
        command, data = await read_photo_intent(body)
        digest = fingerprint(command.model_copy(update={"data": ""}))
        existing = await session.scalar(
            select(Portrait).where(
                Portrait.workspace_id == workspace,
                Portrait.owner_ref == actor,
                Portrait.request_id == command.request_id,
            )
        )
        if existing is not None:
            if existing.fingerprint != digest:
                raise ConflictError("photo request intent changed")
            return photo_receipt(existing)
        result = await inspector.inspect(data, command.media_type)
        validate_capture(result)
        pixels = result.pixels
        if (
            result.digest != command.sha256
            or not 1 <= len(data) <= MAX_INPUT
            or not 1 <= len(pixels.thumbnail) <= MAX_OUTPUT
            or not 1 <= pixels.width <= 320
            or not 1 <= pixels.height <= 320
            or not pixels.thumbnail.startswith(b"\x89PNG\r\n\x1a\n")
            or not result.original_scan.engine
            or not result.original_scan.definitions
            or not result.derivative_scan.engine
            or not result.derivative_scan.definitions
        ):
            raise PhotoUnavailableError("invalid inspection result")
        row = await store_inspected(session, workspace, actor, command, digest, result, wrapper)
        return photo_receipt(row)


async def store_inspected(
    session: AsyncSession,
    workspace: UUID,
    actor: str,
    command: PhotoUpload,
    intent_digest: str,
    inspected: InspectedPhoto,
    wrapper: KeyWrapper,
) -> Portrait:
    photo_id, now = uuid4(), datetime.now(UTC)
    original = base64.b64decode(command.data, validate=True)
    thumbnail = inspected.pixels.thumbnail
    thumb_digest = hashlib.sha256(thumbnail).hexdigest()
    row = Portrait(
        id=photo_id,
        workspace_id=workspace,
        owner_ref=actor,
        request_id=command.request_id,
        fingerprint=intent_digest,
        media_type=command.media_type,
        sha256=command.sha256,
        thumbnail_sha256=thumb_digest,
        byte_length=command.byte_length,
        width=inspected.pixels.width,
        height=inspected.pixels.height,
        engine=inspected.original_scan.engine,
        definitions=inspected.original_scan.definitions,
        derivative_definitions=inspected.derivative_scan.definitions,
        recorded_at=now,
        expires_at=now + timedelta(hours=24),
    )
    encrypted = await encrypt_parts(row, original, thumbnail, wrapper)
    session.add(row)
    await session.flush()
    session.add_all(encrypted)
    await store_capture(session, row, inspected, wrapper)
    for action in ("persona.portrait_uploaded", "persona.portrait_inspected"):
        session.add(photo_event(action, workspace, actor, photo_id, command.request_id))
    await session.flush()
    return row


async def encrypt_parts(
    row: Portrait,
    original: bytes,
    thumbnail: bytes,
    wrapper: KeyWrapper,
) -> list[PortraitPayload]:
    encrypted: list[PortraitPayload] = []
    for part, data, digest in (
        ("original", original, row.sha256),
        ("thumbnail", thumbnail, row.thumbnail_sha256),
    ):
        sealed = await seal(data, photo_context(row.workspace_id, row.id, part, digest), wrapper)
        encrypted.append(
            PortraitPayload(
                workspace_id=row.workspace_id,
                portrait_id=row.id,
                part=part,
                ciphertext=sealed.ciphertext,
                nonce=sealed.nonce,
                key_id=sealed.key_id,
                wrapped_key=sealed.wrapped_key,
            )
        )
    return encrypted
