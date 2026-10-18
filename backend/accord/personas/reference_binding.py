"""Reference approval is an owner write bound to a newly created immutable version."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.capture_contracts import ReferenceChange
from accord.personas.capture_models import PortraitCapture, VersionReference
from accord.personas.models import Version
from accord.personas.photo_models import Portrait, VersionPortrait
from accord.personas.photo_storage import photo_event
from accord.personas.repository import AccessDeniedError, ConflictError


async def prior_references(session: AsyncSession, version: Version) -> tuple[UUID, ...]:
    return tuple(
        await session.scalars(
            select(VersionReference.portrait_id)
            .join(Version, Version.id == VersionReference.version_id)
            .where(
                Version.workspace_id == version.workspace_id,
                Version.persona_id == version.persona_id,
                Version.revision == version.revision - 1,
                VersionReference.workspace_id == version.workspace_id,
            )
            .order_by(VersionReference.position)
        )
    )


async def previously_enrolled(session: AsyncSession, version: Version, portrait: UUID) -> bool:
    for binding in (VersionPortrait, VersionReference):
        found = await session.scalar(
            select(
                exists().where(
                    binding.workspace_id == version.workspace_id,
                    binding.portrait_id == portrait,
                    binding.version_id == Version.id,
                    Version.workspace_id == version.workspace_id,
                    Version.persona_id == version.persona_id,
                    Version.revision < version.revision,
                )
            )
        )
        if found:
            return True
    return False


async def approved_capture(
    session: AsyncSession, version: Version, actor: str, portrait: UUID
) -> None:
    photo = await session.scalar(
        select(Portrait).where(
            Portrait.workspace_id == version.workspace_id,
            Portrait.id == portrait,
        )
    )
    if photo is None or photo.owner_ref != actor:
        raise AccessDeniedError("reference access denied")
    capture = await session.scalar(
        select(PortraitCapture.portrait_id).where(
            PortraitCapture.workspace_id == version.workspace_id,
            PortraitCapture.portrait_id == portrait,
        )
    )
    if capture is None:
        raise ConflictError("reference analysis capture unavailable")
    if photo.expires_at <= datetime.now(UTC) and not await previously_enrolled(
        session, version, portrait
    ):
        raise ConflictError("reference staging expired")


async def bind_references(
    session: AsyncSession, version: Version, actor: str, change: ReferenceChange
) -> None:
    selected = (
        await prior_references(session, version) if change.action == "keep" else change.upload_ids
    )
    if version.revision == 1 and change.action == "keep":
        primary = await session.scalar(
            select(VersionPortrait.portrait_id)
            .join(
                PortraitCapture,
                (PortraitCapture.portrait_id == VersionPortrait.portrait_id)
                & (PortraitCapture.workspace_id == VersionPortrait.workspace_id),
            )
            .where(
                VersionPortrait.workspace_id == version.workspace_id,
                VersionPortrait.version_id == version.id,
            )
        )
        selected = (primary,) if primary else ()
    for position, portrait in enumerate(selected, start=1):
        await approved_capture(session, version, actor, portrait)
        session.add(
            VersionReference(
                workspace_id=version.workspace_id,
                version_id=version.id,
                portrait_id=portrait,
                position=position,
            )
        )
        event = photo_event(
            "persona.portrait_bound", version.workspace_id, actor, portrait, uuid4()
        )
        event.metadata_ = {
            "operation": "reference_approved",
            "version_id": str(version.id),
            "position": position,
        }
        session.add(event)
