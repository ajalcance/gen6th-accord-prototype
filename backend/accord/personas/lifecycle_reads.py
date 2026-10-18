"""Current requirements and bounded case/history reads; attachment bytes stay private."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.lifecycle_contracts import (
    ConcernStatus,
    LifecycleHistory,
    LifecyclePage,
    LifecycleProfile,
    RequirementStatus,
    Subject,
    effective_status,
)
from accord.personas.lifecycle_models import LifecycleRecord
from accord.personas.lifecycle_repository import is_suspended, latest, observe, receipt
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor, has_role, locked_version


async def requirements(
    session: AsyncSession, workspace: UUID, persona: UUID, profile: LifecycleRecord | None
) -> tuple[RequirementStatus, ...]:
    result: list[RequirementStatus] = []
    for dimension in ("operator", "rights", "content"):
        row = (
            await latest(
                session, workspace, persona, "assessment", target=profile.id, requirement=dimension
            )
            if profile
            else None
        )
        permitted = row is not None and await has_role(
            session, workspace, row.actor_ref, "reviewer"
        )
        assessment = receipt(row) if row else None
        result.append(
            RequirementStatus(
                requirement=dimension,
                status=effective_status(assessment, permitted),
                assessment=assessment,
            )
        )
    return tuple(result)


async def concern_statuses(
    session: AsyncSession, workspace: UUID, persona: UUID, reports: list[LifecycleRecord]
) -> tuple[ConcernStatus, ...]:
    result: list[ConcernStatus] = []
    for report in reports:
        response = await latest(session, workspace, persona, "response", target=report.id)
        result.append(
            ConcernStatus(report=receipt(report), response=receipt(response) if response else None)
        )
    return tuple(result)


async def read(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, command: Subject
) -> LifecycleProfile:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        version, persona = await locked_version(session, workspace, command.version_id)
        profile = await latest(session, workspace, persona.id, "dossier", version.id)
        reports = await session.scalars(
            select(LifecycleRecord)
            .where(
                LifecycleRecord.workspace_id == workspace,
                LifecycleRecord.persona_id == persona.id,
                LifecycleRecord.kind == "concern",
            )
            .order_by(LifecycleRecord.ordinal.desc())
            .limit(20)
        )
        cases = await concern_statuses(session, workspace, persona.id, list(reports))
        result = LifecycleProfile(
            workspace_id=workspace,
            version_id=version.id,
            persona_id=persona.id,
            dossier=receipt(profile) if profile else None,
            requirements=await requirements(session, workspace, persona.id, profile),
            concerns=cases,
            suspended=await is_suspended(session, workspace, persona.id),
            evaluated_at=datetime.now(UTC),
        )
        await authorize_actor(session, workspace, actor, None)
        observe(session, workspace, actor, uuid4(), version.id, "lifecycle_read")
    return result


async def history(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, command: LifecycleHistory
) -> LifecyclePage:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        _, persona = await locked_version(session, workspace, command.version_id)
        query = select(LifecycleRecord).where(
            LifecycleRecord.workspace_id == workspace, LifecycleRecord.persona_id == persona.id
        )
        if command.before_ordinal is not None:
            query = query.where(LifecycleRecord.ordinal < command.before_ordinal)
        rows = list(await session.scalars(query.order_by(LifecycleRecord.ordinal.desc()).limit(21)))
        cases = await concern_statuses(
            session, workspace, persona.id, [row for row in rows[:20] if row.kind == "concern"]
        )
        result = LifecyclePage(
            workspace_id=workspace,
            version_id=command.version_id,
            items=tuple(receipt(row) for row in rows[:20]),
            next_before_ordinal=rows[19].ordinal if len(rows) > 20 else None,
            concerns=cases,
        )
        await authorize_actor(session, workspace, actor, None)
        observe(session, workspace, actor, uuid4(), command.version_id, "lifecycle_history")
    return result
