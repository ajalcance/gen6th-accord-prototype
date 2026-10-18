"""Saved internal handoffs never become approvals; identity comes only from the session."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import investigation_reviews as service
from accord.personas.investigation_contracts import InvestigationHistory
from accord.personas.investigation_review_contracts import (
    InvestigationReviewCommand,
    InvestigationReviewPage,
)
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.workflow_contracts import WorkflowActor
from personas.test_capture_http import private_app


def command() -> InvestigationReviewCommand:
    return InvestigationReviewCommand(
        request_id=uuid4(), version_id=uuid4(), investigation_id=uuid4()
    )


def row(c: InvestigationReviewCommand) -> Mock:
    from datetime import UTC, datetime

    return Mock(
        id=uuid4(),
        workspace_id=uuid4(),
        ordinal=1,
        requester_ref="session-human",
        requested_at=datetime.now(UTC),
        **c.model_dump(),
    )


def trusted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service, "authorize_actor", AsyncMock())
    monkeypatch.setattr(
        service, "locked_version", AsyncMock(return_value=(Mock(revision=1), Mock(head_revision=1)))
    )
    monkeypatch.setattr(service, "observation", Mock())
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())


@pytest.mark.parametrize(
    "field,value", [("actor_ref", "browser"), ("decision", "approved"), ("state", "approved")]
)
def test_browser_identity_or_approval_is_not_a_request(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        InvestigationReviewCommand.model_validate({**command().model_dump(), field: value})


@pytest.mark.asyncio
async def test_request_and_committed_replay_keep_exact_binding_and_server_attribution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trusted(monkeypatch)
    c, actor = command(), WorkflowActor(actor_ref="session-human", kind="human")
    record = row(c)
    prior, append = AsyncMock(return_value=None), AsyncMock(return_value=record)
    monkeypatch.setattr(service, "prior_request", prior)
    monkeypatch.setattr(service, "append_request", append)
    async with AsyncSession() as session:
        receipt = await service.request_review(session, record.workspace_id, actor, c)
    assert receipt.state == "requested" and receipt.requester_ref == actor.actor_ref
    assert receipt.investigation_id == c.investigation_id
    prior.return_value = record
    async with AsyncSession() as session:
        assert await service.request_review(session, record.workspace_id, actor, c) == receipt
    assert append.await_count == 1


@pytest.mark.asyncio
async def test_replay_conflict_and_denial_prevent_append(monkeypatch: pytest.MonkeyPatch) -> None:
    trusted(monkeypatch)
    append = AsyncMock()
    monkeypatch.setattr(service, "append_request", append)
    monkeypatch.setattr(
        service, "prior_request", AsyncMock(side_effect=ConflictError("changed evidence"))
    )
    async with AsyncSession() as session:
        with pytest.raises(ConflictError):
            await service.request_review(
                session, uuid4(), WorkflowActor(actor_ref="human", kind="human"), command()
            )
    monkeypatch.setattr(
        service, "authorize_actor", AsyncMock(side_effect=AccessDeniedError("denied"))
    )
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await service.request_review(
                session, uuid4(), WorkflowActor(actor_ref="human", kind="human"), command()
            )
    append.assert_not_called()


@pytest.mark.asyncio
async def test_new_handoff_requires_exact_authorized_stored_packet() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = None
    with pytest.raises(AccessDeniedError):
        await service.append_request(
            session, uuid4(), WorkflowActor(actor_ref="human", kind="human"), command()
        )
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_changed_request_ids_conflict_and_history_is_version_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c, record = command(), row(command())
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = record
    with pytest.raises(ConflictError):
        await service.prior_request(session, uuid4(), "human", c)
    trusted(monkeypatch)
    record = row(c)
    monkeypatch.setattr(service, "requests", AsyncMock(return_value=[record]))
    async with AsyncSession() as real:
        page = await service.history(
            real,
            record.workspace_id,
            WorkflowActor(actor_ref="human", kind="human"),
            InvestigationHistory(version_id=c.version_id),
        )
    assert page.items[0].version_id == c.version_id and page.items[0].state == "requested"


@pytest.mark.asyncio
async def test_request_routes_are_private_and_bind_to_synthetic_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c = command()
    receipt = service.receipt(row(c))
    request = AsyncMock(return_value=receipt)
    monkeypatch.setattr(service, "request_review", request)
    monkeypatch.setattr(
        service,
        "history",
        AsyncMock(
            return_value=InvestigationReviewPage(
                workspace_id=receipt.workspace_id, version_id=c.version_id, items=(receipt,)
            )
        ),
    )
    monkeypatch.setattr("accord.personas.similarity_http.authorize_actor", AsyncMock())
    monkeypatch.setattr("accord.personas.similarity_service.observation", Mock())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=private_app(receipt.workspace_id)),
        base_url="http://fixture",
    ) as client:
        path = (
            f"/api/workspaces/{receipt.workspace_id}/personas/photos/investigations/review-requests"
        )
        assert (await client.post(f"{path}/request", json={})).status_code == 401
        headers = {"x-synthetic-session": "current"}
        response = await client.post(
            f"{path}/request", json=c.model_dump(mode="json"), headers=headers
        )
        assert response.status_code == 200 and response.json()["state"] == "requested"
        assert response.headers["cache-control"] == "no-store"
        assert request.await_args is not None
        assert request.await_args.args[2].actor_ref == "synthetic-human"
        history = await client.post(
            f"{path}/history", json={"version_id": str(c.version_id)}, headers=headers
        )
        assert history.status_code == 200 and history.json()["items"][0]["investigation_id"] == str(
            c.investigation_id
        )
