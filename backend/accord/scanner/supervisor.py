"""Monotonic freshness/child health around a required internal managed runtime."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Literal

from accord.personas.photo_scanner import ScanReceipt
from accord.personas.scanner_probe import probe_scanner
from accord.scanner.processes import ManagedRuntime, children_live, shutdown_children

STARTUP_SECONDS = 120
POLL_SECONDS = 2
PROBE_SECONDS = 5
SUCCESS_AGE_SECONDS = 10
STOP_SECONDS = 7
Health = Literal["starting", "ready", "unavailable", "stalled", "failed", "stopping"]


class ScannerSupervisor:
    def __init__(
        self,
        runtime: ManagedRuntime,
        probe: Callable[[], Awaitable[ScanReceipt]] = probe_scanner,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if runtime.children:
            raise ValueError("scanner runtime already started")
        self.runtime, self.probe, self.clock = runtime, probe, clock
        self.last_success: float | None = None
        self.unavailable, self.failed, self.stopping = False, False, False
        self.task: asyncio.Task[None] | None = None

    def health(self) -> Health:
        if self.stopping:
            return "stopping"
        if self.failed or (self.task is not None and self.task.done()):
            return "failed"
        if self.last_success is None:
            return "starting"
        if not children_live(self.runtime.children):
            return "failed"
        if self.unavailable:
            return "unavailable"
        if self.clock() - self.last_success > SUCCESS_AGE_SECONDS:
            return "stalled"
        return "ready"

    def start(self) -> None:
        if self.task is not None or self.stopping:
            raise RuntimeError("scanner supervisor cannot restart")
        self.task = asyncio.create_task(self.run())

    async def check(self) -> bool:
        if not children_live(self.runtime.children):
            raise RuntimeError("scanner children unavailable")
        try:
            async with asyncio.timeout(PROBE_SECONDS) as deadline:
                await self.probe()
            if deadline.expired():
                raise TimeoutError
        except Exception:
            self.unavailable = True
            return False
        if self.stopping or not children_live(self.runtime.children):
            raise RuntimeError("scanner stopped during probe")
        self.last_success, self.unavailable = self.clock(), False
        return True

    async def initialize(self) -> None:
        async with asyncio.timeout(STARTUP_SECONDS) as deadline:
            await self.runtime.prepare()
            await self.runtime.start()
            while not await self.check():
                await asyncio.sleep(POLL_SECONDS)
        if deadline.expired():
            raise TimeoutError("scanner startup deadline exceeded")

    async def run(self) -> None:
        try:
            await self.initialize()
            while not self.stopping:
                await asyncio.sleep(POLL_SECONDS)
                await self.check()
        except asyncio.CancelledError:
            raise
        except Exception:
            self.failed = True
        finally:
            try:
                await self.cleanup()
            except Exception:
                self.failed = True
                raise RuntimeError("scanner supervision cleanup unavailable") from None

    async def cleanup(self) -> None:
        cleanup = asyncio.create_task(shutdown_children(self.runtime.children))
        try:
            await asyncio.shield(cleanup)
        except asyncio.CancelledError:
            await asyncio.shield(cleanup)
            raise

    async def stop(self) -> None:
        already_stopping = self.stopping
        self.stopping = True
        if self.task is None:
            return
        if not already_stopping:
            self.task.cancel()
        done, _ = await asyncio.wait({self.task}, timeout=STOP_SECONDS)
        if not done:
            raise RuntimeError("scanner supervision stop deadline exceeded")
        try:
            self.task.result()
        except asyncio.CancelledError:
            pass
        except Exception:
            raise RuntimeError("scanner supervision stop unavailable") from None
