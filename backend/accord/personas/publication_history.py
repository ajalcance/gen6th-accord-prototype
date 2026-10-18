"""Owner discovery permits withdrawal after refresh without disclosing private issuance content."""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.issuance_models import (
    PassportIssuance,
    PassportPublication,
    PassportUnpublication,
)
from accord.personas.passport_repository import campaign_access, observation
from accord.personas.publication_contracts import (
    PublicationHistoryItem,
    PublicationHistoryPage,
    PublicationHistoryQuery,
)
from accord.personas.publication_service import receipt
from accord.personas.repository import AccessDeniedError
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor


async def history(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, query: PublicationHistoryQuery
) -> PublicationHistoryPage:
    async with tracked_transaction(session, workspace, actor.actor_ref, uuid4()):
        await authorize_actor(session, workspace, actor, "creator")
        offer, version, _ = await campaign_access(session, workspace, actor, query.campaign_id)
        if actor.actor_ref != offer.owner_ref:
            raise AccessDeniedError("publication history requires the owner")
        statement = (
            select(PassportPublication, PassportUnpublication.publication_id)
            .join(
                PassportIssuance,
                (PassportIssuance.id == PassportPublication.issuance_id)
                & (PassportIssuance.workspace_id == PassportPublication.workspace_id),
            )
            .outerjoin(
                PassportUnpublication,
                (PassportUnpublication.publication_id == PassportPublication.id)
                & (PassportUnpublication.workspace_id == PassportPublication.workspace_id),
            )
            .where(
                PassportPublication.workspace_id == workspace,
                PassportPublication.owner_ref == actor.actor_ref,
                PassportIssuance.campaign_id == query.campaign_id,
            )
        )
        if query.after_id:
            statement = statement.where(PassportPublication.id > query.after_id)
        rows = (await session.execute(statement.order_by(PassportPublication.id).limit(21))).all()
        items = tuple(
            PublicationHistoryItem(receipt=receipt(row), withdrawn=withdrawal is not None)
            for row, withdrawal in rows[:20]
        )
        observation(session, workspace, actor, offer.id, version.id)
        result = PublicationHistoryPage(
            workspace_id=workspace,
            campaign_id=offer.id,
            items=items,
            next_after_id=items[-1].receipt.publication_id if len(rows) > 20 else None,
        )
    return result
