"""Face commands are bounded after session resolution; no large image or vector body is accepted."""

from collections.abc import AsyncIterator
from uuid import uuid4

import httpx
import pytest

from personas.test_capture_http import private_app


@pytest.mark.asyncio
async def test_unverified_session_never_consumes_stream_and_oversize_is_rejected() -> None:
    workspace = uuid4()
    consumed = False

    async def body() -> AsyncIterator[bytes]:
        nonlocal consumed
        consumed = True
        yield b"x" * 4097

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=private_app(workspace)), base_url="http://synthetic"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/photos/faces/process"
        denied = await client.post(path, content=body())
        assert denied.status_code == 401 and not consumed
        invalid = await client.post(
            path, content=body(), headers={"x-synthetic-session": "current"}
        )
        assert invalid.status_code == 422 and consumed
        assert "no-store" in invalid.headers["cache-control"]
