"""Fixed loopback wire requests and bounded response parsing without a socket connection."""

import asyncio
from typing import Literal
from unittest.mock import AsyncMock, Mock

import pytest

from accord.db.migration_job import proxy_request


@pytest.mark.parametrize(
    "operation,port,wire_request",
    [
        ("startup", 9090, b"GET /startup HTTP/1.1\r\nHost: 127.0.0.1:9090\r\n"),
        ("shutdown", 9091, b"POST /quitquitquit HTTP/1.1\r\nHost: 127.0.0.1:9091\r\n"),
    ],
)
async def test_proxy_request_has_fixed_destination_and_no_redirect_following(
    monkeypatch: pytest.MonkeyPatch,
    operation: Literal["startup", "shutdown"],
    port: int,
    wire_request: bytes,
) -> None:
    reader = AsyncMock()
    reader.readline.return_value = b"HTTP/1.1 302 Found\r\n"
    writer = AsyncMock()
    writer.write = Mock()
    writer.close = Mock()
    connect = AsyncMock(return_value=(reader, writer))
    monkeypatch.setattr(asyncio, "open_connection", connect)
    monkeypatch.setenv("HTTP_PROXY", "http://unreviewed.invalid")
    assert await proxy_request(operation) == 302
    connect.assert_awaited_once_with("127.0.0.1", port, limit=256)
    assert writer.write.call_args.args == (
        wire_request + b"Content-Length: 0\r\nConnection: close\r\n\r\n",
    )
    writer.close.assert_called_once()
    writer.wait_closed.assert_awaited_once()


@pytest.mark.parametrize(
    "line", [b"", b"HTTP/2 200 OK\r\n", b"HTTP/1.1 x00 OK\r\n", b"HTTP/1.1 200", b"HTTP/1.1 200 OK"]
)
async def test_malformed_status_fails_and_closes_stream(
    monkeypatch: pytest.MonkeyPatch,
    line: bytes,
) -> None:
    reader = AsyncMock()
    reader.readline.return_value = line
    writer = AsyncMock()
    writer.write = Mock()
    writer.close = Mock()
    monkeypatch.setattr(asyncio, "open_connection", AsyncMock(return_value=(reader, writer)))
    with pytest.raises(ValueError, match="invalid proxy status"):
        await proxy_request("startup")
    writer.close.assert_called_once()
    writer.wait_closed.assert_awaited_once()


async def test_startup_cancellation_closes_socket_without_extending_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from accord.db import migration_job as job

    async def delayed_line() -> bytes:
        await asyncio.sleep(1)
        return b"HTTP/1.1 200 OK\r\n"

    reader = AsyncMock()
    reader.readline.side_effect = delayed_line
    writer = AsyncMock()
    writer.write = Mock()
    writer.close = Mock()
    monkeypatch.setattr(asyncio, "open_connection", AsyncMock(return_value=(reader, writer)))
    monkeypatch.setattr(job, "STARTUP_SECONDS", 0.01)
    with pytest.raises(TimeoutError):
        await job.wait_for_proxy()
    writer.close.assert_called_once()
    writer.wait_closed.assert_not_awaited()


async def test_excessive_status_line_fails_and_closes_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reader = AsyncMock()
    reader.readline.side_effect = ValueError("Separator exceeds stream limit")
    writer = AsyncMock()
    writer.write = Mock()
    writer.close = Mock()
    monkeypatch.setattr(asyncio, "open_connection", AsyncMock(return_value=(reader, writer)))
    with pytest.raises(ValueError):
        await proxy_request("startup")
    writer.close.assert_called_once()
