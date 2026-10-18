"""Enrollment derives hashes from inspected evidence and denies every missing boundary."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import asset_service as service
from accord.personas.asset_contracts import EnrollAsset
from accord.personas.asset_models import AssetEnrollment
from accord.personas.campaign_models import PersonaAsset
from accord.personas.evidence_models import EvidenceInspection, PrivateEvidence
from accord.personas.models import Persona, Version
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import fingerprint
from accord.personas.workflow_contracts import WorkflowActor


def setup(monkeypatch: pytest.MonkeyPatch) -> tuple[EnrollAsset, dict[str, Mock]]:
    workspace, version, evidence = uuid4(), uuid4(), uuid4()
    command = EnrollAsset(
        request_id=uuid4(),
        version_id=version,
        evidence_id=evidence,
        label="Fictional scene",
        permission_statement="Creator-owned test illustration.",
    )
    now = datetime.now(UTC)
    row = PrivateEvidence(
        id=evidence,
        workspace_id=workspace,
        version_id=version,
        owner_ref="synthetic-owner",
        sha256="a" * 64,
        byte_length=4,
        media_type="text/plain",
        recorded_at=now,
        expires_at=now + timedelta(days=7),
    )
    mocks = {
        "authorize_actor": AsyncMock(),
        "locked_version": AsyncMock(
            return_value=(
                Version(id=version, revision=1),
                Persona(owner_ref="synthetic-owner", head_revision=1),
            )
        ),
        "owned": AsyncMock(return_value=row),
        "inspection": AsyncMock(return_value=EvidenceInspection(verdict="clean")),
        "payload": AsyncMock(return_value=object()),
    }
    for name, mock in mocks.items():
        monkeypatch.setattr(service, name, mock)
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    return command, mocks


@pytest.mark.asyncio
async def test_enrollment_derives_content_hash_and_seals_only_server_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command, mocks = setup(monkeypatch)
    workspace = mocks["owned"].return_value.workspace_id
    async with AsyncSession() as session:
        added = Mock()
        monkeypatch.setattr(session, "add", added)
        monkeypatch.setattr(session, "flush", AsyncMock())
        monkeypatch.setattr(session, "scalar", AsyncMock(side_effect=[None, None, 0]))
        result = await service.enroll(
            session, workspace, WorkflowActor(actor_ref="synthetic-owner", kind="human"), command
        )
    assert result.asset.digest == "a" * 64 and result.evidence_id == command.evidence_id
    rows = [call.args[0] for call in added.call_args_list]
    enrollment = next(row for row in rows if isinstance(row, AssetEnrollment))
    assert enrollment.permission_statement == command.permission_statement
    event = rows[-1]
    assert event.action == "persona.asset_registered" and event.source == "server"
    assert command.permission_statement not in str(event.metadata_)
    assert mocks["authorize_actor"].await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [
        "owner",
        "stale",
        "version",
        "expired",
        "uninspected",
        "rejected",
        "payload",
        "duplicate",
        "limit",
    ],
)
async def test_enrollment_denies_incomplete_or_changed_source(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    command, mocks = setup(monkeypatch)
    evidence = mocks["owned"].return_value
    version, persona = mocks["locked_version"].return_value
    expected: type[Exception] = AccessDeniedError
    values: list[object] = [None, None, 0]
    if failure == "owner":
        persona.owner_ref = "other"
    elif failure == "stale":
        persona.head_revision = 2
        expected = ConflictError
    elif failure == "version":
        evidence.version_id = uuid4()
    elif failure == "expired":
        evidence.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    elif failure == "uninspected":
        mocks["inspection"].return_value = None
    elif failure == "rejected":
        mocks["inspection"].return_value.verdict = "rejected"
    elif failure == "payload":
        mocks["payload"].return_value = None
    elif failure == "duplicate":
        values = [None, uuid4()]
        expected = ConflictError
    else:
        values = [None, None, 20]
        expected = ConflictError
    async with AsyncSession() as session:
        added = Mock()
        monkeypatch.setattr(session, "add", added)
        monkeypatch.setattr(session, "scalar", AsyncMock(side_effect=values))
        with pytest.raises(expected):
            await service.enroll(
                session,
                evidence.workspace_id,
                WorkflowActor(actor_ref="synthetic-owner", kind="human"),
                command,
            )
    added.assert_not_called()


@pytest.mark.asyncio
async def test_enrollment_replay_is_identical_and_changed_intent_conflicts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command, mocks = setup(monkeypatch)
    workspace = mocks["owned"].return_value.workspace_id
    existing = AssetEnrollment(asset_id=uuid4(), fingerprint=fingerprint(command))
    actor = WorkflowActor(actor_ref="synthetic-owner", kind="human")
    async with AsyncSession() as session:
        monkeypatch.setattr(session, "scalar", AsyncMock(return_value=existing))
        monkeypatch.setattr(
            session,
            "get",
            AsyncMock(
                return_value=PersonaAsset(
                    id=existing.asset_id, digest="a" * 64, label=command.label
                )
            ),
        )
        result = await service.enroll(session, workspace, actor, command)
        assert result.asset.id == existing.asset_id
        with pytest.raises(ConflictError):
            await service.enroll(
                session, workspace, actor, command.model_copy(update={"label": "changed"})
            )
    mocks["owned"].assert_not_called()
