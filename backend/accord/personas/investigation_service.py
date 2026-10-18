"""Grounded analysis is attributed evidence; independent human decisions remain separate."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.investigation_contracts import (
    InvestigationCommand,
    InvestigationHistory,
    InvestigationPage,
    InvestigationReadiness,
    InvestigationResult,
)
from accord.personas.investigation_evidence import GroundedEvidence, gather
from accord.personas.investigation_provider import InvestigationRuntime, compare
from accord.personas.investigation_repository import history, replay
from accord.personas.investigation_storage import load, store
from accord.personas.photo_storage import photo_event
from accord.personas.similarity_contracts import SearchCommand
from accord.personas.similarity_query import available, require_query_open
from accord.personas.similarity_service import observation, recheck_catalogue
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor, locked_version, require_current


async def readiness(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    runtime: InvestigationRuntime | None,
) -> InvestigationReadiness:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        ready = runtime is not None and runtime.provider is not None
        if ready and runtime is not None:
            try:
                available(runtime.similarity)
            except RuntimeError:
                ready = False
        result = InvestigationReadiness(
            workspace_id=workspace, state="ready" if ready else "processing_unavailable"
        )
        observation(session, workspace, actor, uuid4())
    return result


async def generate(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: InvestigationCommand,
    runtime: InvestigationRuntime | None,
) -> InvestigationResult:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, command.request_id, actor_type=actor.audit_type
    ):
        async with asyncio.timeout(80):
            await authorize_actor(session, workspace, actor, None)
            version, persona = await locked_version(session, workspace, command.version_id)
            if runtime is None:
                raise RuntimeError("investigation key service unavailable")
            prior = await replay(session, workspace, actor.actor_ref, command)
            if prior is not None:
                result = await load(prior, runtime.similarity.wrapper)
            else:
                if command.scope == "current":
                    require_current(version, persona)
                result = await generate_new(session, workspace, actor, command, runtime)
            await authorize_actor(session, workspace, actor, None)
            observation(session, workspace, actor, command.request_id)
    return result


async def generate_new(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: InvestigationCommand,
    runtime: InvestigationRuntime,
) -> InvestigationResult:
    if runtime.provider is None:
        raise RuntimeError("investigation provider unavailable")
    evidence = await gather(session, workspace, actor, command, runtime)
    await authorize_actor(session, workspace, actor, None)
    await require_query_open(
        runtime.similarity, workspace, actor.actor_ref, evidence.capture.receipt
    )
    output = await compare(runtime.provider, evidence.images)
    rows = await history(session, workspace, InvestigationHistory(version_id=command.version_id))
    result = InvestigationResult(
        id=uuid4(),
        workspace_id=workspace,
        version_id=command.version_id,
        portrait_id=command.portrait_id,
        generation_id=command.generation_id,
        request_id=command.request_id,
        ordinal=rows[0].ordinal + 1 if rows else 1,
        actor_ref=actor.actor_ref,
        recorded_at=datetime.now(UTC),
        source_note=command.source_note,
        query=evidence.capture.receipt,
        reference_sha256=evidence.reference_sha256,
        reference_face=evidence.images.reference_face,
        search=evidence.search,
        model=output.model,
        provider_revision=output.revision,
        findings=output.findings,
    )
    await store(session, result, command, runtime.similarity.wrapper)
    await final_evidence_check(session, workspace, actor, command, runtime, evidence)
    event = photo_event(
        "persona.workspace_observed", workspace, actor.actor_ref, result.id, command.request_id
    )
    event.actor_type, event.resource_type = actor.audit_type, "persona_investigation"
    event.metadata_ = {"operation": "investigation_recorded"}
    session.add(event)
    await session.flush()
    return result


async def final_evidence_check(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: InvestigationCommand,
    runtime: InvestigationRuntime,
    evidence: GroundedEvidence,
) -> None:
    await require_query_open(
        runtime.similarity, workspace, actor.actor_ref, evidence.capture.receipt
    )
    search = SearchCommand.model_validate(
        {field: getattr(command, field) for field in SearchCommand.model_fields}
    )
    await recheck_catalogue(
        session, workspace, actor, search, runtime.similarity, evidence.catalogue
    )


async def read_history(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: InvestigationHistory,
    runtime: InvestigationRuntime | None,
) -> InvestigationPage:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        await locked_version(session, workspace, command.version_id)
        if runtime is None:
            raise RuntimeError("investigation key service unavailable")
        rows = await history(session, workspace, command)
        items = tuple([await load(row, runtime.similarity.wrapper) for row in rows[:20]])
        await authorize_actor(session, workspace, actor, None)
        result = InvestigationPage(
            workspace_id=workspace,
            version_id=command.version_id,
            items=items,
            next_before_ordinal=items[-1].ordinal if len(rows) > 20 else None,
        )
        observation(session, workspace, actor, uuid4())
    return result
