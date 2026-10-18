"""Actual ephemeral Ed25519 signatures, canonical data and separate current permission."""

import copy
import hashlib
import json
from uuid import uuid4

import pytest
from pydantic import ValidationError

from accord.personas.campaign_contracts import CampaignScope
from accord.personas.passport_contracts import PassportPayload, PassportVerification, SignedPassport
from accord.personas.passport_signing import DOMAIN, PassportTrust, canonical
from accord.personas.production_contracts import ProductionUse
from accord.personas.service import fingerprint
from personas.campaign_fixtures import offer_intent
from personas.passport_fixtures import material, production, runtime, signed


@pytest.mark.asyncio
async def test_canonical_property_order_and_domain_do_not_change_signature() -> None:
    payload, _ = material()
    active = runtime()
    packet = await signed(payload, active)
    assert active.trust.verify(packet) == "valid"
    reversed_payload = dict(reversed(tuple(packet.payload.items())))
    assert active.trust.verify(packet.model_copy(update={"payload": reversed_payload})) == "valid"
    assert canonical(dict(packet.payload)).startswith(DOMAIN)
    assert active.signer is not None
    assert await active.signer.sign(
        json.dumps(packet.payload).encode()
    ) != await active.signer.sign(canonical(dict(packet.payload)))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field", ["version", "campaign", "references", "acceptance_id", "issued_at", "claims"]
)
async def test_any_altered_signed_field_fails_integrity(field: str) -> None:
    payload, _ = material()
    active = runtime()
    packet = await signed(payload, active)
    changed = copy.deepcopy(packet.payload)
    changed[field] = "altered synthetic content"
    assert (
        active.trust.verify(packet.model_copy(update={"payload": changed})) == "invalid_signature"
    )


@pytest.mark.asyncio
async def test_unknown_and_replaced_keys_and_signature_fail_closed() -> None:
    payload, _ = material()
    active = runtime()
    packet = await signed(payload, active)
    assert PassportTrust({}).verify(packet) == "untrusted_key"
    assert runtime().trust.verify(packet) == "invalid_signature"
    bad = packet.model_copy(update={"signature": "A" * 86 + "=="})
    assert active.trust.verify(bad) == "invalid_signature"
    assert (
        active.trust.verify(packet.model_copy(update={"payload": {"n": float("nan")}}))
        == "invalid_package"
    )


def test_legacy_scope_preserves_stored_fingerprint_and_production_changes_retry() -> None:
    command = offer_intent(uuid4(), uuid4(), (uuid4(),))
    legacy = command.model_dump(mode="json")
    assert "production" not in legacy["scope"]
    assert (
        fingerprint(command)
        == hashlib.sha256(
            json.dumps(legacy, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    changed = type(command).model_validate(
        {**legacy, "scope": {**legacy["scope"], "production": production().model_dump(mode="json")}}
    )
    assert fingerprint(changed) != fingerprint(command)
    assert CampaignScope.model_validate(changed.scope.model_dump()).production == production()


@pytest.mark.parametrize(
    "changes",
    [
        {"title": " "},
        {"episode": "x" * 81},
        {"role_name": ""},
        {"adaptation": " "},
        {"identity_verified": True},
        {"rights_verified": True},
        {"supporting_references": [{"kind": "approval", "evidence_id": str(uuid4())}]},
        {
            "supporting_references": [
                {"kind": "claim", "evidence_id": str(uuid4()), "approved": True}
            ]
        },
    ],
)
def test_production_rejects_unbounded_or_authoritative_claims(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ProductionUse.model_validate({**production().model_dump(), **changes})


def test_reference_limit_uniqueness_and_exact_payload_binding() -> None:
    reference = {"kind": "consent", "evidence_id": uuid4()}
    for references in (
        [reference, reference],
        [dict(reference, evidence_id=uuid4()) for _ in range(9)],
    ):
        with pytest.raises(ValidationError):
            ProductionUse.model_validate(
                {**production().model_dump(), "supporting_references": references}
            )
    payload, status = material()
    with pytest.raises(ValidationError):
        PassportPayload.model_validate({**payload.model_dump(), "version": material()[0].version})
    with pytest.raises(ValidationError):
        SignedPassport.model_validate(
            {"algorithm": "none", "key_id": "test", "signature": "A" * 86 + "==", "payload": {}}
        )
    with pytest.raises(ValidationError):
        PassportVerification(
            workspace_id=status.receipt.workspace_id,
            campaign_id=status.receipt.id,
            integrity="invalid_signature",
            current_status=status,
        )
