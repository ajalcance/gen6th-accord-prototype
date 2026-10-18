"""Real-file, real-executable managed runtime; no fixture seed, fallback or implicit app."""

import asyncio
import os
import platform
import pwd
import sys

from accord.scanner import filesystem, policy
from accord.scanner.launcher import Command, Launcher, NativeChild, protected_close
from accord.scanner.processes import Child

HELPER_SECONDS = 30
FILE_SECONDS = 15


class ScannerRuntime:
    def __init__(self) -> None:
        if (
            sys.platform != "linux"
            or platform.machine() != "x86_64"
            or os.geteuid() != policy.UID
            or pwd.getpwnam("clamav").pw_uid != policy.UID
        ):
            raise ValueError("scanner runtime platform unavailable")
        self.launcher: Launcher = Launcher()
        self.prepared: bool = False
        self.attempted: bool = False
        self.started: bool = False
        self.loaded: dict[str, str] | None = None

    @property
    def children(self) -> tuple[Child, ...]:
        return tuple(handle for handle in self.launcher.handles if isinstance(handle, NativeChild))

    async def helper(self, command: Command) -> None:
        handle = await self.launcher.spawn(command)
        try:
            async with asyncio.timeout(HELPER_SECONDS):
                result = await handle.wait()
            if result != 0:
                raise RuntimeError("scanner preparation command failed")
        finally:
            await protected_close(handle)

    async def files(self, *, seeds: bool) -> None:
        # Read-only work in a thread; a cancelled read cannot launch or modify a file.
        async with asyncio.timeout(FILE_SECONDS):
            await asyncio.to_thread(
                filesystem.validate_seeds if seeds else filesystem.configuration
            )

    async def snapshot(self) -> dict[str, str]:
        async with asyncio.timeout(FILE_SECONDS):
            return await asyncio.to_thread(filesystem.database_snapshot)

    async def prepare(self) -> None:
        if self.attempted or self.children:
            raise RuntimeError("scanner preparation cannot restart")
        self.attempted = True
        try:
            await self.files(seeds=True)
            for command in ("main", "daily", "bytecode"):
                await self.helper(command)
            await self.files(seeds=True)  # Bind the verified files before trusted updating.
            await self.helper("bootstrap")
            updated = await self.snapshot()
            await self.helper("load")  # EOF stdin; loads and compiles the actual database.
            await self.files(seeds=False)
            if await self.snapshot() != updated:
                raise ValueError("scanner database changed during load")
            self.loaded = updated
            self.prepared = True
        except Exception:
            raise RuntimeError("scanner preparation unavailable") from None

    async def start(self) -> None:
        if not self.prepared or self.started or self.launcher.failed or self.launcher.pending:
            raise RuntimeError("scanner runtime not prepared")
        self.started = True
        await self.files(seeds=False)
        if await self.snapshot() != self.loaded:
            raise RuntimeError("scanner loaded database changed")
        await self.launcher.spawn("clamd")
        await self.launcher.spawn("freshclam")
