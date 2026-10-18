"""Exercise actual unregistered ASGI routes without database or real identity access."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.main import create_app
from accord.personas.read_http import create_read_router
from personas.test_session_boundary import verified


@pytest.mark.parametrize("endpoint", ["/query", "/versions/query"])
@pytest.mark.parametrize("provider_result", ["missing", "denied", "failed", "expired"])
async def test_rejected_session_never_opens_database(endpoint: str, provider_result: str) -> None:
    synthetic = AsyncMock()
    synthetic.verify.return_value = None
    expected = 401
    if provider_result == "failed":
        synthetic.verify.side_effect = RuntimeError("private synthetic provider detail")
        expected = 503
    if provider_result == "missing":
        expected = 503
    elif provider_result == "expired":
        from datetime import UTC, datetime, timedelta

        synthetic.verify.return_value = verified(
            expires_at=datetime.now(UTC) - timedelta(seconds=1)
        )
    app = FastAPI()
    app.include_router(create_read_router(None if provider_result == "missing" else synthetic))

    async def unopened_database() -> AsyncSession:
        raise AssertionError("rejected sessions must not open the database")

    app.dependency_overrides[get_db] = unopened_database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/api/workspaces/{uuid4()}/personas{endpoint}", json={})
    assert response.status_code == expected
    assert response.headers["cache-control"] == "no-store"
    assert set(response.json()) == {"error"}
    assert "private synthetic" not in response.text


async def test_real_app_mounts_routes_but_denies_missing_provider() -> None:
    app = create_app()
    paths = app.openapi()["paths"]
    assert any("personas" in path for path in paths)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        result = await client.post(f"/api/workspaces/{uuid4()}/personas/query", json={})
    assert result.status_code == 503 and result.headers["cache-control"] == "no-store"


async def test_no_get_or_mutation_routes_are_prepared() -> None:
    app = FastAPI()
    app.include_router(create_read_router())
    paths = app.openapi()["paths"]
    assert len(paths) == 2
    assert all(set(operations) == {"post"} for operations in paths.values())


async def test_database_failure_returns_only_sanitized_unavailable_error() -> None:
    provider = AsyncMock()
    provider.verify.return_value = verified()
    app = FastAPI()
    app.include_router(create_read_router(provider))

    async def failed_database() -> AsyncSession:
        raise RuntimeError("synthetic private database hostname")

    app.dependency_overrides[get_db] = failed_database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/api/workspaces/{uuid4()}/personas/query", json={})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "read_unavailable"
    assert "hostname" not in response.text
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("body", [{"actor_ref": "creator-a"}, {"limit": 101}, {"search": "x" * 81}])
async def test_invalid_body_is_sanitized_without_echoing_input(body: dict[str, object]) -> None:
    provider = AsyncMock()
    provider.verify.return_value = verified()
    app = FastAPI()
    app.include_router(create_read_router(provider))

    async def idle_database() -> AsyncSession:
        return AsyncSession()

    app.dependency_overrides[get_db] = idle_database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/api/workspaces/{uuid4()}/personas/query", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_query"
    assert "creator-a" not in response.text and "input" not in response.json()["error"]
