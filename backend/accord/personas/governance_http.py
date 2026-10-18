"""Session-gated real governance queries; no fallback identities or grants."""

from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.campaign_contracts import (
    CampaignDecisionPage,
    CampaignHistoryQuery,
    CampaignStatus,
)
from accord.personas.campaign_history import campaign_history
from accord.personas.campaign_status import inspect_campaign
from accord.personas.evidence_contracts import EvidenceSnapshot
from accord.personas.evidence_status import evidence_status
from accord.personas.governance_contracts import (
    CampaignPage,
    EvidencePage,
    VersionHistoryQuery,
    VersionObjectsQuery,
    VersionPage,
)
from accord.personas.governance_index import campaign_offers, evidence_list
from accord.personas.read_http import PrivateReadRoute, ReadError
from accord.personas.reviews import review_history
from accord.personas.session_boundary import PersonaSessionVerifier, resolve_actor
from accord.personas.version_history import version_history
from accord.personas.workflow_contracts import ReviewHistoryQuery, ReviewPage, WorkflowActor
from accord.personas.workflow_evidence import inspect_workflow_evidence
from accord.personas.workflow_evidence_contracts import RecordKind, WorkflowEvidence

ActorDependency = Callable[[Request], Awaitable[WorkflowActor]]


class CampaignStatusQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    campaign_id: UUID


class EvidenceStatusQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    evidence_id: UUID


class WorkflowEvidenceQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_id: UUID
    kind: RecordKind


def create_governance_read_router(verifier: PersonaSessionVerifier | None = None) -> APIRouter:
    router = APIRouter(
        prefix="/api/workspaces/{workspace_id}/personas",
        tags=["governance reads"],
        route_class=PrivateReadRoute,
        responses={code: {"model": ReadError} for code in (401, 403, 422, 503)},
    )

    async def actor(request: Request) -> WorkflowActor:
        return await resolve_actor(request, verifier)

    register_version_reads(router, actor)
    register_decision_reads(router, actor)
    register_evidence_reads(router, actor)
    return router


def register_version_reads(router: APIRouter, actor: ActorDependency) -> None:
    @router.post("/versions/history/query", response_model=VersionPage)
    async def versions(
        workspace_id: UUID,
        query: VersionHistoryQuery,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> VersionPage:
        return await version_history(session, workspace_id, who, query)

    @router.post("/reviews/history/query", response_model=ReviewPage)
    async def reviews(
        workspace_id: UUID,
        query: ReviewHistoryQuery,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> ReviewPage:
        return await review_history(session, workspace_id, who, query)

    @router.post("/campaigns/query", response_model=CampaignPage)
    async def offers(
        workspace_id: UUID,
        query: VersionObjectsQuery,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> CampaignPage:
        return await campaign_offers(session, workspace_id, who, query)


def register_decision_reads(router: APIRouter, actor: ActorDependency) -> None:
    @router.post("/campaigns/history/query", response_model=CampaignDecisionPage)
    async def decisions(
        workspace_id: UUID,
        query: CampaignHistoryQuery,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> CampaignDecisionPage:
        return await campaign_history(session, workspace_id, who, query)

    @router.post("/campaigns/status/query", response_model=CampaignStatus)
    async def status(
        workspace_id: UUID,
        query: CampaignStatusQuery,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> CampaignStatus:
        return await inspect_campaign(session, workspace_id, who, query.campaign_id)

    @router.post("/workflow/evidence/query", response_model=WorkflowEvidence)
    async def evidence(
        workspace_id: UUID,
        query: WorkflowEvidenceQuery,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> WorkflowEvidence:
        return await inspect_workflow_evidence(
            session, workspace_id, who, query.record_id, query.kind
        )


def register_evidence_reads(router: APIRouter, actor: ActorDependency) -> None:
    @router.post("/evidence/query", response_model=EvidencePage)
    async def items(
        workspace_id: UUID,
        query: VersionObjectsQuery,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> EvidencePage:
        return await evidence_list(session, workspace_id, who, query)

    @router.post("/evidence/status/query", response_model=EvidenceSnapshot)
    async def status(
        workspace_id: UUID,
        query: EvidenceStatusQuery,
        who: Annotated[WorkflowActor, Depends(actor)],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> EvidenceSnapshot:
        return await evidence_status(session, workspace_id, who, query.evidence_id)
