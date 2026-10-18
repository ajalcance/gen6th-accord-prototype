"""Exact approved-reference authorization precedes all decrypts and provider calls."""

from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.capture_models import PortraitCapture, VersionReference
from accord.personas.face_contracts import FaceSubject
from accord.personas.face_models import FaceGeneration
from accord.personas.models import Persona, Version
from accord.personas.photo_models import Portrait
from accord.personas.repository import AccessDeniedError


async def reference(
    session: AsyncSession, workspace: UUID, actor: str, subject: FaceSubject, *, write: bool
) -> tuple[Portrait, PortraitCapture]:
    query = (
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
        .join(
            Version,
            (Version.id == VersionReference.version_id)
            & (Version.workspace_id == VersionReference.workspace_id),
        )
        .where(
            Portrait.workspace_id == workspace,
            Portrait.id == subject.portrait_id,
            PortraitCapture.workspace_id == workspace,
            VersionReference.workspace_id == workspace,
            VersionReference.version_id == subject.version_id,
            Version.workspace_id == workspace,
        )
    )
    if write:
        query = (
            query.join(
                Persona,
                (Persona.id == Version.persona_id) & (Persona.workspace_id == Version.workspace_id),
            )
            .where(Version.creator_ref == actor, Persona.owner_ref == actor)
            .with_for_update(of=Persona)
        )
    row = (await session.execute(query)).one_or_none()
    if row is None:
        raise AccessDeniedError("approved reference access denied")
    return row[0], row[1]


async def generation(
    session: AsyncSession,
    workspace: UUID,
    subject: FaceSubject,
    identity: UUID | None = None,
    request: UUID | None = None,
) -> FaceGeneration | None:
    query = select(FaceGeneration).where(FaceGeneration.workspace_id == workspace)
    if request is not None:
        query = query.where(FaceGeneration.request_id == request)
    else:
        query = query.where(
            FaceGeneration.version_id == subject.version_id,
            FaceGeneration.portrait_id == subject.portrait_id,
        )
        if identity is not None:
            query = query.where(FaceGeneration.id == identity)
    return cast(
        FaceGeneration | None,
        await session.scalar(
            query.order_by(FaceGeneration.recorded_at.desc(), FaceGeneration.id.desc()).limit(1)
        ),
    )
