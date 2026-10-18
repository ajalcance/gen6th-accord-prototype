"""Owner/CI PostgreSQL lane; collection is not execution or live provider acceptance."""

from datetime import datetime, tzinfo
from typing import Self
from uuid import UUID, uuid4

import pytest
from sqlalchemy import update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_contracts import CampaignReceipt, OfferCampaignCommand
from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaign_models import CampaignOffer, PersonaAsset
from accord.personas.campaign_status import inspect_campaign
from accord.personas.campaigns import offer_campaign
from accord.personas.evidence_service import enqueue, inspect_evidence
from accord.personas.models import WorkspaceMember
from accord.personas.passport_contracts import VerifyPassport
from accord.personas.passport_repository import assets
from accord.personas.passport_service import export, verify
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.reviews import record_review
from accord.personas.service import save
from personas.campaign_fixtures import campaign_scope, decision_intent, offer_intent
from personas.conftest import command
from personas.passport_fixtures import material, production, runtime, signed
from personas.private_evidence_fixtures import (
    EphemeralTestWrapper,
    FixtureContentInspector,
    chunks,
    intent,
)
from personas.test_photo_storage import FixtureWrapper, staged
from personas.workflow_fixtures import human, review_intent


async def production_offer(
    session: AsyncSession, workspace: UUID
) -> tuple[OfferCampaignCommand, CampaignReceipt]:
    session.add_all(
        [
            WorkspaceMember(workspace_id=workspace, actor_ref=ref, role="reviewer")
            for ref in ("reviewer-a", "reviewer-b")
        ]
    )
    await session.commit()
    _, portrait = await staged(session, workspace, FixtureWrapper())
    version = await save(
        session, workspace, "creator-a", command(photo={"action": "attach", "upload_id": portrait})
    )
    review = await record_review(
        session, workspace, human("reviewer-a"), review_intent(version.version_id)
    )
    asset = uuid4()
    session.add(
        PersonaAsset(
            id=asset,
            workspace_id=workspace,
            version_id=version.version_id,
            label="Synthetic scene",
            digest="a" * 64,
        )
    )
    await session.commit()
    use = offer_intent(
        version.version_id,
        review.id,
        (asset,),
        scope=campaign_scope((asset,), production=production()),
    )
    return use, await offer_campaign(session, workspace, human("creator-a"), use)


async def test_production_replay_signature_tamper_and_revocation(
    session: AsyncSession, workspace: UUID
) -> None:
    use, offer = await production_offer(session, workspace)
    assert await offer_campaign(session, workspace, human("creator-a"), use) == offer
    assert (
        await assets(session, workspace, human("creator-a"), offer.version_id)
    ).assets == offer.assets
    acceptance = await decide_campaign(
        session, workspace, human("reviewer-b"), decision_intent(offer.id)
    )
    active = runtime()
    packet = await export(session, workspace, human("creator-a"), offer.id, active)
    verification = VerifyPassport(campaign_id=offer.id, package=packet)
    result = await verify(session, workspace, human("reviewer-b"), verification, active)
    assert (
        result.integrity == "valid"
        and result.current_status
        and result.current_status.eligible_for_use
    )
    altered = packet.model_copy(update={"payload": {**packet.payload, "claims": "altered"}})
    rejected = await verify(
        session,
        workspace,
        human("reviewer-b"),
        VerifyPassport(campaign_id=offer.id, package=altered),
        active,
    )
    assert rejected.integrity == "invalid_signature" and rejected.current_status is None
    await decide_campaign(
        session,
        workspace,
        human("creator-a"),
        decision_intent(offer.id, expected_previous_id=acceptance.id, decision="revoked"),
    )
    revoked = await verify(session, workspace, human("reviewer-b"), verification, active)
    assert (
        revoked.integrity == "valid"
        and revoked.current_status
        and "revoked" in revoked.current_status.blocking_reasons
    )
    with pytest.raises(ConflictError):
        await export(session, workspace, human("creator-a"), offer.id, active)


