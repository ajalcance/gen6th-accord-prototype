"""PostgreSQL behavior: encrypted intake, exact replay and immutable version history."""

import base64
import hashlib
import io
from collections.abc import AsyncIterator
from datetime import datetime, tzinfo
from typing import Self
from uuid import UUID, uuid4

import pytest
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.models import Persona, Version
from accord.personas.photo_contracts import PhotoChange, PhotoRejectedError, PhotoUpload
from accord.personas.photo_decoder import Media, decode_pixels
from accord.personas.photo_inspector import InspectedPhoto
from accord.personas.photo_intake import intake
from accord.personas.photo_models import Portrait, PortraitPayload, VersionPortrait
from accord.personas.photo_reads import thumbnail
from accord.personas.photo_scanner import ScanReceipt
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import save
from personas.conftest import command


class FixtureWrapper:
    def __init__(self) -> None:
        self.keys: dict[bytes, tuple[bytes, bytes]] = {}

    async def wrap(self, key: bytes, context: bytes) -> tuple[str, bytes]:
        handle = uuid4().bytes
        self.keys[handle] = (key, context)
        return "synthetic-test-wrapper", handle

    async def unwrap(self, key_id: str, wrapped: bytes, context: bytes) -> bytes:
        assert key_id == "synthetic-test-wrapper"
        key, actual = self.keys[wrapped]
        assert actual == context
        return key


class FixtureInspector:
    async def inspect(self, data: bytes, media: Media) -> InspectedPhoto:
        # Real Pillow pixels, synthetic scanner only. This is not provider acceptance.
        pixels = decode_pixels(data, media)
        receipt = ScanReceipt("synthetic-scanner", "synthetic-definitions")
        return InspectedPhoto(pixels, receipt, receipt, hashlib.sha256(data).hexdigest(), receipt)


def upload() -> PhotoUpload:
    output = io.BytesIO()
    Image.new("RGB", (32, 16), (22, 40, 60)).save(output, format="PNG")
    data = output.getvalue()
    return PhotoUpload(
        request_id=uuid4(),
        media_type="image/png",
        byte_length=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        data=base64.b64encode(data).decode(),
    )


async def body(value: PhotoUpload) -> AsyncIterator[bytes]:
    yield value.model_dump_json().encode()


async def staged(
    session: AsyncSession, workspace: UUID, wrapper: KeyWrapper, owner: str = "creator-a"
) -> tuple[PhotoUpload, UUID]:
    value = upload()
    receipt = await intake(session, workspace, owner, body(value), FixtureInspector(), wrapper)
    return value, receipt.id


@pytest.mark.asyncio
async def test_portrait_replay_encrypts_and_rejects_changed_intent(
    session: AsyncSession,
    workspace: UUID,
) -> None:
    wrapper = FixtureWrapper()
    value, photo_id = await staged(session, workspace, wrapper)
    replay = await intake(session, workspace, "creator-a", body(value), FixtureInspector(), wrapper)
    assert replay.id == photo_id and len(wrapper.keys) == 3
    payloads = (await session.scalars(select(PortraitPayload))).all()
    assert len(payloads) == 2
    original = base64.b64decode(value.data)
    assert all(original not in payload.ciphertext for payload in payloads)
    await session.rollback()
    changed = value.model_copy(update={"media_type": "image/jpeg"})
    with pytest.raises(ConflictError):
        await intake(session, workspace, "creator-a", body(changed), FixtureInspector(), wrapper)


