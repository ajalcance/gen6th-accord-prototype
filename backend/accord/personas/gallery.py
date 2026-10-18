"""Authorized current-version gallery with bounded keyset pagination, not global totals."""

from datetime import UTC, datetime
from typing import Annotated, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.contracts import PersonaVersion
from accord.personas.models import Persona, Version
from accord.personas.repository import snapshot
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor


class GalleryQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    after_persona_id: UUID | None = None
    limit: int = Field(default=20, ge=1, le=100, strict=True)
    search: Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)] = ""


class GalleryPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    items: tuple[PersonaVersion, ...] = Field(max_length=100)
    next_after_persona_id: UUID | None = None

    @model_validator(mode="after")
    def consistent_page(self) -> Self:
        ids = [item.persona_id for item in self.items]
        if ids != sorted(set(ids)) or any(
            item.workspace_id != self.workspace_id for item in self.items
        ):
            raise ValueError("gallery page must contain unique ordered workspace records")
        if self.next_after_persona_id is not None and (
            not ids or self.next_after_persona_id != ids[-1]
        ):
            raise ValueError("gallery cursor must bind the final item")
        return self


def gallery_event(workspace: UUID, actor: WorkflowActor, request_id: UUID, count: int) -> Event:
    return Event(
        event_id=uuid4().hex,
        ts=datetime.now(UTC),
        actor_type=actor.audit_type,
        actor_id=actor.actor_ref,
        tenant_id=workspace,
        category="persona",
        action="persona.workspace_observed",
        outcome="success",
        severity="info",
        resource_type="persona_gallery",
        resource_id=str(workspace),
        correlation_id=str(request_id),
        source="server",
        metadata_={"operation": "gallery_list", "returned": count},
    )


async def list_gallery(
    session: AsyncSession, workspace_id: UUID, actor: WorkflowActor, query: GalleryQuery
) -> GalleryPage:
    """One current-head SELECT; refresh to see inserts before the cursor or changed names."""
    request_id = uuid4()
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace_id, actor, None)
        statement = (
            select(Version)
            .join(
                Persona,
                (
                    (Persona.id == Version.persona_id)
                    & (Persona.workspace_id == Version.workspace_id)
                    & (Persona.head_revision == Version.revision)
                ),
            )
            .where(Version.workspace_id == workspace_id)
        )
        if query.after_persona_id is not None:
            statement = statement.where(Version.persona_id > query.after_persona_id)
        if query.search:
            statement = statement.where(Version.name.icontains(query.search, autoescape=True))
        rows = list(
            await session.scalars(statement.order_by(Version.persona_id).limit(query.limit + 1))
        )
        items = tuple(snapshot(row) for row in rows[: query.limit])
        result = GalleryPage(
            workspace_id=workspace_id,
            items=items,
            next_after_persona_id=items[-1].persona_id if len(rows) > query.limit else None,
        )
        session.add(gallery_event(workspace_id, actor, request_id, len(items)))
    return result
