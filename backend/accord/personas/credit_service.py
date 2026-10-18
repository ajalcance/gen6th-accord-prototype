"""Owner declarations and authenticated self-confirmation; no rights or review escalation."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.credit_contracts import (
    ConfirmCredit,
    CreditConfirmation,
    CreditContent,
    CreditProfile,
    CreditSnapshot,
    CreditSubject,
    SaveCredits,
)
from accord.personas.credit_models import CreditAcceptance, CreditRecord
from accord.personas.credit_repository import confirmation, confirmations, latest, replay, snapshot
from accord.personas.evidence_repository import owned
from accord.personas.models import WorkspaceMember
from accord.personas.photo_storage import photo_event
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import fingerprint
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor, locked_version, require_current


def observe(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    request: UUID,
    record: UUID,
    operation: str,
) -> None:
    event = photo_event("persona.workspace_observed", workspace, actor.actor_ref, record, request)
    event.actor_type, event.resource_type = actor.audit_type, "persona_credit_profile"
    event.metadata_ = {"operation": operation}
    session.add(event)


async def read(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, command: CreditSubject
) -> CreditProfile:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        await locked_version(session, workspace, command.version_id)
        row = await latest(session, workspace, command.version_id)
        result = CreditProfile(
            workspace_id=workspace,
            version_id=command.version_id,
            snapshot=snapshot(row) if row else None,
            confirmations=await confirmations(session, workspace, row.id) if row else (),
        )
        await authorize_actor(session, workspace, actor, None)
        observe(session, workspace, actor, uuid4(), command.version_id, "credits_read")
    return result


async def save(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, command: SaveCredits
) -> CreditSnapshot:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, command.request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, "creator")
        version, persona = await locked_version(session, workspace, command.version_id)
        if persona.owner_ref != actor.actor_ref:
            raise AccessDeniedError("only the performer owner may declare credits")
        row = await replay(
            session,
            CreditRecord,
            workspace,
            actor.actor_ref,
            command.request_id,
            fingerprint(command),
        )
        if row is None:
            require_current(version, persona)
            row = await append(session, workspace, actor, command)
        await authorize_actor(session, workspace, actor, "creator")
        result = snapshot(row)
    return result


async def append(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, command: SaveCredits
) -> CreditRecord:
    previous = await latest(session, workspace, command.version_id)
    if (previous.id if previous else None) != command.expected_previous_id:
        raise ConflictError("credit profile changed")
    for credit in command.content.credits:
        if (
            credit.actor_ref is not None
            and await session.get(
                WorkspaceMember, (workspace, credit.actor_ref), populate_existing=True
            )
            is None
        ):
            raise AccessDeniedError("credited account is not a workspace member")
        if credit.evidence_id is not None:
            evidence = await owned(session, workspace, actor, credit.evidence_id)
            if evidence.version_id != command.version_id:
                raise AccessDeniedError("credit evidence must belong to the exact version")
    row = CreditRecord(
        id=uuid4(),
        workspace_id=workspace,
        version_id=command.version_id,
        request_id=command.request_id,
        ordinal=previous.ordinal + 1 if previous else 1,
        declared_by=actor.actor_ref,
        recorded_at=datetime.now(UTC),
        fingerprint=fingerprint(command),
        content=command.content.model_dump(mode="json"),
    )
    session.add(row)
    observe(session, workspace, actor, command.request_id, row.id, "credits_declared")
    await session.flush()
    return row


def require_self_confirmation(
    content: CreditContent, command: ConfirmCredit, actor: WorkflowActor
) -> None:
    if command.credit_index >= len(content.credits):
        raise AccessDeniedError("credit unavailable")
    credit = content.credits[command.credit_index]
    if actor.kind != "human" or credit.kind != "human" or credit.actor_ref != actor.actor_ref:
        raise AccessDeniedError("a contributor must confirm their own attributed role")


async def confirm(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, command: ConfirmCredit
) -> CreditConfirmation:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, command.request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        version, persona = await locked_version(session, workspace, command.version_id)
        row = await replay(
            session,
            CreditAcceptance,
            workspace,
            actor.actor_ref,
            command.request_id,
            fingerprint(command),
        )
        if row is None:
            require_current(version, persona)
            row = await append_confirmation(session, workspace, actor, command)
        await authorize_actor(session, workspace, actor, None)
        result = confirmation(row)
    return result


async def append_confirmation(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, command: ConfirmCredit
) -> CreditAcceptance:
    profile = await latest(session, workspace, command.version_id)
    if profile is None or profile.id != command.profile_id:
        raise ConflictError("credit declaration changed")
    require_self_confirmation(CreditContent.model_validate(profile.content), command, actor)
    existing = await session.scalar(
        select(CreditAcceptance.id).where(
            CreditAcceptance.workspace_id == workspace,
            CreditAcceptance.profile_id == profile.id,
            CreditAcceptance.credit_index == command.credit_index,
        )
    )
    if existing is not None:
        raise ConflictError("credit was already confirmed; reuse its original request")
    row = CreditAcceptance(
        id=uuid4(),
        workspace_id=workspace,
        version_id=command.version_id,
        profile_id=profile.id,
        credit_index=command.credit_index,
        request_id=command.request_id,
        actor_ref=actor.actor_ref,
        fingerprint=fingerprint(command),
        recorded_at=datetime.now(UTC),
    )
    session.add(row)
    observe(session, workspace, actor, command.request_id, row.id, "credit_confirmed")
    await session.flush()
    return row
