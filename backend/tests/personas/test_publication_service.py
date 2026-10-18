"""Public approval, replay and withdrawal orchestration; SQL/provider acceptance is separate."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import publication_service as service
from accord.personas.campaign_models import CampaignOffer
from accord.personas.issuance_models import PassportIssuance, PassportPublication
from accord.personas.models import Persona, Version
from accord.personas.passport_signing import PassportRuntime
from accord.personas.publication_contracts import ApprovePublication, PublicProjection
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import fingerprint
from personas.passport_fixtures import material, runtime, signed
from personas.test_passport_service import ACTOR


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [
        None,
        "owner",
        "blocked",
        "changed",
        "signer",
        "missing_issuance",
        "permission_removed",
        "late_permission_removed",
    ],
)
async def test_approval_signs_only_selected_fields_and_refuses_boundary_failures(
    monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    payload, status = material()
    active: PassportRuntime | None = runtime()
    assert active is not None
    packet = await signed(payload, active)
    offer = CampaignOffer(id=payload.campaign.id, owner_ref=ACTOR.actor_ref)
    version = Version(id=payload.version.version_id)
    command = ApprovePublication(
        request_id=uuid4(), campaign_id=offer.id, fields=("name", "ai_disclosure")
    )
    monkeypatch.setattr(
        service, "campaign_access", AsyncMock(return_value=(offer, version, Persona()))
    )
    exporting = AsyncMock(return_value=packet)
    monkeypatch.setattr(service, "export", exporting)
    blocked = status.model_copy(
        update={"eligible_for_use": False, "blocking_reasons": ("revoked",)}
    )
    permission = AsyncMock(return_value=status)
    monkeypatch.setattr(service, "current_status", permission)
    authorizing = AsyncMock()
    monkeypatch.setattr(service, "authorize_actor", authorizing)
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    expected: type[Exception] = RuntimeError
    issuance: PassportIssuance | None = PassportIssuance(id=uuid4())
    if failure == "owner":
        offer.owner_ref = "other"
        expected = AccessDeniedError
    elif failure == "blocked":
        permission.return_value = blocked
        expected = ConflictError
    elif failure == "changed":
        permission.side_effect = [status, blocked]
        expected = ConflictError
    elif failure == "signer":
        active = None
    elif failure == "missing_issuance":
        issuance = None
    elif failure == "permission_removed":
        authorizing.side_effect = AccessDeniedError("removed")
        expected = AccessDeniedError
    elif failure == "late_permission_removed":
        authorizing.side_effect = [None, None, AccessDeniedError("removed during signing")]
        expected = AccessDeniedError
    async with AsyncSession() as session:
        added = Mock()
        monkeypatch.setattr(session, "add", added)
        monkeypatch.setattr(session, "scalar", AsyncMock(side_effect=[None, issuance]))
        if failure:
            with pytest.raises(expected):
                await service.approve(session, payload.version.workspace_id, ACTOR, command, active)
            added.assert_not_called()
        else:
            result = await service.approve(
                session, payload.version.workspace_id, ACTOR, command, active
            )
            assert active is not None and active.trust.verify(result.package) == "valid"
            public = PublicProjection.model_validate(result.package.payload)
            assert set(public.values) == {"name", "ai_disclosure"}
            assert result.path == f"/p/{payload.version.workspace_id}/{public.publication_id}"
            serialized = result.package.model_dump_json()
            assert all(
                word not in serialized
                for word in (
                    "workspace_id",
                    "recipient_ref",
                    "creator_ref",
                    "evidence_id",
                    "biography",
                    "nonce",
                    "conditions",
                )
            )
            assert len(added.call_args_list) == 2
    if failure in {"owner", "permission_removed"}:
        exporting.assert_not_awaited()


@pytest.mark.asyncio
async def test_public_production_name_is_the_approved_film_title() -> None:
    payload, _ = material()
    command = ApprovePublication(
        request_id=uuid4(),
        campaign_id=payload.campaign.id,
        fields=("name", "ai_disclosure", "production_name"),
    )
    async with AsyncSession() as session:
        public = await service.projection(
            session, payload.version.workspace_id, command, payload, uuid4()
        )
    assert payload.campaign.scope.production is not None
    assert public.values["production_name"] == payload.campaign.scope.production.title


@pytest.mark.asyncio
async def test_public_approval_retry_never_signs_twice_and_changed_fields_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, status = material()
    active = runtime()
    packet = await signed(payload, active)
    command = ApprovePublication(
        request_id=uuid4(), campaign_id=payload.campaign.id, fields=("name", "ai_disclosure")
    )
    public = PublicProjection(
        publication_id=uuid4(),
        approved_at=payload.issued_at,
        valid_from=payload.campaign.scope.starts_at,
        valid_until=payload.campaign.scope.ends_at,
        version_revision=1,
        values={"name": "Fictional", "ai_disclosure": "Synthetic"},
    )
    import base64

    from accord.personas.passport_contracts import SignedPassport

    assert active.signer is not None
    from accord.personas.passport_signing import canonical

    public_packet = SignedPassport(
        key_id=active.signer.key_id,
        payload=public.model_dump(mode="json"),
        signature=base64.b64encode(
            await active.signer.sign(canonical(public.model_dump(mode="json")))
        ).decode(),
    )
    row = PassportPublication(
        id=public.publication_id,
        workspace_id=payload.version.workspace_id,
        package=public_packet.model_dump(mode="json"),
        fingerprint=fingerprint(command),
    )
    monkeypatch.setattr(
        service,
        "campaign_access",
        AsyncMock(return_value=(CampaignOffer(owner_ref=ACTOR.actor_ref), Version(), Persona())),
    )
    monkeypatch.setattr(service, "authorize_actor", AsyncMock())
    monkeypatch.setattr(service, "current_status", AsyncMock(return_value=status))
    monkeypatch.setattr(service, "export", AsyncMock(return_value=packet))
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    async with AsyncSession() as session:
        monkeypatch.setattr(session, "scalar", AsyncMock(return_value=row))
        monkeypatch.setattr(session, "get", AsyncMock(return_value=None))
        result = await service.approve(
            session, payload.version.workspace_id, ACTOR, command, active
        )
        assert result.package == public_packet
        with pytest.raises(ConflictError):
            await service.approve(
                session,
                payload.version.workspace_id,
                ACTOR,
                command.model_copy(update={"fields": ("name", "ai_disclosure", "biography")}),
                active,
            )


@pytest.mark.asyncio
async def test_withdrawal_is_owner_scoped_and_repeat_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, _ = material()
    packet = await signed(payload, runtime())
    row = PassportPublication(
        id=uuid4(),
        workspace_id=payload.version.workspace_id,
        issuance_id=uuid4(),
        package=packet.model_dump(mode="json"),
    )
    monkeypatch.setattr(service, "authorize_actor", AsyncMock())
    monkeypatch.setattr(service, "observation", Mock())
    async with AsyncSession() as session:
        added = Mock()
        monkeypatch.setattr(session, "add", added)
        monkeypatch.setattr(session, "scalar", AsyncMock(return_value=row))
        get = AsyncMock(
            side_effect=[
                PassportIssuance(package=packet.model_dump(mode="json")),
                None,
                PassportIssuance(package=packet.model_dump(mode="json")),
                object(),
            ]
        )
        monkeypatch.setattr(session, "get", get)
        await service.unpublish(session, row.workspace_id, ACTOR, row.id)
        await service.unpublish(session, row.workspace_id, ACTOR, row.id)
    assert len(added.call_args_list) == 2
