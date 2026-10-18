"""Private raw-byte intake; trusted sessions and exact owner authorization precede consumption."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.evidence_contracts import EvidenceIntent, EvidenceSnapshot, MediaType
from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.evidence_service import (
    ContentInspector,
    RetentionGate,
    enqueue,
    inspect_evidence,
    purge_expired,
    read_document,
)
from accord.personas.passport_http import intent as bounded_intent
from accord.personas.photo_contracts import PhotoRejectedError
from accord.personas.photo_http import PRIVATE_PHOTO_HEADERS
from accord.personas.read_http import read_error
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.similarity_service import observation
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor, has_role
from accord.personas.write_http import ActorDependency, PrivateWriteRoute


class EvidenceSubject(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    evidence_id: UUID


class EvidenceCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    upload_available: bool
    inspection_available: bool
    download_available: bool
    purge_available: bool


def create_evidence_router(
    verifier: PersonaSessionVerifier | None = None,
    wrapper: KeyWrapper | None = None,
    inspector: ContentInspector | None = None,
    retention: RetentionGate | None = None,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas/evidence",
        route_class=PrivateWriteRoute,
    )

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    register_readiness(router, actor, wrapper, inspector, retention)
    register_upload(router, actor, wrapper)
    register_inspection(router, actor, wrapper, inspector)
    register_content_routes(router, actor, wrapper, retention)
    return router


def register_upload(router: APIRouter, actor: ActorDependency, wrapper: KeyWrapper | None) -> None:

    @router.post("/upload/{version_id}", response_model=EvidenceSnapshot)
    async def upload(
        workspace_id: UUID,
        version_id: UUID,
        request: Request,
        request_id: Annotated[UUID, Header(alias="X-Request-ID")],
        digest: Annotated[str, Header(alias="X-Content-SHA256")],
        length: Annotated[int, Header(alias="X-Evidence-Length")],
        media: Annotated[MediaType, Header(alias="Content-Type")],
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> EvidenceSnapshot | Response:
        if wrapper is None:
            raise RuntimeError("evidence encryption unavailable")
        try:
            intent = EvidenceIntent(
                request_id=request_id,
                version_id=version_id,
                media_type=media,
                byte_length=length,
                sha256=digest,
            )
            return await enqueue(session, workspace_id, who, intent, request.stream(), wrapper)
        except ValueError:
            return read_error(422, "invalid_evidence", "Evidence bytes or metadata disagree.")


def register_inspection(
    router: APIRouter,
    actor: ActorDependency,
    wrapper: KeyWrapper | None,
    inspector: ContentInspector | None,
) -> None:

    @router.post("/inspect", response_model=EvidenceSnapshot)
    async def inspect(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> EvidenceSnapshot | Response:
        if wrapper is None or inspector is None:
            raise RuntimeError("evidence inspection unavailable")
        command = await bounded_intent(session, workspace_id, who, request, EvidenceSubject)
        try:
            return await inspect_evidence(
                session, workspace_id, who, command.evidence_id, wrapper, inspector
            )
        except (ValueError, PhotoRejectedError):
            return read_error(422, "evidence_rejected", "Evidence could not pass inspection.")


def register_readiness(
    router: APIRouter,
    actor: ActorDependency,
    wrapper: KeyWrapper | None,
    inspector: ContentInspector | None,
    retention: RetentionGate | None,
) -> None:
    @router.post("/readiness", response_model=EvidenceCapabilities)
    async def readiness(
        workspace_id: UUID,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> EvidenceCapabilities:
        from uuid import uuid4

        async with tracked_transaction(session, workspace_id, who.actor_ref, uuid4()):
            await authorize_actor(session, workspace_id, who, None)
            creator = await has_role(session, workspace_id, who.actor_ref, "creator")
            observation(session, workspace_id, who, uuid4())
        return EvidenceCapabilities(
            workspace_id=workspace_id,
            upload_available=creator and wrapper is not None,
            inspection_available=creator and wrapper is not None and inspector is not None,
            download_available=creator and wrapper is not None,
            purge_available=creator and retention is not None,
        )


def register_content_routes(
    router: APIRouter,
    actor: ActorDependency,
    wrapper: KeyWrapper | None,
    retention: RetentionGate | None,
) -> None:
    @router.post("/content")
    async def content(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> Response:
        if wrapper is None:
            raise RuntimeError("evidence encryption unavailable")
        command = await bounded_intent(session, workspace_id, who, request, EvidenceSubject)
        metadata, data = await read_document(
            session, workspace_id, who, command.evidence_id, wrapper
        )
        return Response(
            data,
            media_type="application/octet-stream",
            headers={
                **PRIVATE_PHOTO_HEADERS,
                "Content-Disposition": 'attachment; filename="private-evidence.bin"',
                "X-Content-SHA256": metadata.sha256,
            },
        )

    @router.post("/purge", response_model=EvidenceSnapshot)
    async def purge(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> EvidenceSnapshot:
        if retention is None:
            raise RuntimeError("trusted retention authority unavailable")
        command = await bounded_intent(session, workspace_id, who, request, EvidenceSubject)
        return await purge_expired(session, workspace_id, who, command.evidence_id, retention)
