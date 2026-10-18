"""Opt-in session-bound lifecycle routes, authorisation before bounded body parsing."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas import lifecycle_reads, lifecycle_service
from accord.personas.credit_intent import authorized_credit_intent
from accord.personas.lifecycle_contracts import (
    AppendLifecycle,
    LifecycleHistory,
    LifecyclePage,
    LifecycleProfile,
    LifecycleReceipt,
    Subject,
)
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.write_http import PrivateWriteRoute


def create_lifecycle_router(
    verifier: PersonaSessionVerifier | None, enabled: bool = False
) -> APIRouter:
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas/lifecycle", route_class=PrivateWriteRoute
    )

    async def actor(request: Request) -> WorkflowActor:
        who = await resolve_actor(request, verifier)
        if not enabled:
            raise RuntimeError("performer lifecycle persistence is not configured")
        return who

    @router.post("/read", response_model=LifecycleProfile)
    async def read(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> LifecycleProfile:
        command = await authorized_credit_intent(session, workspace_id, who, request, Subject)
        return await lifecycle_reads.read(session, workspace_id, who, command)

    @router.post("/append", response_model=LifecycleReceipt)
    async def append(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> LifecycleReceipt:
        command = await authorized_credit_intent(
            session, workspace_id, who, request, AppendLifecycle
        )
        return await lifecycle_service.append(session, workspace_id, who, command)

    @router.post("/history", response_model=LifecyclePage)
    async def history(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> LifecyclePage:
        command = await authorized_credit_intent(
            session, workspace_id, who, request, LifecycleHistory
        )
        return await lifecycle_reads.history(session, workspace_id, who, command)

    return router
