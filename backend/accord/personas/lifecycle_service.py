"""Attributed declarations, independent assessments and concern handling."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.lifecycle_contracts import (
    AppendLifecycle,
    Assessment,
    Dossier,
    LifecycleReceipt,
    Response,
)
from accord.personas.lifecycle_evidence import capture_digests
from accord.personas.lifecycle_models import LifecycleRecord
from accord.personas.lifecycle_repository import latest, observe, receipt, replay, target_record
from accord.personas.models import Persona, Version, WorkspaceMember
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import fingerprint
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor, locked_version, require_current


async def check_authority(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    persona: Persona,
    command: AppendLifecycle,
) -> None:
    content = command.content
    if isinstance(content, Dossier):
        await authorize_actor(session, workspace, actor, "creator")
        if persona.owner_ref != actor.actor_ref:
            raise AccessDeniedError("only the performer owner may declare authority and rights")
    elif isinstance(content, (Assessment, Response)):
        await authorize_actor(session, workspace, actor, "reviewer")
        if persona.owner_ref == actor.actor_ref:
            raise AccessDeniedError("independent reviewer required")
        if isinstance(content, Assessment):
            profile = await target_record(
                session, workspace, persona.id, content.profile_id, "dossier"
            )
            dossier = Dossier.model_validate(profile.content)
            if actor.actor_ref == dossier.operator.actor_ref:
                raise AccessDeniedError("an operator cannot approve their own authority or rights")
        else:
            report = await target_record(
                session, workspace, persona.id, content.concern_id, "concern"
            )
            if actor.actor_ref == report.actor_ref:
                raise AccessDeniedError("a reporter cannot decide their own concern")
            current = await latest(session, workspace, persona.id, "dossier")
            if (
                current
                and Dossier.model_validate(current.content).operator.actor_ref == actor.actor_ref
            ):
                raise AccessDeniedError("an operator cannot decide their own performer's concern")


async def validate_append(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    version: Version,
    persona: Persona,
    command: AppendLifecycle,
) -> tuple[UUID | None, str | None, dict[str, str]]:
    content = command.content
    target: UUID | None = None
    requirement: str | None = None
    digests: dict[str, str] = {}
    if isinstance(content, (Dossier, Assessment)):
        require_current(version, persona)
    if isinstance(content, Dossier):
        previous = await latest(session, workspace, persona.id, "dossier", version.id)
        if (
            await session.get(
                WorkspaceMember, (workspace, content.operator.actor_ref), populate_existing=True
            )
            is None
        ):
            raise AccessDeniedError("nominated operator must belong to this workspace")
        digests = await capture_digests(session, workspace, version.id, persona.owner_ref, content)
    elif isinstance(content, Assessment):
        target, requirement = content.profile_id, content.requirement
        previous, digests = await validate_assessment(session, workspace, version, persona, content)
    elif isinstance(content, Response):
        target = content.concern_id
        previous = await latest(session, workspace, persona.id, "response", target=target)
        if (
            previous is not None
            and Response.model_validate(previous.content).decision == "resolved"
        ):
            raise ConflictError("resolved cases require a new concern")
        if (
            previous is not None
            and Response.model_validate(previous.content).decision == "suspended"
            and content.decision == "open"
        ):
            raise ConflictError(
                "a suspended case requires explicit resolution before restoring use"
            )
    else:
        previous = None
    if (previous.id if previous else None) != command.expected_previous_id:
        raise ConflictError("lifecycle record changed; reload before deciding")
    return target, requirement, digests


async def validate_assessment(
    session: AsyncSession,
    workspace: UUID,
    version: Version,
    persona: Persona,
    content: Assessment,
) -> tuple[LifecycleRecord | None, dict[str, str]]:
    profile = await latest(session, workspace, persona.id, "dossier", version.id)
    if profile is None or profile.id != content.profile_id:
        raise ConflictError("dossier changed; review the current declaration")
    previous = await latest(
        session,
        workspace,
        persona.id,
        "assessment",
        version.id,
        content.profile_id,
        content.requirement,
    )
    digests: dict[str, str] = {}
    if content.decision == "approved":
        dossier = Dossier.model_validate(profile.content)
        validate_expiry(content, dossier)
        digests = await capture_digests(
            session, workspace, version.id, persona.owner_ref, dossier, content.requirement
        )
    return previous, digests


def validate_expiry(assessment: Assessment, dossier: Dossier) -> None:
    now = datetime.now(UTC)
    if not now < assessment.valid_until <= now + timedelta(days=366):
        raise ConflictError("approval expiry must be future and within 366 days")
    if assessment.requirement == "rights" and (
        assessment.valid_until > min(right.ends_at for right in dossier.rights)
        or any(right.starts_at > now or right.ends_at <= now for right in dossier.rights)
    ):
        raise ConflictError("rights approval must be within every declared rights window")


async def append(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, command: AppendLifecycle
) -> LifecycleReceipt:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, command.request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        version, persona = await locked_version(session, workspace, command.version_id)
        await check_authority(session, workspace, actor, persona, command)
        row = await replay(
            session, workspace, actor.actor_ref, command.request_id, fingerprint(command)
        )
        if row is None:
            row = await insert(session, workspace, actor, version, persona, command)
        await check_authority(session, workspace, actor, persona, command)
        await authorize_actor(session, workspace, actor, None)
        result = receipt(row)
    return result


async def insert(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    version: Version,
    persona: Persona,
    command: AppendLifecycle,
) -> LifecycleRecord:
    target, requirement, digests = await validate_append(
        session, workspace, actor, version, persona, command
    )
    previous = await latest(session, workspace, persona.id)
    row = LifecycleRecord(
        id=uuid4(),
        workspace_id=workspace,
        persona_id=persona.id,
        version_id=version.id,
        request_id=command.request_id,
        expected_previous_id=command.expected_previous_id,
        target_id=target,
        ordinal=previous.ordinal + 1 if previous else 1,
        actor_ref=actor.actor_ref,
        kind=command.content.kind,
        requirement=requirement,
        recorded_at=datetime.now(UTC),
        fingerprint=fingerprint(command),
        content=command.content.model_dump(mode="json"),
        evidence_digests=digests,
    )
    session.add(row)
    observe(
        session, workspace, actor, command.request_id, row.id, "lifecycle_" + command.content.kind
    )
    await session.flush()
    return row
