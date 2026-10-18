"""Prepared governance routes validate wire DTOs and fail closed before database access."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.governance_contracts import VersionHistoryQuery, VersionObjectsQuery
from accord.personas.governance_http import create_governance_read_router
from personas.governance_bridge import bridge, responses
from personas.test_session_boundary import verified

PATHS = (
    "/versions/history/query",
    "/reviews/history/query",
    "/campaigns/query",
    "/campaigns/history/query",
    "/campaigns/status/query",
    "/workflow/evidence/query",
    "/evidence/query",
    "/evidence/status/query",
)


@pytest.mark.parametrize(
    "values", [{"limit": 0}, {"limit": 101}, {"limit": True}, {"actor_ref": "creator-a"}]
)
def test_discovery_request_bounds_and_false_authority(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        VersionHistoryQuery.model_validate({"persona_id": uuid4(), **values})
    with pytest.raises(ValidationError):
        VersionObjectsQuery.model_validate({"version_id": uuid4(), **values})


@pytest.mark.parametrize("cursor", [0, -1, True, "1"])
def test_version_cursor_must_be_a_positive_integer(cursor: object) -> None:
    with pytest.raises(ValidationError):
        VersionHistoryQuery.model_validate({"persona_id": uuid4(), "before_revision": cursor})


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("mode", ["missing", "expired", "revoked", "failed"])
async def test_session_failure_precedes_database_access(path: str, mode: str) -> None:
    provider = AsyncMock()
    provider.verify.return_value = None
    if mode == "expired":
        from datetime import UTC, datetime, timedelta

        provider.verify.return_value = verified(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    if mode == "failed":
        provider.verify.side_effect = RuntimeError("synthetic secret")
    app = FastAPI()
    app.include_router(create_governance_read_router(None if mode == "missing" else provider))

    async def unopened() -> AsyncSession:
        raise AssertionError("unverified session opened database")

    app.dependency_overrides[get_db] = unopened
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        result = await client.post(f"/api/workspaces/{uuid4()}/personas{path}", json={})
    assert result.status_code == (503 if mode in {"missing", "failed"} else 401)
    assert result.headers["cache-control"] == "no-store"
    assert "synthetic" not in result.text


def test_factory_is_read_only_and_bounded() -> None:
    app = FastAPI()
    app.include_router(create_governance_read_router())
    paths = app.openapi()["paths"]
    assert len(paths) == 8 and all(set(operations) == {"post"} for operations in paths.values())


async def test_real_asgi_serialization_for_all_prepared_governance_reads() -> None:
    data = responses()
    version = data["load"].model_dump(mode="json")
    workspace, version_id = version["workspace_id"], version["version_id"]
    commands = (
        (PATHS[0], {"persona_id": version["persona_id"]}, "version_history"),
        (PATHS[1], {"version_id": version_id}, "review_history"),
        (PATHS[2], {"version_id": version_id}, "campaign_offers"),
        (
            PATHS[3],
            {"campaign_id": data["inspect_campaign"].model_dump(mode="json")["receipt"]["id"]},
            "campaign_history",
        ),
        (
            PATHS[4],
            {"campaign_id": data["inspect_campaign"].model_dump(mode="json")["receipt"]["id"]},
            "inspect_campaign",
        ),
        (
            PATHS[5],
            {
                "record_id": data["inspect_workflow_evidence"].model_dump(mode="json")["anchor"][
                    "record_id"
                ],
                "kind": "review",
            },
            "inspect_workflow_evidence",
        ),
        (PATHS[6], {"version_id": version_id}, "evidence_list"),
        (
            PATHS[7],
            {"evidence_id": data["evidence_status"].model_dump(mode="json")["id"]},
            "evidence_status",
        ),
    )
    for path, body, name in commands:
        result = await bridge(f"/api/workspaces/{workspace}/personas{path}", body)
        assert result["status"] == 200 and result["body"] == data[name].model_dump(mode="json")


@pytest.mark.parametrize(
    "body",
    [
        {"version_id": str(uuid4()), "actor_ref": "creator-a"},
        {"version_id": str(uuid4()), "limit": 101},
        {"version_id": str(uuid4()), "limit": True},
    ],
)
async def test_query_rejects_false_identity_and_unbounded_lists(body: dict[str, object]) -> None:
    result = await bridge(f"/api/workspaces/{uuid4()}/personas/evidence/query", body)
    assert result["status"] == 422
    assert "creator-a" not in str(result["body"])
