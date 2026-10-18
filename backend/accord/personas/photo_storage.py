"""Authenticated encryption contexts and transactional portrait observations."""

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from accord.command.models import Event
from accord.personas.photo_contracts import PhotoReceipt
from accord.personas.photo_models import Portrait


def photo_context(workspace: UUID, photo: UUID, part: str, digest: str) -> bytes:
    return json.dumps(
        ["accord-portrait-v1", str(workspace), str(photo), part, digest],
        separators=(",", ":"),
    ).encode("ascii")


def photo_receipt(photo: Portrait) -> PhotoReceipt:
    return PhotoReceipt(
        id=photo.id,
        workspace_id=photo.workspace_id,
        request_id=photo.request_id,
        sha256=photo.sha256,
        width=photo.width,
        height=photo.height,
    )


def photo_event(
    action: str, workspace: UUID, actor: str, resource: UUID, request_id: UUID
) -> Event:
    return Event(
        event_id=uuid4().hex,
        ts=datetime.now(UTC),
        actor_type="user",
        actor_id=actor,
        tenant_id=workspace,
        category="persona",
        action=action,
        outcome="success",
        severity="info",
        resource_type="portrait",
        resource_id=str(resource),
        correlation_id=str(request_id),
        source="server",
        metadata_={},
    )
