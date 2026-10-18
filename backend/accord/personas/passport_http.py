"""Bounded private package verification; uploaded statements are never sealed as server facts."""

import asyncio
import json
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas import passport_repository as repository
from accord.personas import passport_service as service
from accord.personas.passport_contracts import (
    AssetPage,
    AssetQuery,
    PassportReadiness,
    PassportSubject,
    PassportVerification,
    SignedPassport,
    VerifyPassport,
)
from accord.personas.passport_signing import MAX_PACKAGE_BYTES, PassportRuntime
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.similarity_http import ActorResolver
from accord.personas.similarity_service import observation
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor
from accord.personas.write_http import PrivateWriteRoute


def distinct_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


async def intent[Intent: BaseModel](
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
        data = bytearray()
        try:
            async with asyncio.timeout(5):
                async for chunk in request.stream():
                    data.extend(chunk)
                    if len(data) > MAX_PACKAGE_BYTES:
                        raise ValueError("package exceeds bound")
            result = model.model_validate(json.loads(data, object_pairs_hook=distinct_keys))
        except (ValidationError, ValueError, RecursionError, TimeoutError) as exc:
            raise HTTPException(422, "invalid passport intent") from exc
        observation(session, workspace, actor, uuid4())
    return result


def create_passport_router(
    verifier: PersonaSessionVerifier | None = None, runtime: PassportRuntime | None = None
) -> APIRouter:
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas/passports",
        tags=["persona passports"],
        route_class=PrivateWriteRoute,
    )

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    register_readiness(router, actor, runtime)

    @router.post("/assets", response_model=AssetPage)
    async def assets(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> AssetPage:
        command = await intent(session, workspace_id, who, request, AssetQuery)
        return await repository.assets(session, workspace_id, who, command.version_id)

    @router.post("/export", response_model=SignedPassport)
    async def export(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> SignedPassport:
        command = await intent(session, workspace_id, who, request, PassportSubject)
        return await service.export(session, workspace_id, who, command.campaign_id, runtime)

    @router.post("/verify", response_model=PassportVerification)
    async def verify(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> PassportVerification:
        command = await intent(session, workspace_id, who, request, VerifyPassport)
        return await service.verify(session, workspace_id, who, command, runtime)

    return router


def register_readiness(
    router: APIRouter, actor: ActorResolver, runtime: PassportRuntime | None
) -> None:
    @router.post("/readiness", response_model=PassportReadiness)
    async def readiness(
        workspace_id: UUID,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> PassportReadiness:
        return await service.readiness(session, workspace_id, who, runtime)
