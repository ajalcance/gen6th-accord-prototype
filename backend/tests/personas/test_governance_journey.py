"""Owner/CI SQL + ASGI journey. Synthetic identity and mounted routes exist only in this test."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Self
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.campaign_contracts import CampaignReceipt
from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaigns import offer_campaign
from accord.personas.contracts import PersonaVersion
from accord.personas.evidence_service import enqueue
from accord.personas.governance_http import create_governance_read_router
from accord.personas.read_http import create_read_router
from accord.personas.repository import ConflictError
from accord.personas.service import save
from personas.campaign_fixtures import campaign_material, decision_intent, offer_intent
from personas.conftest import command
from personas.private_evidence_fixtures import EphemeralTestWrapper, chunks, intent
from personas.test_session_boundary import verified
from personas.workflow_fixtures import human


@asynccontextmanager
async def client_for(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    provider = AsyncMock()
    provider.verify.return_value = verified(actor_ref="creator-a")
    app = FastAPI()
    app.include_router(create_read_router(provider))
    app.include_router(create_governance_read_router(provider))

    async def database() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def offer_for_journey(
    session: AsyncSession, workspace: UUID
) -> tuple[PersonaVersion, CampaignReceipt]:
    version, review, assets = await campaign_material(session, workspace)
    offer_command = offer_intent(version.version_id, review.id, assets)
    offer = await offer_campaign(session, workspace, human("creator-a"), offer_command)
    assert await offer_campaign(session, workspace, human("creator-a"), offer_command) == offer
    return version, offer


async def test_services_to_http_exact_retry_conflict_review_and_revocation(
    session: AsyncSession, workspace: UUID
) -> None:
    version, offer = await offer_for_journey(session, workspace)
    accepted = await decide_campaign(
        session, workspace, human("reviewer-b"), decision_intent(offer.id)
    )
    revoke = decision_intent(
        offer.id,
        decision="revoked",
        expected_previous_id=accepted.id,
        statement="Creator revokes this fictional permission.",
    )
    receipt = await decide_campaign(session, workspace, human("creator-a"), revoke)
    assert await decide_campaign(session, workspace, human("creator-a"), revoke) == receipt
    async with client_for(session) as client:
        base = f"/api/workspaces/{workspace}/personas"
        status = await client.post(
            base + "/campaigns/status/query", json={"campaign_id": str(offer.id)}
        )
        assert status.status_code == 200 and status.json()["blocking_reasons"] == ["revoked"]
        history = await client.post(
            base + "/campaigns/history/query", json={"campaign_id": str(offer.id)}
        )
        assert [row["decision"] for row in history.json()["items"]] == ["revoked", "accepted"]
        evidence = await client.post(
            base + "/workflow/evidence/query",
            json={"record_id": str(receipt.id), "kind": "campaign_decision"},
        )
        assert evidence.json()["anchor"]["version_id"] == str(offer.version_id)
        assert evidence.json()["audit_state"] == "pending"
        reviews = await client.post(
            base + "/reviews/history/query", json={"version_id": str(version.version_id)}
        )
        assert reviews.json()["items"][0]["id"] == str(offer.review_id)
    change = command("Fictional newer", persona_id=version.persona_id, expected_revision=1)
    updated = await save(session, workspace, "creator-a", change)
    assert await save(session, workspace, "creator-a", change) == updated
    with pytest.raises(ConflictError):
        await save(
            session,
            workspace,
            "creator-a",
            command("Stale draft", persona_id=updated.persona_id, expected_revision=1),
        )


async def test_service_expiry_serializes_without_private_material(
    session: AsyncSession, workspace: UUID
) -> None:
    version, offer = await offer_for_journey(session, workspace)
    queued = await enqueue(
        session,
        workspace,
        human("creator-a"),
        intent(version.version_id),
        chunks(),
        EphemeralTestWrapper(),
    )
    deadline = max(queued.expires_at, offer.scope.ends_at) + timedelta(seconds=1)

    class AfterExpiry(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> Self:
            return cls.fromtimestamp(deadline.timestamp(), tz or UTC)

    async with client_for(session) as client:
        base = f"/api/workspaces/{workspace}/personas"
        with (
            patch("accord.personas.campaign_status.datetime", AfterExpiry),
            patch("accord.personas.evidence_repository.datetime", AfterExpiry),
        ):
            status = await client.post(
                base + "/campaigns/status/query", json={"campaign_id": str(offer.id)}
            )
            evidence = await client.post(
                base + "/evidence/query", json={"version_id": str(offer.version_id)}
            )
    assert "expired" in status.json()["blocking_reasons"]
    assert not status.json()["eligible_for_use"]
    assert evidence.status_code == 200 and evidence.json()["items"][0]["id"] == str(queued.id)
    assert evidence.json()["items"][0]["state"] == "expired"
    assert (
        not {"ciphertext", "wrapped_key", "key_id", "nonce", "owner_ref"}
        & evidence.json()["items"][0].keys()
    )
