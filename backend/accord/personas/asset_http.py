"""Bounded private enrollment commands with server-attributed ownership."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.asset_contracts import EnrollAsset, EnrolledAsset
from accord.personas.asset_service import enroll
from accord.personas.passport_http import intent
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.write_http import PrivateWriteRoute


def create_asset_router(verifier: PersonaSessionVerifier | None = None) -> APIRouter:
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas/assets", route_class=PrivateWriteRoute
    )

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    @router.post("/enroll", response_model=EnrolledAsset)
    async def enrollment(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> EnrolledAsset:
        command = await intent(session, workspace_id, who, request, EnrollAsset)
        return await enroll(session, workspace_id, who, command)

    return router
