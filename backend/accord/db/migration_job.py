"""Operator-only fixed migration operation with bounded private proxy lifecycle."""

import argparse
import asyncio
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal, Never

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from accord.config import DatabaseTransport, Settings, get_settings
from accord.db.runtime import validated_database_url

STARTUP_SECONDS = 60
SHUTDOWN_SECONDS = 3
TARGETS = (
    "0009identity",
    "0010portraits",
    "0011captures",
    "0012faces",
    "0013investigation",
    "0014production",
    "0015jobs",
    "0016passports",
    "0017credits",
    "0018lifecycle",
)


class Phase(StrEnum):
    CONFIGURATION = "configuration"
    STARTUP = "startup"
    MIGRATION = "migration"


@dataclass(frozen=True)
class JobResult:
    failure: Phase | None
    shutdown_failed: bool

    @property
    def succeeded(self) -> bool:
        return self.failure is None and not self.shutdown_failed


async def proxy_request(operation: Literal["startup", "shutdown"]) -> int:
    """Fixed loopback HTTP only; bounded status line, no redirects or proxy discovery."""
    if operation not in ("startup", "shutdown"):
        raise ValueError("invalid proxy operation")
    port, method, path = (
        (9090, "GET", "/startup") if operation == "startup" else (9091, "POST", "/quitquitquit")
    )
    writer: asyncio.StreamWriter | None = None
    try:
        async with asyncio.timeout(1):
            reader, writer = await asyncio.open_connection("127.0.0.1", port, limit=256)
            writer.write(
                f"{method} {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n"
                "Content-Length: 0\r\nConnection: close\r\n\r\n".encode("ascii")
            )
            await writer.drain()
            line = await reader.readline()
            fields = line.split(b" ", 2)
            if (
                not line.endswith(b"\r\n")
                or len(fields) != 3
                or fields[0] not in (b"HTTP/1.0", b"HTTP/1.1")
            ):
                raise ValueError("invalid proxy status line")
            if len(fields[1]) != 3 or not fields[1].isdigit():
                raise ValueError("invalid proxy status code")
            return int(fields[1])
    finally:
        if writer is not None:
            writer.close()
            task = asyncio.current_task()
            if task is None or not task.cancelling():
                async with asyncio.timeout(1):
                    await writer.wait_closed()


async def wait_for_proxy() -> None:
    """Require startup HTTP 200 within an overall deadline; never follow redirects."""
    async with asyncio.timeout(STARTUP_SECONDS):
        while True:
            try:
                status = await proxy_request("startup")
            except (OSError, TimeoutError, ValueError):
                status = 503
            if status == 200:
                return
            await asyncio.sleep(1)


async def stop_proxy() -> None:
    """A successful request is shutdown acknowledgment, not proof of container exit."""
    async with asyncio.timeout(SHUTDOWN_SECONDS):
        if await proxy_request("shutdown") != 200:
            raise RuntimeError("proxy shutdown not acknowledged")


def migration_config(settings: Settings, target: str) -> Config:
    """Use only reviewed targets, private transport and the separate operator login."""
    if (
        target not in TARGETS
        or settings.database_transport is not DatabaseTransport.CLOUD_SQL_PROXY
    ):
        raise ValueError("reviewed migration configuration required")
    url = validated_database_url(settings)
    address = make_url(url)
    if address.username != "accord_migrator" or address.database != "appdb":
        raise ValueError("reviewed migration operator required")
    config = Config()
    config.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[2] / "migrations")
    )
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def run_job(target: str) -> JobResult:
    """Preserve primary failure category and attempt shutdown for every outcome."""
    phase = Phase.CONFIGURATION
    failure: Phase | None = None
    shutdown_failed = False
    try:
        config = migration_config(get_settings(), target)
        phase = Phase.STARTUP
        asyncio.run(wait_for_proxy())
        phase = Phase.MIGRATION
        command.upgrade(config, target)
    except Exception:
        failure = phase
    finally:
        try:
            asyncio.run(stop_proxy())
        except Exception:
            shutdown_failed = True
    return JobResult(failure, shutdown_failed)


class JobArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise ValueError("invalid migration arguments")


def main() -> None:
    """Print fixed categories only: database/provider exceptions may contain credentials."""
    parser = JobArgumentParser(description="Reviewed operator migration job")
    parser.add_argument("--target", required=True, choices=TARGETS)
    try:
        target = parser.parse_args().target
    except ValueError:
        target = ""
    result = run_job(target)
    print(f"migration_job={ 'passed' if result.succeeded else 'failed' }")
    print(f"failure_phase={result.failure or 'none'} shutdown_failed={result.shutdown_failed}")
    raise SystemExit(0 if result.succeeded else 1)


if __name__ == "__main__":
    main()
