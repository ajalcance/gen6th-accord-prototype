"""Bind only inspected owner uploads while creating an immutable version."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.models import Version
from accord.personas.photo_contracts import PhotoChange
from accord.personas.photo_models import Portrait, PortraitPayload, VersionPortrait
from accord.personas.photo_storage import photo_event
from accord.personas.repository import AccessDeniedError, ConflictError


async def bind_photo(
    session: AsyncSession, version: Version, actor: str, change: PhotoChange
) -> None:
    selected = change.upload_id
    if change.action == "keep" and version.revision > 1:
        selected = await session.scalar(
            select(VersionPortrait.portrait_id)
            .join(Version, Version.id == VersionPortrait.version_id)
            .where(
                Version.workspace_id == version.workspace_id,
                Version.persona_id == version.persona_id,
                Version.revision == version.revision - 1,
                VersionPortrait.workspace_id == version.workspace_id,
            )
        )
    if change.action == "remove" or selected is None:
        return
    photo = await session.scalar(
        select(Portrait).where(
            Portrait.workspace_id == version.workspace_id, Portrait.id == selected
        )
    )
    if photo is None or photo.owner_ref != actor:
        raise AccessDeniedError("portrait access denied")
    # Keeping a historical binding is permitted beyond staging expiry.
    if change.action == "attach" and photo.expires_at <= datetime.now(UTC):
        raise ConflictError("portrait staging expired")
    parts = (
        await session.scalars(
            select(PortraitPayload.part).where(
                PortraitPayload.workspace_id == version.workspace_id,
                PortraitPayload.portrait_id == selected,
            )
        )
    ).all()
    if set(parts) != {"original", "thumbnail"}:
        raise ConflictError("portrait bytes unavailable")
    session.add(
        VersionPortrait(
            workspace_id=version.workspace_id, version_id=version.id, portrait_id=selected
        )
    )
    session.add(
        photo_event("persona.portrait_bound", version.workspace_id, actor, selected, uuid4())
    )
