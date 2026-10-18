"""Bounded exact baseline over a single studio's approved references and latest generations."""

from typing import cast
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Subquery

from accord.personas.capture_models import PortraitCapture, VersionReference
from accord.personas.face_models import FaceGeneration
from accord.personas.models import Persona, Version
from accord.personas.similarity_contracts import Scope

POOL_LIMIT = 128
ReferenceRow = tuple[Version, PortraitCapture, FaceGeneration | None]


def reference_pool(
    workspace: UUID, scope: Scope
) -> Select[tuple[Version, PortraitCapture, FaceGeneration]]:
    latest = latest_generations(workspace)
    query = (
        select(Version, PortraitCapture, FaceGeneration)
        .join(
            VersionReference,
            (VersionReference.version_id == Version.id)
            & (VersionReference.workspace_id == Version.workspace_id),
        )
        .join(
            PortraitCapture,
            (PortraitCapture.portrait_id == VersionReference.portrait_id)
            & (PortraitCapture.workspace_id == VersionReference.workspace_id),
        )
        .join(
            Persona,
            (Persona.id == Version.persona_id) & (Persona.workspace_id == Version.workspace_id),
        )
        .outerjoin(
            latest,
            (latest.c.version_id == Version.id)
            & (latest.c.portrait_id == PortraitCapture.portrait_id),
        )
        .outerjoin(
            FaceGeneration,
            (FaceGeneration.id == latest.c.id)
            & (FaceGeneration.workspace_id == Version.workspace_id),
        )
        .where(
            Version.workspace_id == workspace,
            VersionReference.workspace_id == workspace,
            PortraitCapture.workspace_id == workspace,
            Persona.workspace_id == workspace,
        )
        .order_by(Version.persona_id, Version.revision.desc(), PortraitCapture.portrait_id)
        .limit(POOL_LIMIT + 1)
        .execution_options(populate_existing=True)
    )
    return query.where(Version.revision == Persona.head_revision) if scope == "current" else query


def latest_generations(workspace: UUID) -> Subquery:
    return (
        select(FaceGeneration.id, FaceGeneration.version_id, FaceGeneration.portrait_id)
        .where(FaceGeneration.workspace_id == workspace)
        .distinct(FaceGeneration.version_id, FaceGeneration.portrait_id)
        .order_by(
            FaceGeneration.version_id,
            FaceGeneration.portrait_id,
            FaceGeneration.recorded_at.desc(),
            FaceGeneration.id.desc(),
        )
        .subquery("latest_reference_generation")
    )


async def pool(session: AsyncSession, workspace: UUID, scope: Scope) -> list[ReferenceRow]:
    rows = (await session.execute(reference_pool(workspace, scope))).all()
    if len(rows) > POOL_LIMIT:
        raise RuntimeError("catalogue exceeds bounded exact baseline")
    return [cast(ReferenceRow, tuple(row)) for row in rows]


def pool_binding(rows: list[ReferenceRow]) -> tuple[tuple[UUID, UUID, UUID | None], ...]:
    return tuple((v.id, c.portrait_id, g.id if g else None) for v, c, g in rows)
