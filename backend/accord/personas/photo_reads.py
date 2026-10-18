"""Only an authorized version's metadata-free thumbnail can leave the server."""

import hashlib
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.capture_models import VersionReference
from accord.personas.evidence_crypto import KeyWrapper, SealedEvidence, unseal
from accord.personas.models import Version
from accord.personas.photo_contracts import PhotoUnavailableError
from accord.personas.photo_models import Portrait, PortraitPayload, VersionPortrait
from accord.personas.photo_storage import photo_context, photo_event
from accord.personas.repository import AccessDeniedError, authorize
from accord.personas.transactions import tracked_transaction


async def thumbnail(
    session: AsyncSession,
    workspace: UUID,
    actor: str,
    version_id: UUID,
    wrapper: KeyWrapper | None,
) -> bytes | None:
    async with tracked_transaction(session, workspace, actor, uuid4()):
        await authorize(session, workspace, actor, write=False)
        version = await session.scalar(
            select(Version.id).where(
                Version.workspace_id == workspace,
                Version.id == version_id,
            )
        )
        if version is None:
            raise AccessDeniedError("version access denied")
        photo = await session.scalar(
            select(Portrait)
            .join(VersionPortrait, VersionPortrait.portrait_id == Portrait.id)
            .where(
                VersionPortrait.workspace_id == workspace,
                Portrait.workspace_id == workspace,
                VersionPortrait.version_id == version_id,
            )
        )
        if photo is None:
            session.add(photo_event("persona.portrait_read", workspace, actor, version_id, uuid4()))
            return None
        if wrapper is None:
            raise PhotoUnavailableError("photo key provider unavailable")
        payload = await session.scalar(
            select(PortraitPayload).where(
                PortraitPayload.workspace_id == workspace,
                PortraitPayload.portrait_id == photo.id,
                PortraitPayload.part == "thumbnail",
            )
        )
        if payload is None:
            raise PhotoUnavailableError("portrait payload unavailable")
        data = await decrypted_thumbnail(payload, photo, wrapper)
        session.add(photo_event("persona.portrait_read", workspace, actor, photo.id, uuid4()))
    return data


async def decrypted_thumbnail(
    payload: PortraitPayload,
    photo: Portrait,
    wrapper: KeyWrapper,
) -> bytes:
    data = await unseal(
        SealedEvidence(payload.ciphertext, payload.nonce, payload.key_id, payload.wrapped_key),
        photo_context(photo.workspace_id, photo.id, "thumbnail", photo.thumbnail_sha256),
        wrapper,
    )
    if (
        len(data) > 1048576
        or hashlib.sha256(data).hexdigest() != photo.thumbnail_sha256
        or not data.startswith(b"\x89PNG\r\n\x1a\n")
    ):
        raise PhotoUnavailableError("portrait payload integrity failed")
    return data


async def reference_thumbnail(
    session: AsyncSession,
    workspace: UUID,
    actor: str,
    version_id: UUID,
    portrait_id: UUID,
    wrapper: KeyWrapper | None,
) -> bytes:
    async with tracked_transaction(session, workspace, actor, uuid4()):
        await authorize(session, workspace, actor, write=False)
        photo = await session.scalar(
            select(Portrait)
            .join(
                VersionReference,
                (VersionReference.portrait_id == Portrait.id)
                & (VersionReference.workspace_id == Portrait.workspace_id),
            )
            .where(
                VersionReference.version_id == version_id,
                VersionReference.portrait_id == portrait_id,
                VersionReference.workspace_id == workspace,
                Portrait.workspace_id == workspace,
            )
        )
        if photo is None:
            raise AccessDeniedError("reference thumbnail access denied")
        if wrapper is None:
            raise PhotoUnavailableError("photo key provider unavailable")
        payload = await session.scalar(
            select(PortraitPayload).where(
                PortraitPayload.workspace_id == workspace,
                PortraitPayload.portrait_id == portrait_id,
                PortraitPayload.part == "thumbnail",
            )
        )
        if payload is None:
            raise PhotoUnavailableError("reference payload unavailable")
        data = await decrypted_thumbnail(payload, photo, wrapper)
        session.add(photo_event("persona.portrait_read", workspace, actor, portrait_id, uuid4()))
    return data
