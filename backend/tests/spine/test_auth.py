"""Auth scaffold: the request principal is resolved and recorded as the event actor."""

from __future__ import annotations

from typing import Any

from conftest import auth_headers, stream_events
from fakeredis.aioredis import FakeRedis
from httpx import AsyncClient


async def _last_event(redis: FakeRedis) -> dict[str, Any]:
    events = await stream_events(redis)
    assert events, "no telemetry event was emitted"
    return events[-1]


async def test_anonymous_client_report_is_denied(
    client: AsyncClient, fake_redis: FakeRedis
) -> None:
    resp = await client.post("/api/v1/client-events", json={"action": "client.route_view"})
    assert resp.status_code == 401
    assert await stream_events(fake_redis) == []


async def test_authenticated_request_records_principal(
    client: AsyncClient, fake_redis: FakeRedis
) -> None:
    resp = await client.post(
        "/api/v1/client-events", json={"action": "client.route_view"}, headers=auth_headers()
    )
    assert resp.status_code == 202
    event = await _last_event(fake_redis)
    assert event["actor"] == {"type": "user", "id": "user-123", "sid": "sess-9"}


async def test_forged_token_is_rejected(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/client-events",
        json={"action": "client.route_view"},
        headers={"Authorization": "Bearer user-123.sess-9.deadbeef"},
    )
    assert resp.status_code == 401


async def test_malformed_authorization_header_is_rejected(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/client-events",
        json={"action": "client.route_view"},
        headers={"Authorization": "Bearer not-a-token"},
    )
    assert resp.status_code == 401
