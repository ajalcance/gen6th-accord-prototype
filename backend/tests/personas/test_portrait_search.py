"""Exact search contracts and authorization order without a database/provider fallback."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import create_mock_engine
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.contracts import PersonaVersion
from accord.personas.portrait_search import (
    PortraitSearchPage,
    matching_versions,
    search_observation,
    search_portraits,
)
from accord.personas.repository import AccessDeniedError
from accord.personas.workflow_contracts import WorkflowActor
from personas.conftest import command


def page(workspace: UUID) -> PortraitSearchPage:
    item = PersonaVersion(
        workspace_id=workspace,
        persona_id=uuid4(),
        version_id=uuid4(),
        revision=1,
        creator_ref="synthetic-human",
        recorded_at=datetime.now(UTC),
        content=command().content,
    )
    return PortraitSearchPage(
        workspace_id=workspace, request_id=uuid4(), sha256="a" * 64, items=(item,), has_more=False
    )


@pytest.mark.parametrize("problem", ["duplicate", "foreign", "truncated", "method"])
def test_search_contract_rejects_invalid_candidate_evidence(problem: str) -> None:
    result = page(uuid4())
    value = result.model_dump()
    item = result.items[0]
    changes: dict[str, object] = {
        "duplicate": (item, item),
        "foreign": (item.model_copy(update={"workspace_id": uuid4()}),),
        "truncated": True,
        "method": "face_identity",
    }
    value[
        (
            "items"
            if problem in {"duplicate", "foreign"}
            else "has_more" if problem == "truncated" else "method"
        )
    ] = changes[problem]
    with pytest.raises(ValidationError):
        PortraitSearchPage.model_validate(value)


def test_search_statement_binds_all_tables_and_bounds_grouped_results() -> None:
    workspace = uuid4()
    engine = create_mock_engine("postgresql://", lambda *_args, **_kwargs: None)
    compiled = matching_versions(workspace, "a" * 64).compile(dialect=engine.dialect)
    sql = str(compiled)
    assert "DISTINCT ON (persona_versions.persona_id)" in sql
    assert "persona_versions.revision DESC" in sql
    assert all(
        f"{table}.workspace_id =" in sql
        for table in (
            "persona_versions",
            "persona_version_portraits",
            "persona_version_references",
            "persona_portraits",
        )
    )
    assert list(compiled.params.values()).count(workspace) == 5
    assert "UNION" in sql
    assert "a" * 64 in compiled.params.values() and 21 in compiled.params.values()
    assert "persona_portrait_payloads" not in sql


def test_observation_carries_only_server_attribution_and_bounded_counts() -> None:
    workspace = uuid4()
    actor = WorkflowActor(actor_ref="synthetic-human", kind="human")
    result = page(workspace)
    event = search_observation(workspace, actor, result)
    assert event.actor_id == actor.actor_ref and event.tenant_id == workspace
    assert event.action == "persona.workspace_observed" and event.source == "server"
    assert event.metadata_ == {
        "operation": "portrait_exact_search",
        "method": "exact_file_sha256",
        "returned": 1,
        "has_more": False,
    }
    assert result.sha256 not in str(event.metadata_)


@pytest.mark.asyncio
async def test_permission_is_checked_before_consuming_query_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    consumed = False

    async def unread() -> AsyncIterator[bytes]:
        nonlocal consumed
        consumed = True
        yield b"private query"

    reject = AsyncMock(side_effect=AccessDeniedError("synthetic denial"))
    record = AsyncMock()
    monkeypatch.setattr("accord.personas.portrait_search.authorize_actor", reject)
    monkeypatch.setattr("accord.personas.transactions.record_rejection", record)
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await search_portraits(
                session, uuid4(), WorkflowActor(actor_ref="synthetic-human", kind="human"), unread()
            )
    assert not consumed
    record.assert_awaited_once()
