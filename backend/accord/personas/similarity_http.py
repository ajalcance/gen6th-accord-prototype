"""Thin private query lifecycle routes with verified membership before even metadata input."""

from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas import similarity_service as service
from accord.personas.face_http import bounded_intent
from accord.personas.photo_contracts import PhotoRejectedError
from accord.personas.read_http import read_error
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.similarity_contracts import (
    ClearReceipt,
    QueryReceipt,
    QuerySubject,
    SearchCommand,
    SimilarityPage,
    SimilarityReadiness,
)
from accord.personas.similarity_query import SimilarityRuntime
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor
from accord.personas.write_http import PrivateWriteRoute


async def authorized_intent[Intent: BaseModel](
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    request: Request,
    model: type[Intent],
) -> Intent:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        command = await bounded_intent(request, model)
        service.observation(session, workspace, actor, uuid4())
    return command


def create_similarity_router(
    verifier: PersonaSessionVerifier | None, runtime: SimilarityRuntime | None
) -> APIRouter:
    router = APIRouter(
        prefix="/similarity", tags=["persona similarity"], route_class=PrivateWriteRoute
    )

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    register_query_routes(router, actor, runtime)
    register_read_routes(router, actor, runtime)
    return router


ActorResolver = Callable[[Request], Awaitable[WorkflowActor]]


def register_query_routes(
    router: APIRouter, actor: ActorResolver, runtime: SimilarityRuntime | None
) -> None:
    @router.post("/prepare", response_model=QueryReceipt)
    async def prepare(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> QueryReceipt | Response:
        try:
            return await service.prepare(session, workspace_id, who, request.stream(), runtime)
        except PhotoRejectedError:
            return read_error(422, "query_rejected", "Use a safe PNG or JPEG within 10 MB.")

    @router.post("/search", response_model=SimilarityPage)
    async def search(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> SimilarityPage:
        command = await authorized_intent(session, workspace_id, who, request, SearchCommand)
        return await service.search(session, workspace_id, who, command, runtime)

    @router.post("/clear", response_model=ClearReceipt)
    async def clear(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> ClearReceipt:
        command = await authorized_intent(session, workspace_id, who, request, QuerySubject)
        return await service.clear(session, workspace_id, who, command.query_id, runtime)


def register_read_routes(
    router: APIRouter, actor: ActorResolver, runtime: SimilarityRuntime | None
) -> None:
    @router.post("/readiness", response_model=SimilarityReadiness)
    async def readiness(
        workspace_id: UUID,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> SimilarityReadiness:
        return await service.readiness(session, workspace_id, who, runtime)

    @router.get("/queries/{query_id}/thumbnail")
    async def thumbnail(
        workspace_id: UUID,
        query_id: UUID,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> Response:
        return Response(
            await service.thumbnail(session, workspace_id, who, query_id, runtime),
            media_type="image/png",
            headers={
                "Cache-Control": "private, no-store",
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'none'; sandbox",
            },
        )
