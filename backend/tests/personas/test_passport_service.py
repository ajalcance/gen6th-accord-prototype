"""Disconnected orchestration proofs; actual SQL and Google acceptance remain separate."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import passport_service as service
from accord.personas.campaign_models import CampaignOffer
from accord.personas.models import Persona, Version
from accord.personas.passport_contracts import PassportPayload, SignedPassport, VerifyPassport
from accord.personas.passport_signing import PassportRuntime, PassportTrust, canonical
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.workflow_contracts import WorkflowActor
from personas.passport_fixtures import material, runtime, signed

ACTOR = WorkflowActor(actor_ref="synthetic-owner", kind="human")


def setup(monkeypatch: pytest.MonkeyPatch) -> tuple[PassportPayload, dict[str, Mock]]:
    payload, status = material()
    mocks = {
        name: AsyncMock()
        for name in (
            "campaign_access",
            "authorize_actor",
            "current_status",
            "reference_captures",
            "accepted_binding",
            "stored_issuance",
        )
    }
    for name, mock in mocks.items():
        monkeypatch.setattr(service, name, mock)
    v = payload.version
    version = Version(
        id=v.version_id,
        workspace_id=v.workspace_id,
        persona_id=v.persona_id,
        revision=v.revision,
        creator_ref=v.creator_ref,
        recorded_at=v.recorded_at,
        **v.content.model_dump(),
    )
    offer = CampaignOffer(
        id=payload.campaign.id, version_id=v.version_id, recorded_at=payload.campaign.recorded_at
    )
    mocks["campaign_access"].return_value = (offer, version, Persona(head_revision=1))
    mocks["current_status"].return_value = status
    mocks["reference_captures"].return_value = payload.references
    mocks["accepted_binding"].return_value = True
    mocks["stored_issuance"].return_value = None
    mocks["remember_issuance"] = Mock()
    monkeypatch.setattr(service, "remember_issuance", mocks["remember_issuance"])
    mocks["observation"] = Mock()
    monkeypatch.setattr(service, "observation", mocks["observation"])
    monkeypatch.setattr(service, "workspace_observation", Mock())
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    return payload, mocks


@pytest.mark.asyncio
async def test_export_rechecks_permission_after_actual_signature_and_excludes_private_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, mocks = setup(monkeypatch)
    active = runtime()
    async with AsyncSession() as session:
        packet = await service.export(
            session, payload.version.workspace_id, ACTOR, payload.campaign.id, active
        )
    assert active.trust.verify(packet) == "valid"
    assert mocks["current_status"].await_count == 2
    mocks["authorize_actor"].assert_awaited_once()
    data = packet.model_dump_json()
    assert all(
        word not in data
        for word in ("ciphertext", "nonce", "wrapped_key", "vectors", '"statement"')
    )
    assert packet.payload["claims"] == payload.claims
    mocks["observation"].assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [
        "denied",
        "unavailable",
        "untrusted",
        "scope",
        "references",
        "expired",
        "signer",
        "permission_removed",
        "changed",
    ],
)
async def test_export_failures_never_return_a_package(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    payload, mocks = setup(monkeypatch)
    active: PassportRuntime | None = runtime()
    expected: type[Exception] = RuntimeError
    status = mocks["current_status"].return_value
    if failure == "denied":
        mocks["campaign_access"].side_effect = AccessDeniedError("denied")
        expected = AccessDeniedError
    elif failure == "unavailable":
        active = None
    elif failure == "untrusted" and active is not None:
        active = PassportRuntime(PassportTrust({}), active.signer)
    elif failure == "scope":
        scope = status.receipt.scope.model_copy(update={"production": None})
        mocks["current_status"].return_value = status.model_copy(
            update={"receipt": status.receipt.model_copy(update={"scope": scope})}
        )
        expected = ConflictError
    elif failure == "references":
        mocks["reference_captures"].return_value = ()
        expected = ConflictError
    elif failure in {"expired", "changed"}:
        blocked = status.model_copy(
            update={"eligible_for_use": False, "blocking_reasons": ("expired",)}
        )
        mocks["current_status"].side_effect = (
            [blocked] if failure == "expired" else [status, blocked]
        )
        expected = ConflictError
    elif failure == "signer" and active is not None and active.signer is not None:
        active = PassportRuntime(
            active.trust,
            Mock(
                key_id=active.signer.key_id,
                sign=AsyncMock(side_effect=RuntimeError("private provider data")),
            ),
        )
    else:
        mocks["authorize_actor"].side_effect = AccessDeniedError("removed during signing")
        expected = AccessDeniedError
    async with AsyncSession() as session:
        with pytest.raises(expected):
            await service.export(
                session, payload.version.workspace_id, ACTOR, payload.campaign.id, active
            )
    mocks["observation"].assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reason", ["expired", "revoked", "supporting_evidence_unavailable", "stale_version"]
)
async def test_valid_historical_package_keeps_integrity_but_blocks_current_use(
    monkeypatch: pytest.MonkeyPatch, reason: str
) -> None:
    payload, mocks = setup(monkeypatch)
    active = runtime()
    packet = await signed(payload, active)
    status = mocks["current_status"].return_value
    mocks["current_status"].return_value = status.model_copy(
        update={"eligible_for_use": False, "blocking_reasons": (reason,)}
    )
    async with AsyncSession() as session:
        result = await service.verify(
            session,
            payload.version.workspace_id,
            ACTOR,
            VerifyPassport(campaign_id=payload.campaign.id, package=packet),
            active,
        )
    assert result.integrity == "valid" and result.current_status is not None
    assert (
        not result.current_status.eligible_for_use
        and reason in result.current_status.blocking_reasons
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["version", "acceptance", "reference", "future", "campaign"])
async def test_trusted_signature_cannot_bypass_saved_bindings(
    monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    payload, mocks = setup(monkeypatch)
    if change == "version":
        payload = payload.model_copy(
            update={"version": payload.version.model_copy(update={"persona_id": uuid4()})}
        )
    elif change == "acceptance":
        mocks["accepted_binding"].return_value = False
    elif change == "reference":
        payload = payload.model_copy(
            update={"references": (payload.references[0].model_copy(update={"sha256": "d" * 64}),)}
        )
    elif change == "future":
        payload = payload.model_copy(update={"issued_at": datetime.now(UTC) + timedelta(hours=1)})
    else:
        payload = payload.model_copy(
            update={"campaign": payload.campaign.model_copy(update={"id": uuid4()})}
        )
    active = runtime()
    async with AsyncSession() as session:
        result = await service.verify(
            session,
            payload.version.workspace_id,
            ACTOR,
            VerifyPassport(campaign_id=uuid4(), package=await signed(payload, active)),
            active,
        )
    assert result.integrity == "binding_mismatch" and result.current_status is None


@pytest.mark.asyncio
async def test_altered_package_never_reads_permission_and_authorization_precedes_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, mocks = setup(monkeypatch)
    active = runtime()
    packet = await signed(payload, active)
    packet = packet.model_copy(update={"payload": {**packet.payload, "claims": "altered"}})
    command = VerifyPassport(campaign_id=payload.campaign.id, package=packet)
    async with AsyncSession() as session:
        result = await service.verify(session, payload.version.workspace_id, ACTOR, command, active)
    assert result.integrity == "invalid_signature" and result.current_status is None
    mocks["current_status"].assert_not_called()
    mocks["campaign_access"].side_effect = AccessDeniedError("denied")
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await service.verify(session, payload.version.workspace_id, ACTOR, command, active)


@pytest.mark.asyncio
async def test_missing_runtime_and_readiness_do_not_activate_or_sign(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, _ = setup(monkeypatch)
    async with AsyncSession() as session:
        ready = await service.readiness(session, payload.version.workspace_id, ACTOR, None)
    assert not ready.export_available and not ready.verification_available


@pytest.mark.asyncio
async def test_trusted_but_invalid_schema_and_missing_verifier_are_not_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import base64

    payload, mocks = setup(monkeypatch)
    active = runtime()
    assert active.signer is not None
    raw = {**payload.model_dump(mode="json"), "rights_verified": True}
    packet = SignedPassport(
        key_id=active.signer.key_id,
        payload=raw,
        signature=base64.b64encode(await active.signer.sign(canonical(raw))).decode(),
    )
    command = VerifyPassport(campaign_id=payload.campaign.id, package=packet)
    async with AsyncSession() as session:
        result = await service.verify(session, payload.version.workspace_id, ACTOR, command, active)
    assert result.integrity == "invalid_package" and result.current_status is None
    mocks["current_status"].assert_not_called()
    async with AsyncSession() as session:
        with pytest.raises(RuntimeError):
            await service.verify(session, payload.version.workspace_id, ACTOR, command, None)
    async with AsyncSession() as session:
        ready = await service.readiness(session, payload.version.workspace_id, ACTOR, active)
    assert ready.export_available and ready.verification_available
