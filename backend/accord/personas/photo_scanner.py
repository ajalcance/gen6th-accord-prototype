"""Loopback clamd INSTREAM adapter. No shell scan, remote filename or unbounded response."""

import asyncio
import re
import struct
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from accord.personas.photo_contracts import PhotoRejectedError, PhotoUnavailableError
from accord.personas.photo_decoder import MAX_INPUT


@dataclass(frozen=True)
class ScanReceipt:
    engine: str
    definitions: str


class PhotoScanner(Protocol):
    async def scan(self, data: bytes) -> ScanReceipt: ...


def definition_receipt(value: bytes) -> ScanReceipt:
    try:
        text = value.decode("ascii").strip("\x00")
        engine, definitions, date = text.split("/", 2)
        if not re.fullmatch(r"ClamAV [0-9]+\.[0-9]+\.[0-9]+", engine):
            raise ValueError
        if not re.fullmatch(r"[0-9]{1,12}", definitions):
            raise ValueError
        updated = datetime.strptime(date.strip(), "%a %b %d %H:%M:%S %Y").replace(tzinfo=UTC)
        age = datetime.now(UTC) - updated
        if not -timedelta(minutes=5) <= age <= timedelta(hours=48):
            raise ValueError
        return ScanReceipt(engine, definitions)
    except (UnicodeError, ValueError) as exc:
        raise PhotoUnavailableError("scanner definitions unavailable") from exc


class ClamdScanner:
    def __init__(self, host: str = "127.0.0.1", port: int = 3310) -> None:
        if host not in {"127.0.0.1", "::1"} or not 1 <= port <= 65535:
            raise ValueError("scanner must use an explicit loopback endpoint")
        self.host, self.port = host, port
        self.workers = asyncio.Semaphore(2)

    async def command(self, command: bytes, data: bytes | None = None) -> bytes:
        reader, writer = await asyncio.open_connection(self.host, self.port, limit=1024)
        try:
            writer.write(command)
            await writer.drain()
            if data is not None:
                for offset in range(0, len(data), 65536):
                    chunk = data[offset : offset + 65536]
                    writer.write(struct.pack("!I", len(chunk)) + chunk)
                    await writer.drain()
                writer.write(struct.pack("!I", 0))
                await writer.drain()
            return await reader.readuntil(b"\x00")
        finally:
            writer.close()
            task = asyncio.current_task()
            if task is None or not task.cancelling():
                async with asyncio.timeout(1):
                    await writer.wait_closed()

    async def scan(self, data: bytes) -> ScanReceipt:
        if not 1 <= len(data) <= MAX_INPUT:
            raise PhotoRejectedError("invalid scan size")
        async with self.workers:
            try:
                async with asyncio.timeout(20):
                    before = definition_receipt(await self.command(b"zVERSION\x00"))
                    verdict = await self.command(b"zINSTREAM\x00", data)
                    after = definition_receipt(await self.command(b"zVERSION\x00"))
                    if before != after:
                        raise PhotoUnavailableError("scanner definitions changed")
                    if verdict == b"stream: OK\x00":
                        return before
                    if verdict.startswith(b"stream: ") and verdict.endswith(b" FOUND\x00"):
                        raise PhotoRejectedError("photo rejected by scanner")
                    raise PhotoUnavailableError("scanner returned no complete verdict")
            except PhotoRejectedError:
                raise
            except Exception as exc:
                raise PhotoUnavailableError("scanner unavailable") from exc
