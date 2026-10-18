"""Configured capability observation, never a live readiness or benchmark certification."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.runtime_bootstrap import PersonaRuntime
from accord.personas.runtime_contracts import RuntimeReadiness
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.similarity_service import observation
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor
from accord.personas.write_http import PrivateWriteRoute


def configured(workspace: UUID, runtime: PersonaRuntime) -> RuntimeReadiness:
    if runtime.jobs is not None and runtime.jobs.workspace_id != workspace:
        return RuntimeReadiness(
            workspace_id=workspace,
            face_jobs_configured=False,
            search_configured=False,
            investigation_configured=False,
            signing_configured=False,
            verification_configured=False,
        )
    policy = runtime.similarity.policy if runtime.similarity else None
    search = bool(policy and policy.reviewed_at <= datetime.now(UTC) < policy.expires_at)
    passport = runtime.passports
    return RuntimeReadiness(
        workspace_id=workspace,
        face_jobs_configured=bool(runtime.jobs and runtime.jobs.workspace_id == workspace),
        search_configured=search,
        investigation_configured=bool(
            search and runtime.investigation and runtime.investigation.provider
        ),
        signing_configured=bool(
            passport and passport.signer and passport.trust.contains(passport.signer.key_id)
        ),
        verification_configured=bool(passport and passport.trust.available()),
    )


def create_runtime_router(
    verifier: PersonaSessionVerifier | None, runtime: PersonaRuntime
) -> APIRouter:
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas/runtime", route_class=PrivateWriteRoute
    )

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    @router.post("/readiness", response_model=RuntimeReadiness)
    async def readiness(
        workspace_id: UUID,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> RuntimeReadiness:
        async with tracked_transaction(session, workspace_id, who.actor_ref, uuid4()):
            await authorize_actor(session, workspace_id, who, None)
            result = configured(workspace_id, runtime)
            observation(session, workspace_id, who, uuid4())
        return result

    return router
