"""Three thin private routes; no image query enrollment, vector response or browser coordinates."""

import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.face_contracts import FaceCommand, FaceProfile, FaceResult, FaceSubject
from accord.personas.face_providers import FaceProviders
from accord.personas.face_service import process, profile
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.write_http import PrivateWriteRoute


async def bounded_intent[Intent: BaseModel](request: Request, model: type[Intent]) -> Intent:
    """Read small metadata only after the actor dependency verifies the current session."""
    data = bytearray()
    try:
        async with asyncio.timeout(5):
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data) > 4096:
                    raise HTTPException(422, "face intent exceeds the bound")
        return model.model_validate_json(data)
    except (ValidationError, TimeoutError) as exc:
        raise HTTPException(422, "invalid face intent") from exc


def create_face_router(
    verifier: PersonaSessionVerifier | None,
    wrapper: KeyWrapper | None,
    providers: FaceProviders | None,
) -> APIRouter:
    router = APIRouter(route_class=PrivateWriteRoute)

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    @router.post("/faces/query", response_model=FaceProfile)
    async def query(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> FaceProfile:
        command = await bounded_intent(request, FaceSubject)
        return await profile(session, workspace_id, who.actor_ref, command, wrapper, providers)

    @router.post("/faces/process", response_model=FaceResult)
    async def analyze(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> FaceResult:
        command = await bounded_intent(request, FaceCommand)
        return await process(session, workspace_id, who.actor_ref, command, wrapper, providers)

    return router
