"""Party isolation and bounded owner-only asset discovery before any signing work."""

from typing import cast
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import passport_repository as repository
from accord.personas.repository import AccessDeniedError
from accord.personas.workflow_contracts import WorkflowActor


@pytest.mark.asyncio
@pytest.mark.parametrize("actor", ["owner", "recipient", "other"])
async def test_campaign_parties_are_checked_before_version_disclosure(
    monkeypatch: pytest.MonkeyPatch, actor: str
) -> None:
    authorized, version = AsyncMock(), AsyncMock(return_value=(Mock(), Mock()))
    monkeypatch.setattr(repository, "authorize_actor", authorized)
    monkeypatch.setattr(
        repository,
        "offer_row",
        AsyncMock(return_value=Mock(owner_ref="owner", recipient_ref="recipient")),
    )
    monkeypatch.setattr(repository, "locked_version", version)
    who = WorkflowActor(actor_ref=actor, kind="human")
    session = cast(AsyncSession, Mock())
    if actor == "other":
        with pytest.raises(AccessDeniedError):
            await repository.campaign_access(session, uuid4(), who, uuid4())
        version.assert_not_called()
    else:
        await repository.campaign_access(session, uuid4(), who, uuid4())
        version.assert_awaited_once()
    authorized.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["normal", "empty", "overflow", "other_owner", "denied"])
async def test_asset_read_requires_owner_and_fresh_membership_and_bounds(
    monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    workspace, version = uuid4(), uuid4()
    who = WorkflowActor(actor_ref="owner", kind="human")
    auth = AsyncMock(side_effect=AccessDeniedError("denied") if mode == "denied" else None)
    monkeypatch.setattr(repository, "authorize_actor", auth)
    monkeypatch.setattr(
        repository,
        "locked_version",
        AsyncMock(
            return_value=(Mock(), Mock(owner_ref="other" if mode == "other_owner" else "owner"))
        ),
    )
    rows = [] if mode == "empty" else [Mock(id=uuid4(), digest="a" * 64, label="Synthetic asset")]
    if mode == "overflow":
        rows *= 21
    scalars = AsyncMock(return_value=rows)
    monkeypatch.setattr(AsyncSession, "scalars", scalars)
    event = Mock()
    monkeypatch.setattr(repository, "observation", event)
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    async with AsyncSession() as session:
        if mode in {"overflow", "other_owner", "denied"}:
            with pytest.raises(RuntimeError if mode == "overflow" else AccessDeniedError):
                await repository.assets(session, workspace, who, version)
            event.assert_not_called()
        else:
            result = await repository.assets(session, workspace, who, version)
            assert result.version_id == version and len(result.assets) == len(rows)
            assert auth.await_count == 2
            event.assert_called_once()
    if mode in {"other_owner", "denied"}:
        scalars.assert_not_called()
