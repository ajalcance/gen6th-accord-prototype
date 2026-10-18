"""Stored grant checks and portrait disclosure faults; public IDs never grant general reads."""

import base64
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import publication_reads as reads
from accord.personas import publication_service as service
from accord.personas.issuance_models import PassportIssuance, PassportPublication
from accord.personas.passport_contracts import SignedPassport
from accord.personas.passport_signing import PassportRuntime, canonical
from accord.personas.publication_contracts import ApprovePublication, PublicProjection
from accord.personas.repository import AccessDeniedError, ConflictError
from personas.passport_fixtures import material, runtime, signed


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure", [None, "missing", "withdrawn", "runtime", "signature", "id", "fields", "issuance"]
)
async def test_stored_public_grant_binds_signature_fields_and_issuance(
    monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    payload, _ = material()
    active: PassportRuntime | None = runtime()
    assert active is not None
    public = PublicProjection(
        publication_id=uuid4(),
        approved_at=payload.issued_at,
        valid_from=payload.campaign.scope.starts_at,
        valid_until=payload.campaign.scope.ends_at,
        version_revision=1,
        values={"name": "Fictional", "ai_disclosure": "Synthetic"},
    )
    assert active.signer is not None
    package = SignedPassport(
        key_id=active.signer.key_id,
        payload=public.model_dump(mode="json"),
        signature=base64.b64encode(
            await active.signer.sign(canonical(public.model_dump(mode="json")))
        ).decode(),
    )
    row = PassportPublication(
        id=public.publication_id,
        workspace_id=payload.version.workspace_id,
        package=package.model_dump(mode="json"),
        issuance_id=uuid4(),
        fields=["name", "ai_disclosure"],
    )
    private: PassportIssuance | None = PassportIssuance(
        package=(await signed(payload, active)).model_dump(mode="json")
    )
    expected: type[Exception] = RuntimeError
    if failure == "id":
        row.id = uuid4()
    elif failure == "fields":
        row.fields = ["name", "biography"]
    elif failure == "signature":
        row.package = {**row.package, "key_id": "unknown"}
    elif failure == "runtime":
        active = None
    elif failure == "issuance":
        private = None
    elif failure in {"missing", "withdrawn"}:
        expected = AccessDeniedError
    async with AsyncSession() as session:
        monkeypatch.setattr(session, "execute", AsyncMock())
        scalar = AsyncMock(side_effect=[None if failure == "missing" else row, private])
        monkeypatch.setattr(session, "scalar", scalar)
        monkeypatch.setattr(
            session, "get", AsyncMock(return_value=object() if failure == "withdrawn" else None)
        )
        if failure:
            with pytest.raises(expected):
                await reads.approved_row(session, payload.version.workspace_id, row.id, active)
        else:
            result = await reads.approved_row(session, payload.version.workspace_id, row.id, active)
            assert result[2] == payload
            params = scalar.await_args_list[0].args[0].compile().params
            assert payload.version.workspace_id in params.values() and row.id in params.values()


@pytest.mark.asyncio
async def test_portrait_must_be_an_explicit_approved_field_before_decryption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, _ = material()
    public = PublicProjection(
        publication_id=uuid4(),
        approved_at=payload.issued_at,
        valid_from=payload.campaign.scope.starts_at,
        valid_until=payload.campaign.scope.ends_at,
        version_revision=1,
        values={"name": "Fictional", "ai_disclosure": "Synthetic"},
    )
    monkeypatch.setattr(reads, "approved_row", AsyncMock(return_value=(Mock(), public, payload)))
    decrypting = AsyncMock()
    monkeypatch.setattr(reads, "decrypted_thumbnail", decrypting)
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await reads.public_portrait(
                session, payload.version.workspace_id, public.publication_id, runtime(), None
            )
    decrypting.assert_not_called()
    command = ApprovePublication(
        request_id=uuid4(),
        campaign_id=payload.campaign.id,
        fields=("name", "ai_disclosure", "portrait_sha256"),
    )
    monkeypatch.setattr(service, "primary_portrait", AsyncMock(return_value=None))
    async with AsyncSession() as session:
        with pytest.raises(ConflictError):
            await service.projection(
                session, payload.version.workspace_id, command, payload, uuid4()
            )