@pytest.mark.asyncio
async def test_photo_add_keep_replace_remove_preserves_immutable_history(
    session: AsyncSession,
    workspace: UUID,
) -> None:
    wrapper = FixtureWrapper()
    _, first = await staged(session, workspace, wrapper)
    version = await save(
        session,
        workspace,
        "creator-a",
        command(
            photo=PhotoChange(action="attach", upload_id=first),
        ),
    )
    kept = await save(
        session,
        workspace,
        "creator-a",
        command(
            persona_id=version.persona_id,
            expected_revision=1,
        ),
    )
    _, second = await staged(session, workspace, wrapper)
    replaced = await save(
        session,
        workspace,
        "creator-a",
        command(
            persona_id=version.persona_id,
            expected_revision=2,
            photo=PhotoChange(action="attach", upload_id=second),
        ),
    )
    removed = await save(
        session,
        workspace,
        "creator-a",
        command(
            persona_id=version.persona_id,
            expected_revision=3,
            photo=PhotoChange(action="remove"),
        ),
    )
    for item in (version, kept, replaced):
        image = await thumbnail(session, workspace, "viewer", item.version_id, wrapper)
        assert image and image.startswith(b"\x89PNG\r\n\x1a\n")
    assert await thumbnail(session, workspace, "viewer", removed.version_id, wrapper) is None
    assert await session.scalar(select(func.count()).select_from(PortraitPayload)) == 4


@pytest.mark.asyncio
async def test_other_owner_attachment_rolls_back_all_version_changes(
    session: AsyncSession,
    workspace: UUID,
) -> None:
    wrapper = FixtureWrapper()
    _, photo_id = await staged(session, workspace, wrapper, "creator-b")
    with pytest.raises(AccessDeniedError):
        await save(
            session,
            workspace,
            "creator-a",
            command(
                photo=PhotoChange(action="attach", upload_id=photo_id),
            ),
        )
    assert await session.scalar(select(func.count()).select_from(VersionPortrait)) == 0
    assert await session.scalar(select(func.count()).select_from(Persona)) == 0
    assert await session.scalar(select(func.count()).select_from(Version)) == 0


@pytest.mark.asyncio
async def test_membership_denial_precedes_consumption_and_invalid_input_is_not_stored(
    session: AsyncSession,
    workspace: UUID,
) -> None:
    consumed = False

    async def unread() -> AsyncIterator[bytes]:
        nonlocal consumed
        consumed = True
        yield b"invalid"

    with pytest.raises(AccessDeniedError):
        await intake(session, workspace, "viewer", unread(), FixtureInspector(), FixtureWrapper())
    assert not consumed
    with pytest.raises(PhotoRejectedError):
        await intake(
            session, workspace, "creator-a", unread(), FixtureInspector(), FixtureWrapper()
        )
    assert await session.scalar(select(func.count()).select_from(Portrait)) == 0


@pytest.mark.asyncio
async def test_expired_stage_cannot_attach_but_existing_history_is_kept(
    session: AsyncSession,
    workspace: UUID,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrapper = FixtureWrapper()
    _, photo_id = await staged(session, workspace, wrapper)
    first = await save(
        session,
        workspace,
        "creator-a",
        command(
            photo=PhotoChange(action="attach", upload_id=photo_id),
        ),
    )

    class Future(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> Self:
            return cls.fromtimestamp(datetime.now(tz).timestamp() + 172800, tz)

    monkeypatch.setattr("accord.personas.photo_binding.datetime", Future)
    with pytest.raises(ConflictError):
        await save(
            session,
            workspace,
            "creator-a",
            command(
                photo=PhotoChange(action="attach", upload_id=photo_id),
            ),
        )
    kept = await save(
        session,
        workspace,
        "creator-a",
        command(
            persona_id=first.persona_id,
            expected_revision=1,
        ),
    )
    assert await thumbnail(session, workspace, "viewer", kept.version_id, wrapper)


@pytest.mark.asyncio
async def test_key_outage_leaves_no_portrait_or_payload(
    session: AsyncSession,
    workspace: UUID,
) -> None:
    class Unavailable(FixtureWrapper):
        async def wrap(self, key: bytes, context: bytes) -> tuple[str, bytes]:
            raise RuntimeError("synthetic key outage")

    with pytest.raises(RuntimeError, match="outage"):
        await staged(session, workspace, Unavailable())
    assert await session.scalar(select(func.count()).select_from(Portrait)) == 0
    assert await session.scalar(select(func.count()).select_from(PortraitPayload)) == 0
