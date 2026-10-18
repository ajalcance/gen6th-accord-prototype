"""Party-scoped decision history with stable bounded pagination and observation."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_contracts import CampaignDecisionPage, CampaignHistoryQuery
from accord.personas.campaign_models import CampaignDecision
from accord.personas.campaign_repository import decision_receipt, offer_row
from accord.personas.repository import AccessDeniedError
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_events import decision_event
from accord.personas.workflow_repository import authorize_actor, locked_version


async def campaign_history(
    session: AsyncSession, workspace_id: UUID, actor: WorkflowActor, query: CampaignHistoryQuery
) -> CampaignDecisionPage:
    request_id = uuid4()
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace_id, actor, None)
        offer = await offer_row(session, workspace_id, query.campaign_id)
        if actor.actor_ref not in {offer.owner_ref, offer.recipient_ref}:
            raise AccessDeniedError("campaign access denied")
        await locked_version(session, workspace_id, offer.version_id)
        statement = select(CampaignDecision).where(
            CampaignDecision.workspace_id == workspace_id, CampaignDecision.campaign_id == offer.id
        )
        if query.before_ordinal is not None:
            statement = statement.where(CampaignDecision.ordinal < query.before_ordinal)
        rows = list(
            await session.scalars(
                statement.order_by(CampaignDecision.ordinal.desc()).limit(query.limit + 1)
            )
        )
        items = tuple(decision_receipt(row) for row in rows[: query.limit])
        result = CampaignDecisionPage(
            items=items,
            next_before_ordinal=(items[-1].ordinal if len(rows) > query.limit else None),
        )
        session.add(
            decision_event(
                workspace_id=workspace_id,
                actor_ref=actor.actor_ref,
                request_id=request_id,
                record_id=offer.id,
                version_id=offer.version_id,
                event_id=uuid4().hex,
                recorded_at=datetime.now(UTC),
                action="persona.workflow_observed",
            )
        )
    return result
