"""Owner/CI PostgreSQL writes through real ASGI routes; identity remains explicitly synthetic."""

import hashlib
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.campaign_contracts import OfferCampaignCommand
from accord.personas.campaign_models import PersonaAsset
from accord.personas.campaign_status import inspect_campaign
from accord.personas.models import WorkspaceMember
from accord.personas.photo_contracts import PhotoChange
from personas.campaign_fixtures import campaign_material, decision_intent, offer_intent
from personas.conftest import command
from personas.test_photo_storage import FixtureWrapper, staged
from personas.test_session_boundary import verified
from personas.workflow_fixtures import human, review_intent
from personas.write_http_fixtures import row_counts, write_client


async def prepare_campaign_journey(
    session: AsyncSession, workspace: UUID, version: UUID
) -> tuple[UUID, ...]:
    asset_id = uuid4()
    session.add(
        PersonaAsset(
            id=asset_id,
            workspace_id=workspace,
            version_id=version,
            digest=hashlib.sha256(b"Synthetic permitted fixture").hexdigest(),
            label="Synthetic fixture asset",
        )
    )
    await session.commit()
    return (asset_id,)


async def post_intent(
    client: AsyncClient,
    provider: AsyncMock,
    workspace: UUID,
    path: str,
    body: dict[str, object],
    actor: str = "creator-a",
) -> dict[str, object]:
    provider.verify.return_value = verified(actor_ref=actor)
    response = await client.post(f"/api/workspaces/{workspace}/personas{path}", json=body)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return dict(response.json())


async def test_creator_reviewer_recipient_journey_and_exact_receipts(
    session: AsyncSession, workspace: UUID
) -> None:
    session.add_all(
        [
            WorkspaceMember(workspace_id=workspace, actor_ref=name, role="reviewer")
            for name in ("reviewer-a", "reviewer-b")
        ]
    )
    await session.commit()
    async with write_client(session) as (client, provider):
        version, reviewed, assets = await create_and_review(client, provider, session, workspace)
        offer = offer_intent(
            UUID(str(version["version_id"])), UUID(str(reviewed["id"])), assets
        ).model_dump(mode="json")
        offered = await post_intent(client, provider, workspace, "/campaigns/offer", offer)
        assert await post_intent(client, provider, workspace, "/campaigns/offer", offer) == offered
        acceptance = decision_intent(UUID(str(offered["id"]))).model_dump(mode="json")
        accepted = await post_intent(
            client, provider, workspace, "/campaigns/decide", acceptance, "reviewer-b"
        )
        assert (
            await post_intent(
                client, provider, workspace, "/campaigns/decide", acceptance, "reviewer-b"
            )
            == accepted
        )
        revoke = decision_intent(
            UUID(str(offered["id"])),
            decision="revoked",
            expected_previous_id=UUID(str(accepted["id"])),
        ).model_dump(mode="json")
        revoked = await post_intent(client, provider, workspace, "/campaigns/decide", revoke)
        assert (
            await post_intent(client, provider, workspace, "/campaigns/decide", revoke) == revoked
        )
    assert await row_counts(session, workspace) == (1, 1, 1, 2)
    status = await inspect_campaign(
        session, workspace, human("creator-a"), UUID(str(offered["id"]))
    )
    assert status.blocking_reasons == ("revoked",) and not status.eligible_for_use
    await assert_journey_events(session, workspace)


async def assert_journey_events(session: AsyncSession, workspace: UUID) -> None:
    async with session.begin():
        events = list(
            await session.scalars(
                select(Event).where(
                    Event.tenant_id == workspace,
                    Event.action.in_(
                        (
                            "persona.version_saved",
                            "persona.review_recorded",
                            "persona.campaign_offered",
                            "persona.campaign_decided",
                        )
                    ),
                )
            )
        )
    assert len(events) == 5 and all(event.source == "server" for event in events)
    assert {event.actor_id for event in events} == {"creator-a", "reviewer-a", "reviewer-b"}


async def create_and_review(
    client: AsyncClient, provider: AsyncMock, session: AsyncSession, workspace: UUID
) -> tuple[dict[str, object], dict[str, object], tuple[UUID, ...]]:
    _, portrait = await staged(session, workspace, FixtureWrapper())
    save = command(photo=PhotoChange(action="attach", upload_id=portrait)).model_dump(mode="json")
    version = await post_intent(client, provider, workspace, "/versions/save", save)
    assert await post_intent(client, provider, workspace, "/versions/save", save) == version
    assets = await prepare_campaign_journey(session, workspace, UUID(str(version["version_id"])))
    review = review_intent(UUID(str(version["version_id"]))).model_dump(mode="json")
    reviewed = await post_intent(
        client, provider, workspace, "/reviews/record", review, "reviewer-a"
    )
    assert (
        await post_intent(client, provider, workspace, "/reviews/record", review, "reviewer-a")
        == reviewed
    )
    return version, reviewed, assets


