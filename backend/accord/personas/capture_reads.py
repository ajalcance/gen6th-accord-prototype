"""Authorized processing metadata only; analysis pixels and wrapping material stay server-side."""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.capture_contracts import CaptureMetadata, CaptureProfile, CaptureQuery
from accord.personas.capture_models import PortraitCapture, VersionReference
from accord.personas.models import Version
from accord.personas.photo_models import Portrait, VersionPortrait
from accord.personas.photo_storage import photo_event
from accord.personas.repository import AccessDeniedError, authorize
from accord.personas.transactions import tracked_transaction


def capture_metadata(photo: Portrait, capture: PortraitCapture) -> CaptureMetadata:
    return CaptureMetadata(
        portrait_id=photo.id,
        source_sha256=photo.sha256,
        source_width=capture.source_width,
        source_height=capture.source_height,
        orientation=capture.orientation,
        width=capture.width,
        height=capture.height,
        sha256=capture.sha256,
        recipe=capture.recipe,
        decoder_version=capture.decoder_version,
        recorded_at=capture.recorded_at,
    )


async def read_capture(
    session: AsyncSession, workspace: UUID, portrait: UUID | None
) -> CaptureMetadata | None:
    if portrait is None:
        return None
    row = (
        await session.execute(
            select(Portrait, PortraitCapture)
            .join(
                PortraitCapture,
                (PortraitCapture.portrait_id == Portrait.id)
                & (PortraitCapture.workspace_id == Portrait.workspace_id),
            )
            .where(
                Portrait.workspace_id == workspace,
                Portrait.id == portrait,
                PortraitCapture.workspace_id == workspace,
            )
        )
    ).one_or_none()
    return capture_metadata(row[0], row[1]) if row else None


async def capture_subject(
    session: AsyncSession, workspace: UUID, actor: str, query: CaptureQuery
) -> UUID | None:
    if query.upload_id is not None:
        portrait = await session.scalar(
            select(Portrait.id).where(
                Portrait.workspace_id == workspace,
                Portrait.id == query.upload_id,
                Portrait.owner_ref == actor,
            )
        )
        if portrait is None:
            raise AccessDeniedError("upload capture access denied")
        return portrait
    version = await session.scalar(
        select(Version.id).where(
            Version.workspace_id == workspace,
            Version.id == query.version_id,
        )
    )
    if version is None:
        raise AccessDeniedError("version capture access denied")
    return (
        await session.scalars(
            select(VersionPortrait.portrait_id).where(
                VersionPortrait.workspace_id == workspace,
                VersionPortrait.version_id == query.version_id,
            )
        )
    ).one_or_none()


async def reference_captures(
    session: AsyncSession, workspace: UUID, version: UUID | None
) -> tuple[CaptureMetadata, ...]:
    rows = (
        (
            await session.execute(
                select(Portrait, PortraitCapture)
                .join(
                    PortraitCapture,
                    (PortraitCapture.portrait_id == Portrait.id)
                    & (PortraitCapture.workspace_id == Portrait.workspace_id),
                )
                .join(
                    VersionReference,
                    (VersionReference.portrait_id == Portrait.id)
                    & (VersionReference.workspace_id == Portrait.workspace_id),
                )
                .where(
                    VersionReference.workspace_id == workspace,
                    VersionReference.version_id == version,
                    Portrait.workspace_id == workspace,
                    PortraitCapture.workspace_id == workspace,
                )
                .order_by(VersionReference.position)
                .limit(9)
            )
        ).all()
        if version
        else []
    )
    return tuple(capture_metadata(photo, value) for photo, value in rows)


async def capture_profile(
    session: AsyncSession, workspace: UUID, actor: str, query: CaptureQuery
) -> CaptureProfile:
    request = uuid4()
    async with tracked_transaction(session, workspace, actor, request):
        await authorize(session, workspace, actor, write=False)
        portrait = await capture_subject(session, workspace, actor, query)
        capture = await read_capture(session, workspace, portrait)
        result = CaptureProfile(
            workspace_id=workspace,
            upload_id=query.upload_id,
            version_id=query.version_id,
            portrait_id=portrait,
            capture=capture,
            references=await reference_captures(session, workspace, query.version_id),
        )
        session.add(
            photo_event(
                "persona.portrait_read",
                workspace,
                actor,
                query.upload_id or query.version_id or request,
                request,
            )
        )
    return result
