"""Real record writes with server-verified sessions; no credential fallback."""

from collections.abc import Awaitable, Callable, Coroutine
from typing import Annotated, Self
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import model_validator
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.logger import logger
from accord.personas.campaign_contracts import (
    CampaignDecisionCommand,
    CampaignDecisionReceipt,
    CampaignReceipt,
    OfferCampaignCommand,
)
from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaigns import offer_campaign
from accord.personas.contracts import PersonaVersion
from accord.personas.read_http import ReadError, read_error
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.reviews import record_review
from accord.personas.service import SaveCommand, save
from accord.personas.session_boundary import (
    PersonaSessionVerifier,
    SessionDeniedError,
    SessionUnavailableError,
    resolve_actor,
)
from accord.personas.workflow_contracts import ReviewCommand, ReviewSnapshot, WorkflowActor


class VersionSaveIntent(SaveCommand):
    @model_validator(mode="after")
    def initial_revision(self) -> Self:
        if self.persona_id is None and self.expected_revision != 0:
            raise ValueError("new personas require revision zero")
        if self.persona_id is None and self.photo.action != "attach":
            raise ValueError("new registrations require an inspected portrait attachment")
        return self


class PrivateWriteRoute(APIRoute):
    """Return bounded errors without exposing drafts, database errors or identity details."""

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
                response = read_error(403, "access_denied", "This action is not permitted.")
            except ConflictError:
                response = read_error(
                    409, "write_conflict", "The record or request intent changed."
                )
            except RequestValidationError:
                response = read_error(422, "invalid_intent", "The write intent is invalid.")
            except HTTPException as exc:
                response = read_error(
                    exc.status_code, "request_rejected", "The request was rejected."
                )
            except (DBAPIError, RuntimeError):
                logger.error("persona write unavailable (incident_id=%s)", uuid4())
                response = read_error(503, "write_unavailable", "The write outcome is unavailable.")
            except Exception:
                logger.error("persona write failed (incident_id=%s)", uuid4())
                response = read_error(
                    500, "write_failed", "The write outcome could not be confirmed."
                )
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
            return response

        return protected


def create_write_router(verifier: PersonaSessionVerifier | None = None) -> APIRouter:
    """Require reviewed identity/origin/CSRF/credential setup before any live mounting."""
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas",
        tags=["persona writes"],
        route_class=PrivateWriteRoute,
        responses={code: {"model": ReadError} for code in (401, 403, 409, 422, 500, 503)},
    )

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    register_version_write(router, actor)
    register_review_write(router, actor)
    register_campaign_writes(router, actor)
    return router


ActorDependency = Callable[[Request], Awaitable[WorkflowActor]]


def register_version_write(router: APIRouter, actor: ActorDependency) -> None:
    @router.post("/versions/save", response_model=PersonaVersion)
    async def version_save(
        workspace_id: UUID,
        command: VersionSaveIntent,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> PersonaVersion:
        return await save(session, workspace_id, who.actor_ref, command)


def register_review_write(router: APIRouter, actor: ActorDependency) -> None:
    @router.post("/reviews/record", response_model=ReviewSnapshot)
    async def review_record(
        workspace_id: UUID,
        command: ReviewCommand,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> ReviewSnapshot:
        return await record_review(session, workspace_id, who, command)


def register_campaign_writes(router: APIRouter, actor: ActorDependency) -> None:
    @router.post("/campaigns/offer", response_model=CampaignReceipt)
    async def campaign_offer(
        workspace_id: UUID,
        command: OfferCampaignCommand,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> CampaignReceipt:
        return await offer_campaign(session, workspace_id, who, command)

    @router.post("/campaigns/decide", response_model=CampaignDecisionReceipt)
    async def campaign_decide(
        workspace_id: UUID,
        command: CampaignDecisionCommand,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> CampaignDecisionReceipt:
        return await decide_campaign(session, workspace_id, who, command)