@pytest.mark.parametrize("actor", ["viewer", "creator-b", "reviewer-a"])
async def test_export_and_verification_are_private_to_current_parties(
    session: AsyncSession, workspace: UUID, actor: str
) -> None:
    _, offer = await production_offer(session, workspace)
    with pytest.raises(AccessDeniedError):
        await export(session, workspace, human(actor), offer.id, runtime())
    with pytest.raises(AccessDeniedError):
        await assets(session, workspace, human(actor), offer.version_id)
    active = runtime()
    verification = VerifyPassport(campaign_id=offer.id, package=await signed(material()[0], active))
    with pytest.raises(AccessDeniedError):
        await verify(session, workspace, human(actor), verification, active)


async def test_supporting_evidence_quarantine_and_expiry_block_use(
    session: AsyncSession, workspace: UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    use, offer = await production_offer(session, workspace)
    actor, wrapper = human("creator-a"), EphemeralTestWrapper()
    evidence = await enqueue(session, workspace, actor, intent(offer.version_id), chunks(), wrapper)
    p = type(production()).model_validate(
        {
            **production().model_dump(),
            "supporting_references": [{"kind": "consent", "evidence_id": evidence.id}],
        }
    )
    scoped = use.model_copy(
        update={"request_id": uuid4(), "scope": use.scope.model_copy(update={"production": p})}
    )
    with pytest.raises(AccessDeniedError):
        await offer_campaign(session, workspace, actor, scoped)
    await inspect_evidence(
        session, workspace, actor, evidence.id, wrapper, FixtureContentInspector()
    )
    clean = await offer_campaign(session, workspace, actor, scoped)
    await decide_campaign(session, workspace, human("reviewer-b"), decision_intent(clean.id))
    assert (await inspect_campaign(session, workspace, actor, clean.id)).eligible_for_use
    monkeypatch.setattr("accord.personas.production_evidence.datetime", EvidenceFuture)
    expired = await inspect_campaign(session, workspace, actor, clean.id)
    assert expired.blocking_reasons == ("supporting_evidence_unavailable",)


class EvidenceFuture(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> Self:
        return cls.fromtimestamp(datetime.now(tz).timestamp() + 8 * 86400, tz)


async def test_production_scope_remains_database_immutable(
    session: AsyncSession, workspace: UUID
) -> None:
    _, offer = await production_offer(session, workspace)
    with pytest.raises(DBAPIError, match="immutable"):
        async with session.begin():
            await session.execute(
                update(CampaignOffer).where(CampaignOffer.id == offer.id).values(production=None)
            )


async def test_foreign_version_evidence_and_changed_production_retry_are_rejected(
    session: AsyncSession,
    workspace: UUID,
) -> None:
    use, offer = await production_offer(session, workspace)
    p = production().model_copy(update={"episode": "Episode 2"})
    changed = use.model_copy(update={"scope": use.scope.model_copy(update={"production": p})})
    with pytest.raises(ConflictError):
        await offer_campaign(session, workspace, human("creator-a"), changed)
    other = await save(session, workspace, "creator-a", command())
    wrapper, actor = EphemeralTestWrapper(), human("creator-a")
    evidence = await enqueue(session, workspace, actor, intent(other.version_id), chunks(), wrapper)
    await inspect_evidence(
        session, workspace, actor, evidence.id, wrapper, FixtureContentInspector()
    )
    p = type(p).model_validate(
        {**p.model_dump(), "supporting_references": [{"kind": "claim", "evidence_id": evidence.id}]}
    )
    scoped = use.model_copy(
        update={"request_id": uuid4(), "scope": use.scope.model_copy(update={"production": p})}
    )
    with pytest.raises(AccessDeniedError):
        await offer_campaign(session, workspace, actor, scoped)
    assert (
        await inspect_campaign(session, workspace, actor, offer.id)
    ).receipt.scope.production == production()
