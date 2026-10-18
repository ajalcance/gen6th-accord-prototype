"""Persisted issuance replays cannot sign twice or bypass fresh authorization/bindings."""

from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import issuance_repository as repository
from accord.personas import passport_service as service
from accord.personas.passport_signing import PassportRuntime
from accord.personas.repository import AccessDeniedError, ConflictError
from personas.passport_fixtures import runtime, signed
from personas.test_passport_service import ACTOR, setup


@pytest.mark.asyncio
async def test_committed_export_replays_identical_package_without_signer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, mocks = setup(monkeypatch)
    active = runtime()
    packet = await signed(payload, active)
    mocks["stored_issuance"].return_value = packet
    monkeypatch.setattr(repository, "reference_captures", mocks["reference_captures"])
    async with AsyncSession() as session:
        result = await service.export(
            session,
            payload.version.workspace_id,
            ACTOR,
            payload.campaign.id,
            PassportRuntime(active.trust),
        )
    assert result == packet
    mocks["remember_issuance"].assert_not_called()


@pytest.mark.asyncio
async def test_replayed_export_refuses_changed_references(monkeypatch: pytest.MonkeyPatch) -> None:
    payload, mocks = setup(monkeypatch)
    active = runtime()
    mocks["stored_issuance"].return_value = await signed(payload, active)
    monkeypatch.setattr(repository, "reference_captures", AsyncMock(return_value=()))
    async with AsyncSession() as session:
        with pytest.raises(ConflictError):
            await service.export(
                session, payload.version.workspace_id, ACTOR, payload.campaign.id, active
            )
    mocks["remember_issuance"].assert_not_called()


def test_remember_issuance_stores_one_record_and_identifier_only_event() -> None:
    from accord.personas.issuance_models import PassportIssuance
    from personas.passport_fixtures import material

    payload, _ = material()
    session = Mock(spec=AsyncSession)
    package = Mock()
    repository.remember_issuance(session, payload.version.workspace_id, ACTOR, payload, package)
    rows = [call.args[0] for call in session.add.call_args_list]
    assert len(rows) == 2 and isinstance(rows[0], PassportIssuance)
    assert rows[0].acceptance_id == payload.acceptance_id
    assert rows[1].action == "persona.passport_issued"
    assert rows[1].metadata_ == {"version_id": str(payload.version.version_id)}


@pytest.mark.asyncio
async def test_committed_replay_rechecks_membership_before_disclosure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload, mocks = setup(monkeypatch)
    active = runtime()
    mocks["stored_issuance"].return_value = await signed(payload, active)
    mocks["authorize_actor"].side_effect = AccessDeniedError("membership lost during replay")
    monkeypatch.setattr(repository, "reference_captures", mocks["reference_captures"])
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await service.export(
                session, payload.version.workspace_id, ACTOR, payload.campaign.id, active
            )
    mocks["observation"].assert_not_called()
