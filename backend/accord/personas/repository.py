"""Scoped storage operations; all calls require the service transaction."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.contracts import PersonaDraft, PersonaVersion
from accord.personas.models import Persona, Version, WriteReceipt


class AccessDeniedError(Exception):
    """No authorized record is disclosed."""


class ConflictError(Exception):
    """Stale revision or changed payload under an existing request ID."""


async def authorize(
    session: AsyncSession,
    workspace_id: UUID,
    actor_ref: str,
    *,
    write: bool,
) -> None:
    await session.execute(
        text("SELECT set_config('accord.workspace_id', :workspace, true)"),
        {"workspace": str(workspace_id)},
    )
    role = await session.scalar(
        text("SELECT accord_workspace_membership(:workspace, :actor)"),
        {"workspace": workspace_id, "actor": actor_ref},
    )
    if role is None or (write and role != "creator"):
        raise AccessDeniedError("workspace access denied")


async def replay(
    session: AsyncSession,
    workspace_id: UUID,
    actor_ref: str,
    request_id: UUID,
    fingerprint: str,
) -> Version | None:
    receipt = await session.get(WriteReceipt, (workspace_id, actor_ref, request_id))
    if receipt is None:
        return None
    if receipt.fingerprint != fingerprint:
        raise ConflictError("request ID already used for different content")
    result = await session.scalars(
        select(Version).where(
            Version.id == receipt.version_id,
            Version.workspace_id == workspace_id,
        )
    )
    version = result.one_or_none()
    if version is None:
        raise RuntimeError("stored replay receipt has no authorized version")
    return version


async def head(
    session: AsyncSession,
    workspace_id: UUID,
    persona_id: UUID,
    actor_ref: str,
    expected_revision: int,
) -> Persona:
    persona = await session.scalar(
        select(Persona)
        .where(
            Persona.id == persona_id,
            Persona.workspace_id == workspace_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if persona is None or persona.owner_ref != actor_ref:
        raise AccessDeniedError("persona access denied")
    if persona.head_revision != expected_revision:
        raise ConflictError("persona revision changed")
    return persona


async def version_row(
    session: AsyncSession, workspace_id: UUID, persona_id: UUID, revision: int | None
) -> Version:
    """Use only after membership authorization in the caller's transaction."""
    query = select(Version).where(
        Version.workspace_id == workspace_id, Version.persona_id == persona_id
    )
    if revision is not None:
        query = query.where(Version.revision == revision)
    row = await session.scalar(query.order_by(Version.revision.desc()).limit(1))
    if row is None:
        raise AccessDeniedError("persona access denied")
    return row


def snapshot(row: Version) -> PersonaVersion:
    return PersonaVersion(
        persona_id=row.persona_id,
        workspace_id=row.workspace_id,
        version_id=row.id,
        revision=row.revision,
        creator_ref=row.creator_ref,
        recorded_at=row.recorded_at,
        content=PersonaDraft(
            name=row.name,
            biography=row.biography,
            human_contribution=row.human_contribution,
            ai_disclosure=row.ai_disclosure,
        ),
    )
