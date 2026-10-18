"""Transactional version persistence for server-verified workspace actors.

The caller supplies a server-resolved actor. Membership is read from PostgreSQL;
request bodies never supply a role. This service owns the complete transaction.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, SerializerFunctionWrapHandler, model_serializer
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.capture_contracts import ReferenceChange
from accord.personas.contracts import PersonaDraft, PersonaVersion
from accord.personas.models import Persona, Version, WriteReceipt
from accord.personas.photo_binding import bind_photo
from accord.personas.photo_contracts import PhotoChange
from accord.personas.reference_binding import bind_references
from accord.personas.repository import authorize, head, replay, snapshot, version_row
from accord.personas.transactions import tracked_transaction


class SaveCommand(BaseModel):
    """Validated write intent; retries must reuse all semantic inputs."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: UUID
    content: PersonaDraft
    persona_id: UUID | None = None
    expected_revision: int = Field(default=0, ge=0, strict=True)
    photo: PhotoChange = Field(default_factory=PhotoChange)
    references: ReferenceChange = Field(default_factory=ReferenceChange)

    @model_serializer(mode="wrap")
    def legacy_intent(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        data = cast(dict[str, object], handler(self))
        if self.photo.action == "keep":
            data.pop("photo", None)
        if self.references.action == "keep":
            data.pop("references", None)
        return data


def fingerprint(command: BaseModel) -> str:
    """Replay equality only; not a signature or public evidence fingerprint."""
    data = command.model_dump(mode="json")
    # Existing four-field request receipts retain their exact replay fingerprint.
    if isinstance(command, SaveCommand) and command.photo.action == "keep":
        data.pop("photo", None)
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def saved_event(row: Version, actor_ref: str, request_id: UUID) -> Event:
    return Event(
        event_id=row.event_id,
        ts=row.recorded_at,
        actor_type="user",
        actor_id=actor_ref,
        tenant_id=row.workspace_id,
        category="persona",
        action="persona.version_saved",
        outcome="success",
        severity="info",
        resource_type="persona",
        resource_id=str(row.persona_id),
        correlation_id=str(request_id),
        source="server",
        metadata_={"version_id": str(row.id), "revision": row.revision},
    )


async def prepare_persona(
    session: AsyncSession,
    workspace_id: UUID,
    actor_ref: str,
    command: SaveCommand,
) -> Persona:
    if command.persona_id is None:
        if command.expected_revision != 0:
            raise ValueError("new personas require revision zero")
        persona = Persona(
            id=uuid4(), workspace_id=workspace_id, owner_ref=actor_ref, head_revision=1
        )
        session.add(persona)
    else:
        persona = await head(
            session,
            workspace_id,
            command.persona_id,
            actor_ref,
            command.expected_revision,
        )
        persona.head_revision += 1
    await session.flush()
    return persona


async def new_version(
    session: AsyncSession,
    workspace_id: UUID,
    actor_ref: str,
    command: SaveCommand,
) -> Version:
    persona = await prepare_persona(session, workspace_id, actor_ref, command)
    row = Version(
        id=uuid4(),
        workspace_id=workspace_id,
        persona_id=persona.id,
        revision=persona.head_revision,
        creator_ref=actor_ref,
        recorded_at=datetime.now(UTC),
        event_id=uuid4().hex,
        **command.content.model_dump(),
    )
    session.add(saved_event(row, actor_ref, command.request_id))
    await session.flush()
    session.add(row)
    await session.flush()
    await bind_photo(session, row, actor_ref, command.photo)
    await bind_references(session, row, actor_ref, command.references)
    session.add(
        WriteReceipt(
            workspace_id=workspace_id,
            actor_ref=actor_ref,
            request_id=command.request_id,
            fingerprint=fingerprint(command),
            version_id=row.id,
        )
    )
    await session.flush()
    return row


async def save(
    session: AsyncSession,
    workspace_id: UUID,
    actor_ref: str,
    command: SaveCommand,
) -> PersonaVersion:
    """Commit head, immutable version, event and replay receipt together, or none."""
    async with tracked_transaction(session, workspace_id, actor_ref, command.request_id):
        await authorize(session, workspace_id, actor_ref, write=True)
        row = await replay(
            session, workspace_id, actor_ref, command.request_id, fingerprint(command)
        )
        if row is None:
            row = await new_version(session, workspace_id, actor_ref, command)
        result = snapshot(row)
    return result


async def load(
    session: AsyncSession,
    workspace_id: UUID,
    actor_ref: str,
    persona_id: UUID,
    revision: int | None = None,
) -> PersonaVersion:
    """Workspace-authorized snapshot read, with a committed read event."""
    request_id = uuid4()
    async with tracked_transaction(session, workspace_id, actor_ref, request_id):
        await authorize(session, workspace_id, actor_ref, write=False)
        row = await version_row(session, workspace_id, persona_id, revision)
        session.add(read_event(row, actor_ref, request_id))
        result = snapshot(row)
    return result


def read_event(row: Version, actor_ref: str, request_id: UUID) -> Event:
    """One minimal server observation for an authorized version read."""
    return Event(
        event_id=uuid4().hex,
        ts=datetime.now(UTC),
        actor_type="user",
        actor_id=actor_ref,
        tenant_id=row.workspace_id,
        category="persona",
        action="persona.version_read",
        outcome="success",
        severity="info",
        resource_type="persona",
        resource_id=str(row.persona_id),
        correlation_id=str(request_id),
        source="server",
        metadata_={"version_id": str(row.id), "revision": row.revision},
    )
