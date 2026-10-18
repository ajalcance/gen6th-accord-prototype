"""Verified private analysis/readiness/history routes; no browser findings or actor inputs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas import investigation_service as service
from accord.personas.investigation_contracts import (
    InvestigationCommand,
    InvestigationHistory,
    InvestigationPage,
    InvestigationReadiness,
    InvestigationResult,
)
from accord.personas.investigation_provider import InvestigationRuntime
from accord.personas.investigation_review_http import create_review_router
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.similarity_http import authorized_intent
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.write_http import PrivateWriteRoute


def create_investigation_router(
    verifier: PersonaSessionVerifier | None, runtime: InvestigationRuntime | None
) -> APIRouter:
    router = APIRouter(
        prefix="/investigations", tags=["persona investigations"], route_class=PrivateWriteRoute
    )
    router.include_router(create_review_router(verifier))

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    @router.post("/readiness", response_model=InvestigationReadiness)
    async def readiness(
        workspace_id: UUID,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> InvestigationReadiness:
        return await service.readiness(session, workspace_id, who, runtime)

    @router.post("/generate", response_model=InvestigationResult)
    async def generate(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> InvestigationResult:
        command = await authorized_intent(session, workspace_id, who, request, InvestigationCommand)
        return await service.generate(session, workspace_id, who, command, runtime)

    @router.post("/history", response_model=InvestigationPage)
    async def history(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> InvestigationPage:
        command = await authorized_intent(session, workspace_id, who, request, InvestigationHistory)
        return await service.read_history(session, workspace_id, who, command, runtime)

    return router
