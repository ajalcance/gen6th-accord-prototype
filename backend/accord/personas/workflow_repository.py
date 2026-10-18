"""Shared scoped queries for internal review and campaign decisions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.models import Persona, Version, WorkspaceMember
from accord.personas.repository import AccessDeniedError, ConflictError, authorize
from accord.personas.review_models import ReviewRecord
from accord.personas.workflow_contracts import WorkflowActor


async def authorize_actor(
    session: AsyncSession, workspace_id: UUID, actor: WorkflowActor, role: str | None
) -> None:
    await authorize(session, workspace_id, actor.actor_ref, write=False)
    if actor.kind != "human":
        raise AccessDeniedError("human decision context required")
    member = await session.get(
        WorkspaceMember, (workspace_id, actor.actor_ref), populate_existing=True
    )
    if member is None or (role is not None and member.role != role):
        raise AccessDeniedError("decision permission denied")


async def locked_version(
    session: AsyncSession, workspace_id: UUID, version_id: UUID
) -> tuple[Version, Persona]:
    version = await session.scalar(
        select(Version).where(Version.workspace_id == workspace_id, Version.id == version_id)
    )
    if version is None:
        raise AccessDeniedError("version access denied")
    persona = await session.scalar(
        select(Persona)
        .where(Persona.workspace_id == workspace_id, Persona.id == version.persona_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if persona is None:
        raise AccessDeniedError("persona access denied")
    return version, persona


def require_current(version: Version, persona: Persona) -> None:
    if version.revision != persona.head_revision:
        raise ConflictError("persona version is no longer current")


async def latest_review(
    session: AsyncSession, workspace_id: UUID, version_id: UUID
) -> ReviewRecord | None:
    rows = await session.scalars(
        select(ReviewRecord)
        .where(ReviewRecord.workspace_id == workspace_id, ReviewRecord.version_id == version_id)
        .order_by(ReviewRecord.ordinal.desc())
        .limit(1)
        .execution_options(populate_existing=True)
    )
    return rows.one_or_none()


async def has_role(session: AsyncSession, workspace_id: UUID, actor_ref: str, role: str) -> bool:
    stored_role = await session.scalar(
        select(WorkspaceMember.role).where(
            WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.actor_ref == actor_ref
        )
    )
    return stored_role == role
