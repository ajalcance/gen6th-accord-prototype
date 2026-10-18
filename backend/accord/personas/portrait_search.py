"""Transient exact-file lookup over enrolled, authorized portrait history; no face inference."""

from collections.abc import AsyncIterable
from datetime import UTC, datetime
from typing import Literal, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.capture_models import VersionReference
from accord.personas.contracts import PersonaVersion
from accord.personas.models import Version
from accord.personas.photo_contracts import Digest
from accord.personas.photo_intake import read_photo_intent
from accord.personas.photo_models import Portrait, VersionPortrait
from accord.personas.repository import snapshot
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor

SEARCH_LIMIT = 20


class PortraitSearchPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    request_id: UUID
    sha256: Digest
    method: Literal["exact_file_sha256"] = "exact_file_sha256"
    items: tuple[PersonaVersion, ...] = Field(max_length=SEARCH_LIMIT)
    has_more: bool = Field(strict=True)

    @model_validator(mode="after")
    def scoped_results(self) -> Self:
        ids = [item.persona_id for item in self.items]
        if ids != sorted(set(ids)) or any(
            item.workspace_id != self.workspace_id for item in self.items
        ):
            raise ValueError("search results must contain unique ordered workspace records")
        if self.has_more and len(self.items) != SEARCH_LIMIT:
            raise ValueError("truncated results must fill the result limit")
        return self


def matching_versions(workspace: UUID, digest: str) -> Select[tuple[Version]]:
    """PostgreSQL DISTINCT ON returns the newest matching version for each persona."""
    enrolled = (
        select(
            VersionPortrait.workspace_id, VersionPortrait.version_id, VersionPortrait.portrait_id
        )
        .where(
            VersionPortrait.workspace_id == workspace,
        )
        .union(
            select(
                VersionReference.workspace_id,
                VersionReference.version_id,
                VersionReference.portrait_id,
            ).where(
                VersionReference.workspace_id == workspace,
            )
        )
        .subquery("enrolled_portraits")
    )
    return (
        select(Version)
        .join(
            enrolled,
            (enrolled.c.version_id == Version.id)
            & (enrolled.c.workspace_id == Version.workspace_id),
        )
        .join(
            Portrait,
            (Portrait.id == enrolled.c.portrait_id)
            & (Portrait.workspace_id == enrolled.c.workspace_id),
        )
        .where(
            Version.workspace_id == workspace,
            enrolled.c.workspace_id == workspace,
            Portrait.workspace_id == workspace,
            Portrait.sha256 == digest,
        )
        .distinct(Version.persona_id)
        .order_by(Version.persona_id, Version.revision.desc())
        .limit(SEARCH_LIMIT + 1)
    )


def search_observation(workspace: UUID, actor: WorkflowActor, page: PortraitSearchPage) -> Event:
    # No uploaded bytes, name, digest, candidate identifiers or claimed browser actor in telemetry.
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
        resource_type="persona_portrait_search",
        resource_id=str(workspace),
        correlation_id=str(page.request_id),
        source="server",
        metadata_={
            "operation": "portrait_exact_search",
            "method": page.method,
            "returned": len(page.items),
            "has_more": page.has_more,
        },
    )


async def search_portraits(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, body: AsyncIterable[bytes]
) -> PortraitSearchPage:
    """Authorize before consuming input. Hash bytes without decoding, storing or enrolling them."""
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        command, _data = await read_photo_intent(body)
        rows = list(await session.scalars(matching_versions(workspace, command.sha256)))
        page = PortraitSearchPage(
            workspace_id=workspace,
            request_id=command.request_id,
            sha256=command.sha256,
            items=tuple(snapshot(row) for row in rows[:SEARCH_LIMIT]),
            has_more=len(rows) > SEARCH_LIMIT,
        )
        session.add(search_observation(workspace, actor, page))
    return page
