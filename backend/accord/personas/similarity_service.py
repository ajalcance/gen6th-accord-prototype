"""Authorize before bytes/decryption/cost and again after long operations before disclosure."""

import asyncio
from collections.abc import AsyncIterable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.face_contracts import RepresentationInfo
from accord.personas.face_providers import quality_reasons
from accord.personas.photo_intake import read_photo_intent
from accord.personas.photo_storage import photo_event
from accord.personas.repository import ConflictError
from accord.personas.similarity_cache import query_key
from accord.personas.similarity_contracts import (
    ClearReceipt,
    QueryReceipt,
    SearchCommand,
    SimilarityCandidate,
    SimilarityPage,
    SimilarityReadiness,
)
from accord.personas.similarity_query import (
    QueryCapture,
    SimilarityRuntime,
    available,
    load_query,
    prepare_query,
    query_vectors,
    require_query_open,
)
from accord.personas.similarity_ranking import confident_candidates, score_references
from accord.personas.similarity_repository import pool, pool_binding
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor


def observation(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, request: UUID
) -> None:
    event = photo_event(
        "persona.workspace_observed", workspace, actor.actor_ref, workspace, request
    )
    event.actor_type = actor.audit_type
    event.resource_type = "persona_similarity_query"
    session.add(event)


async def readiness(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, runtime: SimilarityRuntime | None
) -> SimilarityReadiness:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        state: str = "processing_unavailable"
        policy = runtime.policy if runtime else None
        if runtime is not None:
            state = "calibration_required" if policy is None else "ready"
        if policy and not policy.reviewed_at <= datetime.now(UTC) < policy.expires_at:
            state = "calibration_expired"
        result = SimilarityReadiness.model_validate(
            {
                "workspace_id": workspace,
                "state": state,
                "policy_id": policy.policy_id if policy else None,
            }
        )
        observation(session, workspace, actor, uuid4())
    return result


async def prepare(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    body: AsyncIterable[bytes],
    runtime: SimilarityRuntime | None,
) -> QueryReceipt:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        async with asyncio.timeout(80):
            await authorize_actor(session, workspace, actor, None)
            active = available(runtime)
            command, data = await read_photo_intent(body)
            receipt = await prepare_query(active, workspace, actor.actor_ref, command, data)
            await authorize_actor(session, workspace, actor, None)
            available(active)
            observation(session, workspace, actor, command.request_id)
    return receipt


async def search(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: SearchCommand,
    runtime: SimilarityRuntime | None,
) -> SimilarityPage:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, command.request_id, actor_type=actor.audit_type
    ):
        async with asyncio.timeout(80):
            await authorize_actor(session, workspace, actor, None)
            active = available(runtime)
            capture = await load_query(active, workspace, actor.actor_ref, command.query_id)
            if command.face_index >= len(capture.receipt.faces):
                raise HTTPException(422, "select a detected face")
            reasons = quality_reasons(capture.receipt.faces[command.face_index])
            page = await searched_page(session, workspace, actor, command, active, capture, reasons)
            await authorize_actor(session, workspace, actor, None)
            available(active)
            observation(session, workspace, actor, command.request_id)
    return page


async def searched_page(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: SearchCommand,
    runtime: SimilarityRuntime,
    capture: QueryCapture,
    reasons: tuple[str, ...],
) -> SimilarityPage:
    policy = runtime.policy
    if policy is None:
        raise RuntimeError("calibration unavailable")
    info: RepresentationInfo | None = None
    items: tuple[SimilarityCandidate, ...] = ()
    more, references, compatible = False, 0, 0
    state = "quality_blocked"
    if not reasons:
        info, vectors = await query_vectors(
            runtime, workspace, actor.actor_ref, capture, command.face_index
        )
        if not policy.query_matches(capture.receipt, info):
            raise RuntimeError("query representation incompatible with calibration")
        await authorize_actor(session, workspace, actor, None)
        rows = await pool(session, workspace, command.scope)
        binding = pool_binding(rows)
        scored = await score_references(runtime, rows, vectors, policy)
        references, compatible = len(rows), len(scored)
        items, more = confident_candidates(scored, policy)
        state = result_state(references, compatible, bool(items))
        await require_query_open(runtime, workspace, actor.actor_ref, capture.receipt)
        await recheck_catalogue(session, workspace, actor, command, runtime, binding)
    else:
        await require_query_open(runtime, workspace, actor.actor_ref, capture.receipt)
    return SimilarityPage.model_validate(
        {
            **command.model_dump(),
            "workspace_id": workspace,
            "policy_id": policy.policy_id,
            "evidence_sha256": policy.evidence_sha256,
            "representation": info,
            "state": state,
            "reasons": reasons,
            "reference_count": references,
            "compatible_count": compatible,
            "items": items,
            "has_more": more,
        }
    )


def result_state(references: int, compatible: int, candidates: bool) -> str:
    if not references:
        return "empty_catalogue"
    if not compatible:
        return "no_compatible_references"
    return "candidate_review" if candidates else "no_confident_match"


async def recheck_catalogue(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: SearchCommand,
    runtime: SimilarityRuntime,
    binding: tuple[tuple[UUID, UUID, UUID | None], ...],
) -> None:
    await authorize_actor(session, workspace, actor, None)
    available(runtime)
    if binding != pool_binding(await pool(session, workspace, command.scope)):
        raise ConflictError("reference catalogue changed during similarity query")


async def clear(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    query: UUID,
    runtime: SimilarityRuntime | None,
) -> ClearReceipt:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        if runtime is None:
            raise RuntimeError("query storage unavailable")
        keys = tuple(query_key(workspace, actor.actor_ref, query, part) for part in range(11))
        await runtime.store.close(keys, datetime.now(UTC) + timedelta(minutes=10))
        observation(session, workspace, actor, query)
    return ClearReceipt(workspace_id=workspace, query_id=query)


async def thumbnail(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    query: UUID,
    runtime: SimilarityRuntime | None,
) -> bytes:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        if runtime is None:
            raise RuntimeError("query storage unavailable")
        capture = await load_query(runtime, workspace, actor.actor_ref, query)
        await authorize_actor(session, workspace, actor, None)
        observation(session, workspace, actor, query)
    return capture.thumbnail
