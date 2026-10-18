"""Existing bounded clamd command framing and deterministic cleanup on all outcomes."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from accord.personas.photo_scanner import ClamdScanner


@pytest.mark.parametrize("failure", [None, "read", "drain", "oversized", "incomplete"])
async def test_command_bounds_response_and_closes_stream_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    failure: str | None,
) -> None:
    reader = AsyncMock()
    reader.readuntil.return_value = b"PONG\x00"
    writer = AsyncMock()
    writer.write = Mock()
    writer.close = Mock()
    if failure == "read":
        reader.readuntil.side_effect = OSError("synthetic read failure")
    elif failure == "drain":
        writer.drain.side_effect = OSError("synthetic drain failure")
    elif failure == "oversized":
        reader.readuntil.side_effect = asyncio.LimitOverrunError("oversized", 1025)
    elif failure == "incomplete":
        reader.readuntil.side_effect = asyncio.IncompleteReadError(b"PON", None)
    connect = AsyncMock(return_value=(reader, writer))
    monkeypatch.setattr(asyncio, "open_connection", connect)
    scanner = ClamdScanner()
    if failure:
        with pytest.raises((OSError, asyncio.LimitOverrunError, asyncio.IncompleteReadError)):
            await scanner.command(b"zPING\x00")
    else:
        assert await scanner.command(b"zPING\x00") == b"PONG\x00"
    connect.assert_awaited_once_with("127.0.0.1", 3310, limit=1024)
    writer.write.assert_called_once_with(b"zPING\x00")
    writer.close.assert_called_once()
    writer.wait_closed.assert_awaited_once()
    if failure != "drain":
        reader.readuntil.assert_awaited_once_with(b"\x00")


async def test_stream_shutdown_wait_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    async def delayed_close() -> None:
        await asyncio.sleep(2)

    reader = AsyncMock()
    reader.readuntil.return_value = b"PONG\x00"
    writer = AsyncMock()
    writer.write = Mock()
    writer.close = Mock()
    writer.wait_closed.side_effect = delayed_close
    monkeypatch.setattr(asyncio, "open_connection", AsyncMock(return_value=(reader, writer)))
    with pytest.raises(TimeoutError):
        await ClamdScanner().command(b"zPING\x00")
    writer.close.assert_called_once()
