"""Anonymous projection reads never disclose private issuance or accept altered packages."""

import base64
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas import publication_reads as reads
from accord.personas.issuance_models import PassportPublication
from accord.personas.passport_contracts import SignedPassport
from accord.personas.passport_signing import canonical
from accord.personas.publication_contracts import PublicProjection
from accord.personas.publication_http import create_public_passport_router
from accord.personas.repository import AccessDeniedError
from personas.passport_fixtures import material, runtime
from personas.test_photo_http import unbound_db


@pytest.mark.asyncio
@pytest.mark.parametrize("change", [None, "tamper", "different", "revoked"])
async def test_public_verification_separates_integrity_from_current_permission(
    monkeypatch: pytest.MonkeyPatch, change: str | None
) -> None:
    payload, status = material()
    public = PublicProjection(
        publication_id=uuid4(),
        approved_at=payload.issued_at,
        valid_from=payload.campaign.scope.starts_at,
        valid_until=payload.campaign.scope.ends_at,
        version_revision=1,
        values={"name": "Fictional", "ai_disclosure": "Synthetic"},
    )
    active = runtime()
    assert active.signer is not None
    package = SignedPassport(
        key_id=active.signer.key_id,
        payload=public.model_dump(mode="json"),
        signature=base64.b64encode(
            await active.signer.sign(canonical(public.model_dump(mode="json")))
        ).decode(),
    )
    row = PassportPublication(id=public.publication_id, package=package.model_dump(mode="json"))
    monkeypatch.setattr(reads, "approved_row", AsyncMock(return_value=(row, public, payload)))
    monkeypatch.setattr(reads, "offer_row", AsyncMock())
    monkeypatch.setattr(reads, "locked_version", AsyncMock(return_value=(object(), object())))
    checking = AsyncMock(return_value=status)
    monkeypatch.setattr(reads, "current_status", checking)
    monkeypatch.setattr(reads, "observed", Mock())
    uploaded = None
    expected = "valid"
    if change == "tamper":
        uploaded = package.model_copy(
            update={
                "payload": {
                    **package.payload,
                    "values": {"name": "altered", "ai_disclosure": "Synthetic"},
                }
            }
        )
        expected = "invalid_signature"
    elif change == "different":
        altered: dict[str, object] = {**package.payload, "publication_id": str(uuid4())}
        uploaded = SignedPassport(
            key_id=active.signer.key_id,
            payload=altered,
            signature=base64.b64encode(await active.signer.sign(canonical(altered))).decode(),
        )
        expected = "binding_mismatch"
    elif change == "revoked":
        checking.return_value = status.model_copy(update={"eligible_for_use": False})
    async with AsyncSession() as session:
        result = await reads.inspect_public(
            session, payload.version.workspace_id, public.publication_id, active, uploaded
        )
    assert result.package == package and result.verification.integrity == expected
    assert result.verification.current_use == (
        "eligible" if change is None else "blocked" if change == "revoked" else "unavailable"
    )
    if change in {"tamper", "different"}:
        checking.assert_not_awaited()


@pytest.mark.asyncio
async def test_public_routes_require_activation_and_reject_duplicate_or_oversized_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for enabled in (False, True):
        app = FastAPI()
        app.include_router(create_public_passport_router(enabled=enabled))
        app.dependency_overrides[get_db] = unbound_db
        reading = AsyncMock(side_effect=AccessDeniedError("private internal detail"))
        monkeypatch.setattr("accord.personas.publication_http.inspect_public", reading)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
        ) as client:
            path = f"/api/public/passports/{uuid4()}/{uuid4()}"
            response = await client.get(path)
            assert response.status_code == (403 if enabled else 404)
            assert "private internal detail" not in response.text
            assert response.headers["cache-control"] == "no-store"
            for data in (b'{"key_id":"first","key_id":"second"}', b" " * 65537):
                response = await client.post(path + "/verify", content=data)
                assert response.status_code == (422 if enabled else 404)
