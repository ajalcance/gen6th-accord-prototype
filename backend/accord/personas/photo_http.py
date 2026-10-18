"""Thin photo routes reuse current verified sessions and private bounded responses."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.capture_http import create_capture_router
from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.face_http import create_face_router
from accord.personas.face_providers import FaceProviders
from accord.personas.investigation_http import create_investigation_router
from accord.personas.investigation_provider import InvestigationRuntime
from accord.personas.photo_contracts import PhotoReceipt, PhotoRejectedError
from accord.personas.photo_inspector import PhotoInspector
from accord.personas.photo_intake import intake
from accord.personas.photo_reads import thumbnail
from accord.personas.portrait_search_http import create_portrait_search_router
from accord.personas.read_http import read_error
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.similarity_http import create_similarity_router
from accord.personas.similarity_query import SimilarityRuntime
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.write_http import PrivateWriteRoute

PRIVATE_PHOTO_HEADERS = {
    "Cache-Control": "private, no-store",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; sandbox",
}


def create_photo_router(
    verifier: PersonaSessionVerifier | None = None,
    inspector: PhotoInspector | None = None,
    wrapper: KeyWrapper | None = None,
    faces: FaceProviders | None = None,
    similarity: SimilarityRuntime | None = None,
    investigation: InvestigationRuntime | None = None,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas/photos",
        tags=["persona photos"],
        route_class=PrivateWriteRoute,
    )

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    @router.post("/upload", response_model=PhotoReceipt)
    async def upload(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> PhotoReceipt | Response:
        try:
            return await intake(
                session, workspace_id, who.actor_ref, request.stream(), inspector, wrapper
            )
        except PhotoRejectedError:
            return read_error(
                422, "photo_rejected", "Use a valid, safe PNG or JPEG within the limits."
            )

    @router.get("/versions/{version_id}/thumbnail")
    async def read_thumbnail(
        workspace_id: UUID,
        version_id: UUID,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> Response:
        data = await thumbnail(session, workspace_id, who.actor_ref, version_id, wrapper)
        return Response(
            data,
            status_code=200 if data is not None else 204,
            media_type="image/png",
            headers=PRIVATE_PHOTO_HEADERS,
        )

    include_processing(router, verifier, wrapper, faces, similarity, investigation)
    return router


def include_processing(
    router: APIRouter,
    verifier: PersonaSessionVerifier | None,
    wrapper: KeyWrapper | None,
    faces: FaceProviders | None,
    similarity: SimilarityRuntime | None,
    investigation: InvestigationRuntime | None,
) -> None:
    router.include_router(create_portrait_search_router(verifier))
    router.include_router(create_capture_router(verifier, wrapper))
    router.include_router(create_face_router(verifier, wrapper, faces))
    router.include_router(create_similarity_router(verifier, similarity))
    router.include_router(create_investigation_router(verifier, investigation))
