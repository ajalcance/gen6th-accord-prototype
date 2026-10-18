"""Observe committed decision events versus matching retained audit-entry presence."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import AuditLog, Event
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_events import decision_event
from accord.personas.workflow_evidence_contracts import DecisionAnchor, RecordKind, WorkflowEvidence
from accord.personas.workflow_evidence_repository import decision_anchor
from accord.personas.workflow_repository import authorize_actor


def validate_decision_reference(row: Event | AuditLog, anchor: DecisionAnchor) -> None:
    if (
        row.event_id != anchor.event_id
        or row.tenant_id != anchor.workspace_id
        or row.action != anchor.action
        or row.actor_type != "user"
        or row.actor_id != anchor.actor_ref
        or row.outcome != "success"
        or row.severity != "info"
        or row.ts != anchor.recorded_at
        or row.resource_type != "persona_decision"
        or row.resource_id != str(anchor.record_id)
        or row.metadata_ != {"version_id": str(anchor.version_id)}
    ):
        raise RuntimeError("decision evidence references disagree")
    if isinstance(row, Event) and (
        row.source != "server"
        or row.category != "persona"
        or row.correlation_id != str(anchor.write_request_id)
    ):
        raise RuntimeError("decision event is not the committed server observation")


async def matching_evidence(
    session: AsyncSession, anchor: DecisionAnchor, observation_request_id: UUID
) -> WorkflowEvidence:
    event = await session.scalar(
        select(Event)
        .where(Event.event_id == anchor.event_id)
        .execution_options(populate_existing=True)
    )
    audit = await session.scalar(
        select(AuditLog)
        .where(AuditLog.event_id == anchor.event_id)
        .execution_options(populate_existing=True)
    )
    if event is None and audit is None:
        raise RuntimeError("decision evidence is unavailable")
    for row in (event, audit):
        if row is not None:
            validate_decision_reference(row, anchor)
    return WorkflowEvidence(
        anchor=anchor,
        observation_request_id=observation_request_id,
        cold_event_present=event is not None,
        audit_state="entry_present" if audit else "pending",
        audit_sequence=audit.seq if audit else None,
        audit_entry_hash=audit.entry_hash if audit else None,
    )


async def inspect_workflow_evidence(
    session: AsyncSession,
    workspace_id: UUID,
    actor: WorkflowActor,
    record_id: UUID,
    kind: RecordKind,
) -> WorkflowEvidence:
    """Authorized references only; neither current-use eligibility nor chain verification."""
    request_id = uuid4()
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace_id, actor, None)
        anchor = await decision_anchor(session, workspace_id, actor.actor_ref, record_id, kind)
        result = await matching_evidence(session, anchor, request_id)
        session.add(
            decision_event(
                workspace_id=workspace_id,
                actor_ref=actor.actor_ref,
                request_id=request_id,
                record_id=record_id,
                version_id=anchor.version_id,
                event_id=uuid4().hex,
                recorded_at=datetime.now(UTC),
                action="persona.workflow_observed",
            )
        )
    return result
