"""Readiness denies ambiguous/stale replies without inspecting data or revealing errors."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, call

import pytest

from accord.personas import scanner_probe as probe
from accord.personas.photo_contracts import PhotoUnavailableError
from accord.personas.photo_scanner import ClamdScanner


def version(age: timedelta = timedelta()) -> bytes:
    stamp = (datetime.now(UTC) - age).strftime("%a %b %d %H:%M:%S %Y")
    return f"ClamAV 1.4.3/12345/{stamp}\x00".encode("ascii")


async def test_readiness_requires_ping_and_fresh_version_at_fixed_loopback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scanner = Mock()
    scanner.command = AsyncMock(side_effect=[b"PONG\x00", version()])
    factory = Mock(return_value=scanner)
    monkeypatch.setattr(probe, "ClamdScanner", factory)
    receipt = await probe.probe_scanner()
    assert receipt.engine == "ClamAV 1.4.3"
    assert receipt.definitions == "12345"
    factory.assert_called_once_with(host="127.0.0.1", port=3310)
    assert scanner.command.await_args_list == [call(b"zPING\x00"), call(b"zVERSION\x00")]


@pytest.mark.parametrize("reply", [b"", b"PONG", b"PONG\n", b"PONG\x00extra", b"ERROR\x00"])
async def test_ping_requires_exact_complete_response(
    monkeypatch: pytest.MonkeyPatch,
    reply: bytes,
) -> None:
    command = AsyncMock(return_value=reply)
    monkeypatch.setattr(ClamdScanner, "command", command)
    with pytest.raises(PhotoUnavailableError, match="^scanner readiness unavailable$"):
        await probe.probe_scanner()
    command.assert_awaited_once_with(b"zPING\x00")


@pytest.mark.parametrize(
    "reply",
    [
        b"",
        b"invalid\x00",
        b"ClamAV invalid/12345/invalid\x00",
        b"\xff\x00",
        pytest.param(timedelta(hours=49), id="stale-49-hours"),
        pytest.param(-timedelta(minutes=6), id="future-6-minutes"),
    ],
)
async def test_unavailable_definition_receipt_denies_readiness(
    monkeypatch: pytest.MonkeyPatch,
    reply: bytes | timedelta,
) -> None:
    if isinstance(reply, timedelta):
        reply = version(reply)
    command = AsyncMock(side_effect=[b"PONG\x00", reply])
    monkeypatch.setattr(ClamdScanner, "command", command)
    with pytest.raises(PhotoUnavailableError, match="^scanner readiness unavailable$"):
        await probe.probe_scanner()


@pytest.mark.parametrize(
    "age,accepted",
    [
        (timedelta(hours=48), True),
        (timedelta(hours=48, seconds=1), False),
        (-timedelta(minutes=5), True),
        (-timedelta(minutes=5, seconds=1), False),
    ],
)
async def test_readiness_preserves_exact_definition_age_boundaries(
    monkeypatch: pytest.MonkeyPatch,
    age: timedelta,
    accepted: bool,
) -> None:
    now = datetime(2026, 10, 11, 12, tzinfo=UTC)
    clock = Mock(wraps=datetime)
    clock.now.return_value = now
    monkeypatch.setattr("accord.personas.photo_scanner.datetime", clock)
    stamp = (now - age).strftime("%a %b %d %H:%M:%S %Y")
    reply = f"ClamAV 1.4.3/12345/{stamp}\x00".encode("ascii")
    monkeypatch.setattr(ClamdScanner, "command", AsyncMock(side_effect=[b"PONG\x00", reply]))
    if accepted:
        assert (await probe.probe_scanner()).definitions == "12345"
    else:
        with pytest.raises(PhotoUnavailableError, match="^scanner readiness unavailable$"):
            await probe.probe_scanner()


@pytest.mark.parametrize("phase", ["ping", "version"])
async def test_connection_failure_is_generic_and_retains_no_private_cause(
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
) -> None:
    private_error = OSError("synthetic-private-provider-detail")
    replies = [private_error] if phase == "ping" else [b"PONG\x00", private_error]
    monkeypatch.setattr(ClamdScanner, "command", AsyncMock(side_effect=replies))
    with pytest.raises(PhotoUnavailableError) as failure:
        await probe.probe_scanner()
    assert str(failure.value) == "scanner readiness unavailable"
    assert failure.value.__cause__ is None
    assert failure.value.__suppress_context__


async def test_overall_deadline_closes_pending_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    async def delayed_response(separator: bytes) -> bytes:
        await asyncio.sleep(1)
        return b"PONG\x00"

    reader = AsyncMock()
    reader.readuntil.side_effect = delayed_response
    writer = AsyncMock()
    writer.write = Mock()
    writer.close = Mock()
    monkeypatch.setattr(asyncio, "open_connection", AsyncMock(return_value=(reader, writer)))
    monkeypatch.setattr(probe, "PROBE_SECONDS", 0.01)
    with pytest.raises(PhotoUnavailableError, match="readiness unavailable"):
        await probe.probe_scanner()
    writer.close.assert_called_once()
    writer.wait_closed.assert_not_awaited()


@pytest.mark.parametrize("succeeded", [False, True])
def test_cli_emits_only_fixed_outcome(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    succeeded: bool,
) -> None:
    monkeypatch.setattr("sys.argv", ["scanner-probe"])
    monkeypatch.setattr(
        probe,
        "probe_scanner",
        AsyncMock(
            side_effect=None if succeeded else PhotoUnavailableError("synthetic-private-detail"),
        ),
    )
    with pytest.raises(SystemExit) as result:
        probe.main()
    assert result.value.code == (0 if succeeded else 1)
    output = capsys.readouterr()
    assert output.err == ""
    assert output.out == f"scanner_readiness={'passed' if succeeded else 'failed'}\n"


def test_cli_cannot_override_endpoint_or_echo_arguments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["scanner-probe", "--host", "synthetic-private-detail"])
    run = AsyncMock()
    monkeypatch.setattr(probe, "probe_scanner", run)
    with pytest.raises(SystemExit) as result:
        probe.main()
    assert result.value.code == 1
    run.assert_not_awaited()
    assert capsys.readouterr().out == "scanner_readiness=failed\n"


@pytest.mark.parametrize("response", ["valid", "oversized", "truncated", "malformed"])
async def test_real_stream_reader_enforces_framing_and_response_limit(
    monkeypatch: pytest.MonkeyPatch,
    response: str,
) -> None:
    ping = asyncio.StreamReader(limit=1024)
    ping.feed_data(b"PONG\x00")
    ping.feed_eof()
    definitions = asyncio.StreamReader(limit=1024)
    value = {
        "valid": version(),
        "oversized": b"a" * 1025 + b"\x00",
        "truncated": version()[:-1],
        "malformed": b"invalid\x00",
    }[response]
    definitions.feed_data(value)
    definitions.feed_eof()
    writers = [AsyncMock(), AsyncMock()]
    for writer in writers:
        writer.write = Mock()
        writer.close = Mock()
    connect = AsyncMock(side_effect=[(ping, writers[0]), (definitions, writers[1])])
    monkeypatch.setattr(asyncio, "open_connection", connect)
    if response == "valid":
        assert (await probe.probe_scanner()).definitions == "12345"
    else:
        with pytest.raises(PhotoUnavailableError, match="^scanner readiness unavailable$"):
            await probe.probe_scanner()
    assert connect.await_args_list == [call("127.0.0.1", 3310, limit=1024)] * 2
    for writer in writers:
        writer.close.assert_called_once()
        writer.wait_closed.assert_awaited_once()
    writers[0].write.assert_called_once_with(b"zPING\x00")
    writers[1].write.assert_called_once_with(b"zVERSION\x00")
