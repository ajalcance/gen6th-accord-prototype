"""Separate owner approval and opt-in public reads; no private export is served anonymously."""

import asyncio
import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.passport_contracts import SignedPassport
from accord.personas.passport_http import distinct_keys, intent
from accord.personas.passport_signing import MAX_PACKAGE_BYTES, PassportRuntime
from accord.personas.photo_http import PRIVATE_PHOTO_HEADERS
from accord.personas.publication_contracts import (
    ApprovePublication,
    PublicationHistoryPage,
    PublicationHistoryQuery,
    PublicationPage,
    PublicationReceipt,
    PublicationSubject,
)
from accord.personas.publication_history import history
from accord.personas.publication_reads import inspect_public, public_portrait
from accord.personas.publication_service import approve, unpublish
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.write_http import PrivateWriteRoute


def create_publication_router(
    verifier: PersonaSessionVerifier | None = None, runtime: PassportRuntime | None = None
) -> APIRouter:
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas/publications", route_class=PrivateWriteRoute
    )

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    @router.post("/history", response_model=PublicationHistoryPage)
    async def records(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> PublicationHistoryPage:
        command = await intent(session, workspace_id, who, request, PublicationHistoryQuery)
        return await history(session, workspace_id, who, command)

    @router.post("/approve", response_model=PublicationReceipt)
    async def approval(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> PublicationReceipt:
        command = await intent(session, workspace_id, who, request, ApprovePublication)
        return await approve(session, workspace_id, who, command, runtime)

    @router.post("/unpublish", response_model=PublicationReceipt)
    async def withdrawal(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> PublicationReceipt:
        command = await intent(session, workspace_id, who, request, PublicationSubject)
        return await unpublish(session, workspace_id, who, command.publication_id)

    return router


def create_public_passport_router(
    runtime: PassportRuntime | None = None, wrapper: KeyWrapper | None = None, enabled: bool = False
) -> APIRouter:
    router = APIRouter(
        prefix="/api/public/passports/{workspace_id}/{publication_id}",
        route_class=PrivateWriteRoute,
    )

    async def gate() -> None:
        if not enabled:
            raise HTTPException(404, "public passports unavailable")

    @router.get("", response_model=PublicationPage, dependencies=[Depends(gate)])
    async def page(
        workspace_id: UUID, publication_id: UUID, session: Annotated[AsyncSession, Depends(get_db)]
    ) -> PublicationPage:
        return await inspect_public(session, workspace_id, publication_id, runtime)

    @router.post("/verify", response_model=PublicationPage, dependencies=[Depends(gate)])
    async def verify(
        workspace_id: UUID,
        publication_id: UUID,
        request: Request,
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> PublicationPage:
        raw = bytearray()
        try:
            async with asyncio.timeout(5):
                async for chunk in request.stream():
                    if len(chunk) > MAX_PACKAGE_BYTES - len(raw):
                        raise ValueError("public package exceeds bound")
                    raw.extend(chunk)
            package = SignedPassport.model_validate(
                json.loads(raw, object_pairs_hook=distinct_keys)
            )
        except (ValueError, RecursionError, TimeoutError) as exc:
            raise HTTPException(422, "invalid public package") from exc
        return await inspect_public(session, workspace_id, publication_id, runtime, package)

    @router.get("/portrait", dependencies=[Depends(gate)])
    async def portrait(
        workspace_id: UUID, publication_id: UUID, session: Annotated[AsyncSession, Depends(get_db)]
    ) -> Response:
        data = await public_portrait(session, workspace_id, publication_id, runtime, wrapper)
        return Response(data, media_type="image/png", headers=PRIVATE_PHOTO_HEADERS)

    return router
