"""Authorized internal receipt inspection; no public verification or HTTP endpoint."""

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import AuditLog, Event
from accord.personas.models import Version, WriteReceipt
from accord.personas.repository import authorize, version_row
from accord.personas.service import read_event
from accord.personas.transactions import tracked_transaction


class PersistenceEvidence(BaseModel):
    """References only. Audit entry presence does not verify chain integrity."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    persona_id: UUID
    version_id: UUID
    revision: int = Field(ge=1, strict=True)
    recorded_at: datetime
    write_request_id: UUID
    observation_request_id: UUID
    event_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    cold_event_present: bool
    audit_state: Literal["pending", "entry_present"]
    audit_sequence: int | None = Field(ge=1, strict=True)
    audit_entry_hash: str | None = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("recorded_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("receipt time must include a timezone")
        return value

    @model_validator(mode="after")
    def require_consistent_audit(self) -> "PersistenceEvidence":
        present = self.audit_sequence is not None and self.audit_entry_hash is not None
        absent = self.audit_sequence is None and self.audit_entry_hash is None
        if not (present if self.audit_state == "entry_present" else absent):
            raise ValueError("audit state must correspond to complete entry references")
        if not self.cold_event_present and self.audit_state == "pending":
            raise ValueError("evidence requires either a cold event or an audit entry")
        return self


def validate_reference(row: Event | AuditLog, version: Version) -> None:
    """Never display a receipt assembled from mismatched server records."""
    if (
        row.tenant_id != version.workspace_id
        or row.action != "persona.version_saved"
        or row.actor_type != "user"
        or row.actor_id != version.creator_ref
        or row.outcome != "success"
        or row.ts != version.recorded_at
        or row.resource_type != "persona"
        or row.resource_id != str(version.persona_id)
        or row.metadata_ != {"version_id": str(version.id), "revision": version.revision}
    ):
        raise RuntimeError("persona evidence references disagree")


async def evidence_rows(
    session: AsyncSession, version: Version
) -> tuple[WriteReceipt, Event | None, AuditLog | None]:
    receipt = await session.scalar(
        select(WriteReceipt).where(
            WriteReceipt.workspace_id == version.workspace_id,
            WriteReceipt.version_id == version.id,
            WriteReceipt.actor_ref == version.creator_ref,
        )
    )
    # Retention can remove a cold row; never let an ORM identity-map hit report it present.
    event = await session.scalar(
        select(Event)
        .where(Event.event_id == version.event_id)
        .execution_options(populate_existing=True)
    )
    audit = await session.scalar(
        select(AuditLog)
        .where(AuditLog.event_id == version.event_id)
        .execution_options(populate_existing=True)
    )
    if receipt is None or (event is None and audit is None):
        raise RuntimeError("persona evidence is unavailable")
    if event is not None:
        validate_reference(event, version)
        if event.source != "server" or event.correlation_id != str(receipt.request_id):
            raise RuntimeError("persona event is not the committed server observation")
    if audit is not None:
        validate_reference(audit, version)
    return receipt, event, audit


async def inspect_evidence(
    session: AsyncSession,
    workspace_id: UUID,
    actor_ref: str,
    persona_id: UUID,
    revision: int | None = None,
) -> PersistenceEvidence:
    """Membership-scoped observation with its own committed version-read event."""
    request_id = uuid4()
    async with tracked_transaction(session, workspace_id, actor_ref, request_id):
        await authorize(session, workspace_id, actor_ref, write=False)
        version = await version_row(session, workspace_id, persona_id, revision)
        receipt, event, audit = await evidence_rows(session, version)
        session.add(read_event(version, actor_ref, request_id))
        result = PersistenceEvidence(
            workspace_id=workspace_id,
            persona_id=persona_id,
            version_id=version.id,
            revision=version.revision,
            recorded_at=version.recorded_at,
            write_request_id=receipt.request_id,
            observation_request_id=request_id,
            event_id=version.event_id,
            cold_event_present=event is not None,
            audit_state="entry_present" if audit is not None else "pending",
            audit_sequence=audit.seq if audit is not None else None,
            audit_entry_hash=audit.entry_hash if audit is not None else None,
        )
    return result
