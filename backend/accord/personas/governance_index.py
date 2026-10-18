"""Discover authorized offers and owner-only evidence metadata for an exact version."""

from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_models import CampaignOffer
from accord.personas.campaign_repository import campaign_receipt
from accord.personas.evidence_models import PrivateEvidence
from accord.personas.evidence_repository import inspection, snapshot
from accord.personas.governance_contracts import CampaignPage, EvidencePage, VersionObjectsQuery
from accord.personas.repository import AccessDeniedError
from accord.personas.transactions import tracked_transaction
from accord.personas.version_history import observe_history
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor, locked_version


async def campaign_offers(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, query: VersionObjectsQuery
) -> CampaignPage:
    request = uuid4()
    async with tracked_transaction(
        session, workspace, actor.actor_ref, request, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        await locked_version(session, workspace, query.version_id)
        statement = select(CampaignOffer).where(
            CampaignOffer.workspace_id == workspace,
            CampaignOffer.version_id == query.version_id,
            or_(
                CampaignOffer.owner_ref == actor.actor_ref,
                CampaignOffer.recipient_ref == actor.actor_ref,
            ),
        )
        if query.after_id is not None:
            statement = statement.where(CampaignOffer.id > query.after_id)
        rows = list(
            await session.scalars(statement.order_by(CampaignOffer.id).limit(query.limit + 1))
        )
        items = tuple([await campaign_receipt(session, row) for row in rows[: query.limit]])
        result = CampaignPage(
            items=items, next_after_id=items[-1].id if len(rows) > query.limit else None
        )
        session.add(observe_history(workspace, actor, request, query.version_id))
    return result


async def evidence_list(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, query: VersionObjectsQuery
) -> EvidencePage:
    request = uuid4()
    async with tracked_transaction(
        session, workspace, actor.actor_ref, request, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, "creator")
        version, persona = await locked_version(session, workspace, query.version_id)
        if persona.owner_ref != actor.actor_ref or version.creator_ref != actor.actor_ref:
            raise AccessDeniedError("private evidence access denied")
        statement = select(PrivateEvidence).where(
            PrivateEvidence.workspace_id == workspace,
            PrivateEvidence.version_id == query.version_id,
            PrivateEvidence.owner_ref == actor.actor_ref,
        )
        if query.after_id is not None:
            statement = statement.where(PrivateEvidence.id > query.after_id)
        rows = list(
            await session.scalars(statement.order_by(PrivateEvidence.id).limit(query.limit + 1))
        )
        items = []
        for row in rows[: query.limit]:
            inspected = await inspection(session, row)
            items.append(snapshot(row, inspected.verdict if inspected else None))
        result = EvidencePage(
            items=tuple(items), next_after_id=items[-1].id if len(rows) > query.limit else None
        )
        session.add(observe_history(workspace, actor, request, query.version_id))
    return result
