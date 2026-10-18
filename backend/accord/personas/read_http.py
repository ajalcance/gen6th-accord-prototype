"""Real record queries, gated by a configured Zynth session verifier.

Queries use POST because successful reads commit audit observations. There are no GET
record routes, grants, writes, uploads or test-verifier defaults here.
"""

from collections.abc import Callable, Coroutine
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.logger import logger
from accord.personas.contracts import PersonaVersion
from accord.personas.gallery import GalleryPage, GalleryQuery, list_gallery
from accord.personas.repository import AccessDeniedError
from accord.personas.service import load
from accord.personas.session_boundary import (
    PersonaSessionVerifier,
    SessionDeniedError,
    SessionUnavailableError,
    resolve_actor,
)
from accord.personas.workflow_contracts import WorkflowActor


class VersionQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    persona_id: UUID
    revision: int | None = Field(default=None, ge=1, strict=True)


class ReadErrorDetail(BaseModel):
    code: str
    message: str


class ReadError(BaseModel):
    error: ReadErrorDetail


def read_error(status: int, code: str, message: str) -> JSONResponse:
    body = ReadError(error=ReadErrorDetail(code=code, message=message))
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else {}
    return JSONResponse(body.model_dump(), status_code=status, headers=headers)


class PrivateReadRoute(APIRoute):
    """Sanitize errors locally; successful and failed responses are never cached."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[object, object, Response]]:
        original = super().get_route_handler()

        async def protected(request: Request) -> Response:
            try:
                response = await original(request)
            except SessionUnavailableError:
                response = read_error(
                    503, "session_unavailable", "Trusted sessions are unavailable."
                )
            except SessionDeniedError:
                response = read_error(
                    401, "session_required", "A current human session is required."
                )
            except AccessDeniedError:
                response = read_error(403, "access_denied", "Record access is unavailable.")
            except RequestValidationError:
                response = read_error(422, "invalid_query", "The read query is invalid.")
            except HTTPException as exc:
                response = read_error(
                    exc.status_code, "request_rejected", "The request was rejected."
                )
            except Exception:
                logger.error("persona read request failed (incident_id=%s)", uuid4())
                response = read_error(
                    503, "read_unavailable", "Saved records are temporarily unavailable."
                )
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
            return response

        return protected


def create_read_router(verifier: PersonaSessionVerifier | None = None) -> APIRouter:
    """Caller must explicitly review/configure a verifier before mounting this router."""
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas",
        tags=["persona reads"],
        route_class=PrivateReadRoute,
        responses={code: {"model": ReadError} for code in (401, 403, 422, 503)},
    )

    async def trusted_actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    @router.post("/query", response_model=GalleryPage)
    async def gallery_query(
        workspace_id: UUID,
        query: GalleryQuery,
        actor: Annotated[WorkflowActor, Depends(trusted_actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> GalleryPage:
        return await list_gallery(session, workspace_id, actor, query)

    @router.post("/versions/query", response_model=PersonaVersion)
    async def version_query(
        workspace_id: UUID,
        query: VersionQuery,
        actor: Annotated[WorkflowActor, Depends(trusted_actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> PersonaVersion:
        return await load(session, workspace_id, actor.actor_ref, query.persona_id, query.revision)

    return router
