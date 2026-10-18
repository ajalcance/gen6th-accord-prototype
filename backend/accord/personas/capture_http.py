"""Thin private metadata query attached to the existing persona photo resource."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.capture_contracts import CaptureProfile, CaptureQuery
from accord.personas.capture_reads import capture_profile
from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.photo_reads import reference_thumbnail
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.write_http import PrivateWriteRoute


def create_capture_router(
    verifier: PersonaSessionVerifier | None, wrapper: KeyWrapper | None
) -> APIRouter:
    router = APIRouter(route_class=PrivateWriteRoute)

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    @router.post("/capture/query", response_model=CaptureProfile)
    async def query(
        workspace_id: UUID,
        command: CaptureQuery,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> CaptureProfile:
        return await capture_profile(session, workspace_id, who.actor_ref, command)

    @router.get("/versions/{version_id}/references/{portrait_id}/thumbnail")
    async def thumbnail(
        workspace_id: UUID,
        version_id: UUID,
        portrait_id: UUID,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> Response:
        data = await reference_thumbnail(
            session, workspace_id, who.actor_ref, version_id, portrait_id, wrapper
        )
        return Response(
            data,
            media_type="image/png",
            headers={
                "Cache-Control": "private, no-store",
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'none'; sandbox",
            },
        )

    return router
