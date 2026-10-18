"""Transactions retain owner/actor/CAS/replay boundaries without a live database."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import credit_service as service
from accord.personas.credit_contracts import ConfirmCredit, CreditContent, CreditSubject
from accord.personas.credit_models import CreditRecord
from accord.personas.credit_repository import replay
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.workflow_contracts import WorkflowActor
from personas.test_credit_contracts import declaration


def trusted(monkeypatch: pytest.MonkeyPatch, owner: str = "creator", revision: int = 1) -> None:
    monkeypatch.setattr(service, "authorize_actor", AsyncMock())
    monkeypatch.setattr(
        service,
        "locked_version",
        AsyncMock(return_value=(Mock(revision=revision), Mock(owner_ref=owner, head_revision=1))),
    )
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())


def record(workspace: UUID) -> Mock:
    c = declaration()
    return Mock(
        id=uuid4(),
        workspace_id=workspace,
        version_id=c.version_id,
        request_id=c.request_id,
        ordinal=1,
        declared_by="creator",
        recorded_at=datetime.now(UTC),
        content=c.content.model_dump(mode="json"),
    )


@pytest.mark.asyncio
async def test_save_and_replay_bind_server_source_and_do_not_duplicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trusted(monkeypatch)
    c, workspace = declaration(), uuid4()
    row = record(workspace)
    row.version_id, row.request_id = c.version_id, c.request_id
    lookup, append = AsyncMock(return_value=None), AsyncMock(return_value=row)
    monkeypatch.setattr(service, "replay", lookup)
    monkeypatch.setattr(service, "append", append)
    async with AsyncSession() as session:
        saved = await service.save(
            session, workspace, WorkflowActor(actor_ref="creator", kind="human"), c
        )
    assert saved.declared_by == "creator" and saved.version_id == c.version_id
    lookup.return_value = row
    async with AsyncSession() as session:
        assert (
            await service.save(
                session, workspace, WorkflowActor(actor_ref="creator", kind="human"), c
            )
            == saved
        )
    assert append.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("owner,revision", [("another-owner", 1), ("creator", 2)])
async def test_nonowner_and_historical_version_cannot_append(
    monkeypatch: pytest.MonkeyPatch, owner: str, revision: int
) -> None:
    trusted(monkeypatch, owner, revision)
    append = AsyncMock()
    monkeypatch.setattr(service, "replay", AsyncMock(return_value=None))
    monkeypatch.setattr(service, "append", append)
    async with AsyncSession() as session:
        with pytest.raises((AccessDeniedError, ConflictError)):
            await service.save(
                session, uuid4(), WorkflowActor(actor_ref="creator", kind="human"), declaration()
            )
    append.assert_not_called()


@pytest.mark.asyncio
async def test_stale_profile_unknown_member_and_foreign_evidence_do_not_append(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()
    monkeypatch.setattr(service, "latest", AsyncMock(return_value=Mock(id=uuid4())))
    with pytest.raises(ConflictError):
        await service.append(
            session, uuid4(), WorkflowActor(actor_ref="creator", kind="human"), declaration()
        )
    monkeypatch.setattr(service, "latest", AsyncMock(return_value=None))
    session.get.return_value = None
    with pytest.raises(AccessDeniedError):
        await service.append(
            session, uuid4(), WorkflowActor(actor_ref="creator", kind="human"), declaration()
        )
    session.get.return_value = Mock()
    c = declaration()
    credit = c.content.credits[0].model_copy(update={"evidence_id": uuid4()})
    c = c.model_copy(update={"content": CreditContent(credits=(credit,))})
    monkeypatch.setattr(service, "owned", AsyncMock(return_value=Mock(version_id=uuid4())))
    with pytest.raises(AccessDeniedError):
        await service.append(session, uuid4(), WorkflowActor(actor_ref="creator", kind="human"), c)
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_confirmation_stale_and_impersonating_creator_do_not_append(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()
    profile = record(uuid4())
    c = ConfirmCredit(
        request_id=uuid4(), version_id=profile.version_id, profile_id=uuid4(), credit_index=0
    )
    monkeypatch.setattr(service, "latest", AsyncMock(return_value=profile))
    with pytest.raises(ConflictError):
        await service.append_confirmation(
            session, profile.workspace_id, WorkflowActor(actor_ref="ari", kind="human"), c
        )
    c = c.model_copy(update={"profile_id": profile.id})
    with pytest.raises(AccessDeniedError):
        await service.append_confirmation(
            session, profile.workspace_id, WorkflowActor(actor_ref="creator", kind="human"), c
        )
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_append_records_declaration_and_server_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()
    session.get.return_value = Mock()
    session.scalar.return_value = None
    monkeypatch.setattr(service, "latest", AsyncMock(return_value=None))
    actor, workspace, c = WorkflowActor(actor_ref="creator", kind="human"), uuid4(), declaration()
    row = await service.append(session, workspace, actor, c)
    assert row.declared_by == actor.actor_ref and row.ordinal == 1
    assert row.content == c.content.model_dump(mode="json")
    monkeypatch.setattr(service, "latest", AsyncMock(return_value=row))
    intent = ConfirmCredit(
        request_id=uuid4(), version_id=c.version_id, profile_id=row.id, credit_index=0
    )
    accepted = await service.append_confirmation(
        session, workspace, WorkflowActor(actor_ref="ari", kind="human"), intent
    )
    assert accepted.actor_ref == "ari" and accepted.profile_id == row.id
    session.scalar.return_value = accepted.id
    with pytest.raises(ConflictError, match="already confirmed"):
        await service.append_confirmation(
            session, workspace, WorkflowActor(actor_ref="ari", kind="human"), intent
        )
    assert session.flush.await_count == 2


@pytest.mark.asyncio
async def test_changed_replay_payload_conflicts_before_success() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = Mock(fingerprint="old")
    with pytest.raises(ConflictError):
        await replay(session, CreditRecord, uuid4(), "creator", uuid4(), "new")


@pytest.mark.asyncio
async def test_empty_and_failed_profile_reads_are_distinct(monkeypatch: pytest.MonkeyPatch) -> None:
    trusted(monkeypatch)
    monkeypatch.setattr(service, "observe", Mock())
    monkeypatch.setattr(service, "latest", AsyncMock(return_value=None))
    actor, workspace = WorkflowActor(actor_ref="viewer", kind="human"), uuid4()
    async with AsyncSession() as session:
        result = await service.read(session, workspace, actor, CreditSubject(version_id=uuid4()))
    assert result.snapshot is None and not result.confirmations
    monkeypatch.setattr(service, "latest", AsyncMock(side_effect=RuntimeError("unavailable")))
    async with AsyncSession() as session:
        with pytest.raises(RuntimeError):
            await service.read(session, workspace, actor, CreditSubject(version_id=uuid4()))


def test_event_has_verified_actor_and_no_credit_content() -> None:
    session = Mock()
    service.observe(
        session,
        uuid4(),
        WorkflowActor(actor_ref="creator", kind="human"),
        uuid4(),
        uuid4(),
        "credits_declared",
    )
    event = session.add.call_args.args[0]
    assert event.actor_id == "creator" and event.source == "server"
    assert event.metadata_ == {"operation": "credits_declared"}
