"""Disconnected orchestration proofs; real SQL authorization is a separate lane."""

from dataclasses import replace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import investigation_service as service
from accord.personas.investigation_contracts import InvestigationHistory
from accord.personas.investigation_evidence import GroundedEvidence
from accord.personas.investigation_provider import (
    ComparisonInput,
    ComparisonOutput,
    InvestigationRuntime,
)
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.similarity_query import QueryCapture
from accord.personas.workflow_contracts import WorkflowActor
from personas.investigation_fixtures import command, result
from personas.test_face_processing import image_bytes
from personas.test_similarity_service import runtime


def trusted(monkeypatch: pytest.MonkeyPatch) -> dict[str, AsyncMock]:
    mocks = {
        name: AsyncMock()
        for name in (
            "authorize_actor",
            "locked_version",
            "replay",
            "history",
            "gather",
            "store",
            "require_query_open",
            "recheck_catalogue",
            "load",
        )
    }
    for name, mock in mocks.items():
        monkeypatch.setattr(service, name, mock)
    mocks["locked_version"].return_value = (Mock(revision=1), Mock(head_revision=1))
    mocks["replay"].return_value = None
    mocks["history"].return_value = []
    monkeypatch.setattr(service, "observation", Mock())
    monkeypatch.setattr(AsyncSession, "add", Mock())
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    return mocks


def inputs() -> tuple[InvestigationRuntime, GroundedEvidence]:
    packet = result()
    evidence = GroundedEvidence(
        QueryCapture(packet.query, "fixture", image_bytes(), image_bytes()),
        packet.search,
        ComparisonInput(image_bytes(), image_bytes(), packet.query.faces[0], packet.reference_face),
        packet.reference_sha256,
        (),
    )
    provider = Mock(
        compare=AsyncMock(
            return_value=ComparisonOutput(packet.model, packet.provider_revision, packet.findings)
        )
    )
    return InvestigationRuntime(runtime(), provider), evidence


@pytest.mark.asyncio
async def test_authorization_denial_precedes_replay_decryption_and_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mocks, active = trusted(monkeypatch), inputs()[0]
    mocks["authorize_actor"].side_effect = AccessDeniedError("denied")
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await service.generate(
                session, uuid4(), WorkflowActor(actor_ref="human", kind="human"), command(), active
            )
    mocks["locked_version"].assert_not_called()
    mocks["gather"].assert_not_called()
    mocks["load"].assert_not_called()


@pytest.mark.asyncio
async def test_generate_seals_only_packet_and_rechecks_after_encryption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mocks, (active, evidence) = trusted(monkeypatch), inputs()
    intent, workspace = command(), evidence.capture.receipt.workspace_id
    # Bind the synthetic fresh search to this exact intent.
    evidence = replace(
        evidence, search=evidence.search.model_copy(update={"request_id": intent.request_id})
    )
    mocks["gather"].return_value = evidence
    async with AsyncSession() as session:
        packet = await service.generate(
            session, workspace, WorkflowActor(actor_ref="human", kind="human"), intent, active
        )
    assert packet.actor_ref == "human" and packet.source_note == intent.source_note
    assert "vectors" not in packet.model_dump_json() and "query_image" in packet.model_dump_json()
    mocks["store"].assert_awaited_once()
    mocks["recheck_catalogue"].assert_awaited_once()
    assert mocks["require_query_open"].await_count == 2
    assert mocks["authorize_actor"].await_count == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["provider", "clear", "catalogue", "permission"])
async def test_failure_never_returns_a_completed_packet(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    mocks, (active, evidence) = trusted(monkeypatch), inputs()
    intent = command()
    evidence = replace(
        evidence, search=evidence.search.model_copy(update={"request_id": intent.request_id})
    )
    mocks["gather"].return_value = evidence
    expected: type[Exception] = RuntimeError
    if failure == "provider":
        active = replace(
            active,
            provider=Mock(compare=AsyncMock(side_effect=RuntimeError("provider unavailable"))),
        )
    elif failure == "clear":
        expected = HTTPException
        mocks["require_query_open"].side_effect = [None, HTTPException(410)]
    elif failure == "catalogue":
        expected = ConflictError
        mocks["recheck_catalogue"].side_effect = ConflictError("changed")
    else:
        expected = AccessDeniedError
        mocks["authorize_actor"].side_effect = [None, None, AccessDeniedError("removed")]
    async with AsyncSession() as session:
        with pytest.raises(expected):
            await service.generate(
                session,
                evidence.capture.receipt.workspace_id,
                WorkflowActor(actor_ref="human", kind="human"),
                intent,
                active,
            )
        assert not session.new


@pytest.mark.asyncio
async def test_committed_retry_replays_without_query_or_provider_and_conflict_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mocks, (active, _) = trusted(monkeypatch), inputs()
    packet = result()
    mocks["replay"].return_value = Mock()
    mocks["load"].return_value = packet
    active = replace(active, provider=None)
    async with AsyncSession() as session:
        assert (
            await service.generate(
                session,
                packet.workspace_id,
                WorkflowActor(actor_ref="human", kind="human"),
                command(),
                active,
            )
            == packet
        )
    mocks["gather"].assert_not_called()
    mocks["replay"].side_effect = ConflictError("changed intent")
    async with AsyncSession() as session:
        with pytest.raises(ConflictError):
            await service.generate(
                session,
                packet.workspace_id,
                WorkflowActor(actor_ref="human", kind="human"),
                command(),
                active,
            )


@pytest.mark.asyncio
async def test_history_read_remains_available_without_provider_but_reauthorizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mocks, packet = trusted(monkeypatch), result()
    mocks["history"].return_value = [Mock(ordinal=1)]
    mocks["load"].return_value = packet
    active = replace(inputs()[0], provider=None)
    actor = WorkflowActor(actor_ref="human", kind="human")
    async with AsyncSession() as session:
        page = await service.read_history(
            session,
            packet.workspace_id,
            actor,
            InvestigationHistory(version_id=packet.version_id),
            active,
        )
    assert page.items == (packet,)
    assert mocks["authorize_actor"].await_count == 2
    mocks["authorize_actor"].side_effect = [None, AccessDeniedError("revoked during key call")]
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await service.read_history(
                session,
                packet.workspace_id,
                actor,
                InvestigationHistory(version_id=packet.version_id),
                active,
            )
