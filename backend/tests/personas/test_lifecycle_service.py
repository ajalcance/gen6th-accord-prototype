"""Authority separation, independent attestation, CAS and replay without a live DB."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import lifecycle_service as service
from accord.personas.lifecycle_contracts import AppendLifecycle, Response
from accord.personas.lifecycle_models import LifecycleRecord
from accord.personas.lifecycle_repository import replay
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.workflow_contracts import WorkflowActor
from personas.lifecycle_fixtures import assessment, command, dossier, response_command


def actor(name: str = "creator-a") -> WorkflowActor:
    return WorkflowActor(actor_ref=name, kind="human")


@pytest.mark.asyncio
async def test_owner_and_operator_cannot_self_review(monkeypatch: pytest.MonkeyPatch) -> None:
    session, workspace, persona = (
        AsyncMock(spec=AsyncSession),
        uuid4(),
        Mock(id=uuid4(), owner_ref="creator-a"),
    )
    monkeypatch.setattr(service, "authorize_actor", AsyncMock())
    with pytest.raises(AccessDeniedError):
        await service.check_authority(session, workspace, actor("other"), persona, command())
    c = command().model_copy(update={"content": assessment(uuid4())})
    with pytest.raises(AccessDeniedError):
        await service.check_authority(session, workspace, actor(), persona, c)
    monkeypatch.setattr(
        service,
        "target_record",
        AsyncMock(return_value=Mock(content=dossier("reviewer").model_dump(mode="json"))),
    )
    with pytest.raises(AccessDeniedError):
        await service.check_authority(session, workspace, actor("reviewer"), persona, c)


@pytest.mark.asyncio
async def test_reporter_cannot_decide_own_concern(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service, "authorize_actor", AsyncMock())
    monkeypatch.setattr(
        service, "target_record", AsyncMock(return_value=Mock(actor_ref="reviewer"))
    )
    c = AppendLifecycle(
        version_id=uuid4(),
        request_id=uuid4(),
        content=Response(
            kind="response", concern_id=uuid4(), decision="suspended", statement="Synthetic concern"
        ),
    )
    with pytest.raises(AccessDeniedError):
        await service.check_authority(
            AsyncMock(), uuid4(), actor("reviewer"), Mock(id=uuid4(), owner_ref="creator-a"), c
        )


@pytest.mark.asyncio
async def test_nominated_operator_cannot_decide_performer_concern(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service, "authorize_actor", AsyncMock())
    monkeypatch.setattr(service, "target_record", AsyncMock(return_value=Mock(actor_ref="viewer")))
    monkeypatch.setattr(
        service,
        "latest",
        AsyncMock(return_value=Mock(content=dossier("reviewer").model_dump(mode="json"))),
    )
    with pytest.raises(AccessDeniedError, match="operator"):
        await service.check_authority(
            AsyncMock(),
            uuid4(),
            actor("reviewer"),
            Mock(id=uuid4(), owner_ref="creator-a"),
            response_command(uuid4(), uuid4()),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("state, next_state", [("resolved", "suspended"), ("suspended", "open")])
async def test_suspension_requires_resolution_and_resolved_cases_are_terminal(
    monkeypatch: pytest.MonkeyPatch,
    state: str,
    next_state: str,
) -> None:
    c = response_command(uuid4(), uuid4())
    previous = Mock(id=uuid4(), content=c.content.model_dump(mode="json"))
    previous.content["decision"] = state
    monkeypatch.setattr(service, "latest", AsyncMock(return_value=previous))
    c = c.model_copy(
        update={
            "expected_previous_id": previous.id,
            "content": c.content.model_copy(update={"decision": next_state}),
        }
    )
    with pytest.raises(ConflictError):
        await service.validate_append(
            AsyncMock(), uuid4(), actor("reviewer"), Mock(id=c.version_id), Mock(id=uuid4()), c
        )


def test_lifecycle_observation_excludes_dossier_claims() -> None:
    from accord.personas.lifecycle_repository import observe

    session = Mock()
    observe(session, uuid4(), actor(), uuid4(), uuid4(), "lifecycle_dossier")
    event = session.add.call_args.args[0]
    assert event.action == "persona.workspace_observed"
    assert event.resource_type == "persona_lifecycle_record"
    assert event.metadata_ == {"operation": "lifecycle_dossier"}


@pytest.mark.asyncio
async def test_stale_dossier_and_changed_review_do_not_append(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock(spec=AsyncSession)
    c, persona = command(), Mock(id=uuid4(), owner_ref="creator-a", head_revision=1)
    version = Mock(id=c.version_id, revision=1)
    monkeypatch.setattr(service, "latest", AsyncMock(return_value=None))
    session.get.return_value = None
    with pytest.raises(AccessDeniedError):
        await service.validate_append(session, uuid4(), actor(), version, persona, c)
    session.get.return_value = Mock()
    monkeypatch.setattr(service, "capture_digests", AsyncMock(return_value={}))
    monkeypatch.setattr(service, "latest", AsyncMock(return_value=Mock(id=uuid4())))
    with pytest.raises(ConflictError):
        await service.validate_append(session, uuid4(), actor(), version, persona, c)
    c = c.model_copy(update={"content": assessment(uuid4())})
    with pytest.raises(ConflictError, match="dossier changed"):
        await service.validate_append(session, uuid4(), actor("reviewer"), version, persona, c)


@pytest.mark.asyncio
async def test_exact_replay_conflicts_on_changed_payload() -> None:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.return_value = Mock(fingerprint="old")
    with pytest.raises(ConflictError):
        await replay(session, uuid4(), "creator-a", uuid4(), "changed")


@pytest.mark.asyncio
async def test_append_and_retry_keep_server_attribution_and_one_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c, workspace, persona = command(), uuid4(), Mock(id=uuid4(), owner_ref="creator-a")
    monkeypatch.setattr(service, "authorize_actor", AsyncMock())
    monkeypatch.setattr(service, "check_authority", AsyncMock())
    monkeypatch.setattr(
        service, "locked_version", AsyncMock(return_value=(Mock(id=c.version_id), persona))
    )
    monkeypatch.setattr(service, "validate_append", AsyncMock(return_value=(None, None, {})))
    monkeypatch.setattr(service, "latest", AsyncMock(return_value=None))
    lookup = AsyncMock(return_value=None)
    monkeypatch.setattr(service, "replay", lookup)
    monkeypatch.setattr(service, "observe", Mock())
    async with AsyncSession() as session:
        flush = AsyncMock()
        monkeypatch.setattr(session, "flush", flush)
        monkeypatch.setattr(session, "add", Mock())
        saved = await service.append(session, workspace, actor(), c)
        assert saved.actor_ref == "creator-a" and saved.content == c.content
        lookup.return_value = LifecycleRecord(
            **{
                field: getattr(saved, field)
                for field in (
                    "id",
                    "workspace_id",
                    "persona_id",
                    "version_id",
                    "request_id",
                    "expected_previous_id",
                    "ordinal",
                    "actor_ref",
                    "recorded_at",
                )
            },
            content=c.content.model_dump(mode="json"),
            evidence_digests={},
            fingerprint="unused",
            kind="dossier",
        )
        assert await service.append(session, workspace, actor(), c) == saved
        assert flush.await_count == 1
