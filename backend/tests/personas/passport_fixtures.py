"""Synthetic metadata and ephemeral signing keys only; no live identity or keys."""

import base64
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from accord.personas.campaign_contracts import (
    CampaignDecisionReceipt,
    CampaignReceipt,
    CampaignStatus,
)
from accord.personas.capture_contracts import CaptureMetadata
from accord.personas.contracts import PersonaDraft, PersonaVersion
from accord.personas.passport_contracts import PassportPayload, SignedPassport
from accord.personas.passport_signing import PassportRuntime, PassportTrust, canonical
from accord.personas.production_contracts import ProductionUse
from personas.campaign_fixtures import campaign_scope


class SyntheticSigner:
    key_id = "synthetic-ephemeral-key"

    def __init__(self) -> None:
        self.key = Ed25519PrivateKey.generate()

    async def sign(self, data: bytes) -> bytes:
        return self.key.sign(data)


def production() -> ProductionUse:
    return ProductionUse(
        title="Fictional film",
        episode="Episode 1",
        role_name="Captain North",
        adaptation="Costume change only; no sequel or advertising use.",
        supporting_references=(),
    )


def material() -> tuple[PassportPayload, CampaignStatus]:
    now, workspace, version_id, asset = datetime.now(UTC), uuid4(), uuid4(), uuid4()
    version = performer(workspace, version_id, now)
    offer = CampaignReceipt(
        id=uuid4(),
        workspace_id=workspace,
        version_id=version_id,
        review_id=uuid4(),
        owner_ref=version.creator_ref,
        scope=campaign_scope(
            (asset,), recipient_ref="synthetic-recipient", production=production()
        ),
        assets=({"id": asset, "digest": "a" * 64, "label": "Synthetic scene"},),
        recorded_at=now - timedelta(hours=1),
        event_id=uuid4().hex,
    )
    decision = CampaignDecisionReceipt(
        id=uuid4(),
        workspace_id=workspace,
        campaign_id=offer.id,
        ordinal=1,
        actor_ref=offer.scope.recipient_ref,
        decision="accepted",
        statement="Synthetic acceptance.",
        recorded_at=now - timedelta(minutes=10),
        event_id=uuid4().hex,
    )
    payload = PassportPayload(
        issued_at=now,
        version=version,
        campaign=offer,
        acceptance_id=decision.id,
        references=(reference_capture(),),
    )
    return payload, CampaignStatus(
        receipt=offer,
        latest_decision=decision,
        evaluated_at=now,
        blocking_reasons=(),
        eligible_for_use=True,
    )


def performer(workspace: UUID, version: UUID, now: datetime) -> PersonaVersion:
    return PersonaVersion(
        persona_id=uuid4(),
        workspace_id=workspace,
        version_id=version,
        revision=1,
        creator_ref="synthetic-owner",
        recorded_at=now - timedelta(hours=2),
        content=PersonaDraft(
            name="Fictional performer",
            biography="Fictional continuing actor.",
            human_contribution="Original fictional styling.",
            ai_disclosure="Synthetic fixture.",
        ),
    )


def reference_capture() -> CaptureMetadata:
    return CaptureMetadata(
        portrait_id=uuid4(),
        source_sha256="b" * 64,
        source_width=100,
        source_height=100,
        orientation=1,
        width=100,
        height=100,
        sha256="c" * 64,
        recipe="rgba-png-1024-v1",
        decoder_version="synthetic-v1",
        recorded_at=datetime.now(UTC) - timedelta(minutes=30),
    )


def runtime() -> PassportRuntime:
    signer = SyntheticSigner()
    return PassportRuntime(PassportTrust({signer.key_id: signer.key.public_key()}), signer)


async def signed(payload: PassportPayload, active: PassportRuntime) -> SignedPassport:
    assert active.signer is not None
    data = payload.model_dump(mode="json")
    return SignedPassport(
        key_id=active.signer.key_id,
        payload=data,
        signature=base64.b64encode(await active.signer.sign(canonical(data))).decode(),
    )
