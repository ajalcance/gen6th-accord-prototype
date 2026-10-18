"""Session-gated portrait search; private responses reuse the bounded intake wire format."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.photo_contracts import PhotoRejectedError
from accord.personas.portrait_search import PortraitSearchPage, search_portraits
from accord.personas.read_http import read_error
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.write_http import PrivateWriteRoute


def create_portrait_search_router(verifier: PersonaSessionVerifier | None) -> APIRouter:
    router = APIRouter(
        tags=["persona portrait search"],
        route_class=PrivateWriteRoute,
    )

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    @router.post("/search", response_model=PortraitSearchPage)
    async def search(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> PortraitSearchPage | Response:
        try:
            return await search_portraits(session, workspace_id, who, request.stream())
        except PhotoRejectedError:
            return read_error(422, "invalid_search", "Use a PNG or JPEG file within 10 MB.")

    return router
