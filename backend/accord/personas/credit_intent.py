"""Bound credit metadata after membership checks; no image/document bytes are accepted."""

import asyncio
from uuid import UUID, uuid4

from fastapi import HTTPException, Request
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.similarity_service import observation
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor


async def authorized_credit_intent[Intent: BaseModel](
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
                    if len(data) + len(chunk) > 12288:
                        raise HTTPException(422, "credit intent exceeds its bound")
                    data.extend(chunk)
            result = model.model_validate_json(data)
        except (ValidationError, TimeoutError) as exc:
            raise HTTPException(422, "invalid credit intent") from exc
        observation(session, workspace, actor, uuid4())
    return result
