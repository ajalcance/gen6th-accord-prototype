"""Private internal handoff routes; no messages, notifications or model approval."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas import investigation_reviews as service
from accord.personas.investigation_contracts import InvestigationHistory
from accord.personas.investigation_review_contracts import (
    InvestigationReviewCommand,
    InvestigationReviewPage,
    InvestigationReviewReceipt,
)
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.similarity_http import authorized_intent
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.write_http import PrivateWriteRoute


def create_review_router(verifier: PersonaSessionVerifier | None) -> APIRouter:
    router = APIRouter(prefix="/review-requests", route_class=PrivateWriteRoute)

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    @router.post("/request", response_model=InvestigationReviewReceipt)
    async def request_review(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> InvestigationReviewReceipt:
        command = await authorized_intent(
            session, workspace_id, who, request, InvestigationReviewCommand
        )
        return await service.request_review(session, workspace_id, who, command)

    @router.post("/history", response_model=InvestigationReviewPage)
    async def history(
        workspace_id: UUID,
        request: Request,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> InvestigationReviewPage:
        command = await authorized_intent(session, workspace_id, who, request, InvestigationHistory)
        return await service.history(session, workspace_id, who, command)

    return router