async def material_intent(
    session: AsyncSession, workspace: UUID, operation: str
) -> tuple[str, dict[str, object]]:
    version, review, assets = await campaign_material(session, workspace)
    if operation == "save":
        return "/versions/save", command(
            persona_id=version.persona_id, expected_revision=1
        ).model_dump(mode="json")
    if operation == "review":
        return "/reviews/record", review_intent(
            version.version_id, expected_previous_id=review.id
        ).model_dump(mode="json")
    offer = offer_intent(version.version_id, review.id, assets)
    if operation == "offer":
        return "/campaigns/offer", offer.model_dump(mode="json")
    from accord.personas.campaigns import offer_campaign

    offered = await offer_campaign(
        session, workspace, human("creator-a"), OfferCampaignCommand.model_validate(offer)
    )
    return "/campaigns/decide", decision_intent(offered.id).model_dump(mode="json")


@pytest.mark.parametrize(
    "operation,actor",
    [
        ("save", "creator-a"),
        ("review", "reviewer-a"),
        ("offer", "creator-a"),
        ("decide", "reviewer-b"),
    ],
)
async def test_each_write_reauthorizes_retry_after_write_role_loss(
    session: AsyncSession, workspace: UUID, operation: str, actor: str
) -> None:
    path, body = await material_intent(session, workspace, operation)
    async with write_client(session) as (client, provider):
        await post_intent(client, provider, workspace, path, body, actor)
        counts = await row_counts(session, workspace)
        async with session.begin():
            # Preserve immutable records' member references while removing write permission.
            await session.execute(
                update(WorkspaceMember)
                .where(
                    WorkspaceMember.workspace_id == workspace, WorkspaceMember.actor_ref == actor
                )
                .values(role="viewer")
            )
            assert (
                await session.scalar(
                    select(WorkspaceMember.role).where(
                        WorkspaceMember.workspace_id == workspace,
                        WorkspaceMember.actor_ref == actor,
                    )
                )
                == "viewer"
            )
        response = await client.post(f"/api/workspaces/{workspace}/personas{path}", json=body)
    assert response.status_code == 403 and await row_counts(session, workspace) == counts


@pytest.mark.parametrize(
    "operation,actor",
    [
        ("save", "creator-a"),
        ("review", "reviewer-a"),
        ("offer", "creator-a"),
        ("decide", "reviewer-b"),
    ],
)
async def test_foreign_workspace_and_changed_replay_never_create_records(
    session: AsyncSession, workspace: UUID, operation: str, actor: str
) -> None:
    path, body = await material_intent(session, workspace, operation)
    async with write_client(session) as (client, provider):
        await post_intent(client, provider, workspace, path, body, actor)
        counts = await row_counts(session, workspace)
        foreign = await client.post(f"/api/workspaces/{uuid4()}/personas{path}", json=body)
        assert foreign.status_code == 403
        changed = different_intent(body, operation)
        conflict = await client.post(f"/api/workspaces/{workspace}/personas{path}", json=changed)
        assert conflict.status_code == 409
        assert await row_counts(session, workspace) == counts


async def test_self_review_stale_version_and_wrong_recipient_are_denied(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, assets = await campaign_material(session, workspace)
    async with write_client(session) as (client, provider):
        await assert_independence(client, session, workspace, version.version_id, review.id)
        offer = await post_intent(
            client,
            provider,
            workspace,
            "/campaigns/offer",
            offer_intent(version.version_id, review.id, assets).model_dump(mode="json"),
        )
        wrong = await client.post(
            f"/api/workspaces/{workspace}/personas/campaigns/decide",
            json=decision_intent(UUID(str(offer["id"]))).model_dump(mode="json"),
        )
        assert wrong.status_code == 403
        await post_intent(
            client,
            provider,
            workspace,
            "/versions/save",
            command(persona_id=version.persona_id, expected_revision=1).model_dump(mode="json"),
        )
        provider.verify.return_value = verified(actor_ref="reviewer-b")
        stale = await client.post(
            f"/api/workspaces/{workspace}/personas/campaigns/decide",
            json=decision_intent(UUID(str(offer["id"]))).model_dump(mode="json"),
        )
        assert stale.status_code == 409
    assert await row_counts(session, workspace) == (2, 1, 1, 0)


async def assert_independence(
    client: AsyncClient, session: AsyncSession, workspace: UUID, version: UUID, review: UUID
) -> None:
    await creator_role(session, workspace, "reviewer")
    own = await client.post(
        f"/api/workspaces/{workspace}/personas/reviews/record",
        json=review_intent(version, expected_previous_id=review).model_dump(mode="json"),
    )
    assert own.status_code == 403
    await creator_role(session, workspace, "creator")


async def creator_role(session: AsyncSession, workspace: UUID, role: str) -> None:
    async with session.begin():
        await session.execute(
            update(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace, WorkspaceMember.actor_ref == "creator-a"
            )
            .values(role=role)
        )


def different_intent(body: dict[str, object], operation: str) -> dict[str, object]:
    if "statement" in body:
        return {**body, "statement": "Different statement"}
    if operation == "save":
        return {**body, "expected_revision": 9}
    scope = OfferCampaignCommand.model_validate(body).scope.model_dump(mode="json")
    return {**body, "scope": {**scope, "name": "Changed scope"}}
