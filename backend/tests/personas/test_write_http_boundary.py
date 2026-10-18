"""Actual prepared write routes, with explicit synthetic verification and stub services."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.main import create_app
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.write_http import create_write_router
from personas.governance_bridge import WIRE
from personas.test_session_boundary import verified
from personas.write_bridge import bridge, write_responses

OPERATIONS = (
    ("/versions/save", "save", "save"),
    ("/reviews/record", "reviewCommand", "record_review"),
    ("/campaigns/offer", "offer", "offer_campaign"),
    ("/campaigns/decide", "decisionCommand", "decide_campaign"),
)


@pytest.mark.parametrize("path,key,service", OPERATIONS)
@pytest.mark.parametrize("mode", ["missing", "denied", "expired", "failed"])
async def test_write_session_failure_never_opens_database(
    path: str, key: str, service: str, mode: str
) -> None:
    provider = AsyncMock()
    provider.verify.return_value = None
    if mode == "expired":
        provider.verify.return_value = verified(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    if mode == "failed":
        provider.verify.side_effect = RuntimeError("synthetic private identity detail")
    app = FastAPI()
    app.include_router(create_write_router(None if mode == "missing" else provider))

    async def unopened() -> AsyncSession:
        raise AssertionError("unverified write opened database")

    app.dependency_overrides[get_db] = unopened
    with patch(f"accord.personas.write_http.{service}", AsyncMock()) as mocked:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            result = await client.post(f"/api/workspaces/{uuid4()}/personas{path}", json={})
    assert result.status_code == (503 if mode in {"missing", "failed"} else 401)
    assert result.headers["cache-control"] == "no-store"
    assert "synthetic" not in result.text
    mocked.assert_not_awaited()


@pytest.mark.parametrize("path,key,name", OPERATIONS)
async def test_command_attribution_and_serialized_receipt(path: str, key: str, name: str) -> None:
    wire = json.loads(WIRE.read_text())
    body, actor = wire[key], "reviewer-a" if name == "record_review" else "creator-a"
    provider = AsyncMock()
    provider.verify.return_value = verified(actor_ref=actor)
    app = FastAPI()
    app.include_router(create_write_router(provider))
    session = AsyncSession()

    async def database() -> AsyncSession:
        return session

    app.dependency_overrides[get_db] = database
    value = write_responses(body, actor)[name]
    with patch(f"accord.personas.write_http.{name}", AsyncMock(return_value=value)) as service:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/workspaces/{wire['version']['workspace_id']}/personas{path}", json=body
            )
    assert response.status_code == 200 and response.json() == value.model_dump(mode="json")
    assert service.await_args is not None
    args = service.await_args.args
    assert args[0] is session and args[1] == UUID(wire["version"]["workspace_id"])
    assert args[2] == (actor if name == "save" else WorkflowActor(actor_ref=actor, kind="human"))
    assert args[3].model_dump(mode="json") == body
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("path,key,name", OPERATIONS)
@pytest.mark.parametrize("field", ["actor_ref", "role", "server_time"])
async def test_false_write_authority_is_rejected_before_service(
    path: str, key: str, name: str, field: str
) -> None:
    wire = json.loads(WIRE.read_text())
    body = {**wire[key], field: "synthetic private false authority"}
    provider = AsyncMock()
    provider.verify.return_value = verified()
    app = FastAPI()
    app.include_router(create_write_router(provider))

    async def database() -> AsyncSession:
        return AsyncSession()

    app.dependency_overrides[get_db] = database
    with patch(f"accord.personas.write_http.{name}", AsyncMock()) as service:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            result = await client.post(f"/api/workspaces/{uuid4()}/personas{path}", json=body)
    assert result.status_code == 422 and result.json()["error"]["code"] == "invalid_intent"
    assert "synthetic private" not in result.text
    service.assert_not_awaited()


@pytest.mark.parametrize(
    "error,status",
    [(AccessDeniedError, 403), (ConflictError, 409), (RuntimeError, 503), (ValueError, 500)],
)
async def test_write_faults_never_echo_private_details(error: type[Exception], status: int) -> None:
    provider = AsyncMock()
    provider.verify.return_value = verified()
    app = FastAPI()
    app.include_router(create_write_router(provider))

    async def failed_database() -> AsyncSession:
        raise error("synthetic private payload hostname")

    app.dependency_overrides[get_db] = failed_database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        result = await client.post(f"/api/workspaces/{uuid4()}/personas/versions/save", json={})
    assert result.status_code == status and "synthetic private" not in result.text
    assert result.headers["cache-control"] == "no-store"


async def test_initial_revision_is_sanitized_and_routes_are_mounted() -> None:
    wire = json.loads(WIRE.read_text())
    body = {**wire["save"], "persona_id": None, "expected_revision": 3}
    result = await bridge(f"/api/workspaces/{uuid4()}/personas/versions/save", body)
    assert result["status"] == 422
    assert any("personas" in path for path in create_app().openapi()["paths"])
    app = FastAPI()
    app.include_router(create_write_router())
    assert len(app.openapi()["paths"]) == 4
    assert all(set(methods) == {"post"} for methods in app.openapi()["paths"].values())


async def test_http_rejection_and_invalid_serialization_are_sanitized() -> None:
    provider = AsyncMock()
    provider.verify.return_value = verified()
    app = FastAPI()
    app.include_router(create_write_router(provider))

    async def database() -> AsyncSession:
        return AsyncSession()

    app.dependency_overrides[get_db] = database
    wire = json.loads(WIRE.read_text())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch(
            "accord.personas.write_http.save",
            AsyncMock(side_effect=HTTPException(429, "synthetic private detail")),
        ):
            result = await client.post(
                f"/api/workspaces/{uuid4()}/personas/versions/save", json=wire["save"]
            )
        assert result.status_code == 429 and "synthetic private" not in result.text
        with patch(
            "accord.personas.write_http.save",
            AsyncMock(return_value={"private": "synthetic private detail"}),
        ):
            result = await client.post(
                f"/api/workspaces/{uuid4()}/personas/versions/save", json=wire["save"]
            )
        assert result.status_code == 500 and "synthetic private" not in result.text
