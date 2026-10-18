"""Opt-in workspace-only credit routes; existing sessions, body bounds and denial handling."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas import credit_service as service
from accord.personas.credit_contracts import (
    ConfirmCredit,
    CreditConfirmation,
    CreditProfile,
    CreditSnapshot,
    CreditSubject,
    SaveCredits,
)
from accord.personas.credit_intent import authorized_credit_intent
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.write_http import PrivateWriteRoute


def create_credit_router(
    verifier: PersonaSessionVerifier | None, enabled: bool = False
) -> APIRouter:
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas/credits", route_class=PrivateWriteRoute
    )

    async def actor(request: Request) -> WorkflowActor:
        who = await resolve_actor(request, verifier)
        if not enabled:
            raise RuntimeError("credit persistence is not configured")
        return who

    @router.post("/read", response_model=CreditProfile)
    async def read(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> CreditProfile:
        command = await authorized_credit_intent(session, workspace_id, who, request, CreditSubject)
        return await service.read(session, workspace_id, who, command)

    @router.post("/save", response_model=CreditSnapshot)
    async def save(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> CreditSnapshot:
        command = await authorized_credit_intent(session, workspace_id, who, request, SaveCredits)
        return await service.save(session, workspace_id, who, command)

    @router.post("/confirm", response_model=CreditConfirmation)
    async def confirm(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> CreditConfirmation:
        command = await authorized_credit_intent(session, workspace_id, who, request, ConfirmCredit)
        return await service.confirm(session, workspace_id, who, command)

    return router
