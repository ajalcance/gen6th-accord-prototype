"""Owner-scoped metadata status without decrypting or exposing private bytes."""

from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.evidence_contracts import EvidenceSnapshot
from accord.personas.evidence_repository import inspection, observed, owned, snapshot
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor


async def evidence_status(
    session: AsyncSession, workspace_id: UUID, actor: WorkflowActor, evidence_id: UUID
) -> EvidenceSnapshot:
    request_id = uuid4()
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, request_id, actor_type=actor.audit_type
    ):
        # Immutable metadata inspection requires SELECT, not payload lifecycle locks.
        row = await owned(session, workspace_id, actor, evidence_id, lock=False)
        inspected = await inspection(session, row)
        verdict = inspected.verdict if inspected else None
        result = snapshot(row, verdict)
        event = observed(row, actor, request_id, "persona.evidence_read", verdict)
        event.metadata_ = {**event.metadata_, "view": "metadata"}
        session.add(event)
    return result
