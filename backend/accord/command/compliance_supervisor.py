"""Bounded pass supervision; progress is not proof of complete Redis/audit delivery."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Literal

from accord.logger import logger

PASS_SECONDS = 30
CANCEL_SECONDS = 4
Health = Literal["starting", "progressing", "failed", "stalled", "stopping"]


class ComplianceSupervisor:
    def __init__(
        self,
        run_pass: Callable[[], Awaitable[tuple[int, int, int]]],
        poll_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.run_pass, self.poll_seconds, self.clock = run_pass, poll_seconds, clock
        self.last_success: float | None = None
        self.failed = False
        self.stopping = False
        self.task: asyncio.Task[None] | None = None

    def health(self) -> Health:
        if self.stopping:
            return "stopping"
        if self.failed or (self.task is not None and self.task.done()):
            return "failed"
        if self.last_success is None:
            return "starting"
        if self.clock() - self.last_success > PASS_SECONDS + self.poll_seconds + 5:
            return "stalled"
        return "progressing"

    async def cycle(self) -> None:
        """Only a completed, uncancelled pass refreshes progress."""
        try:
            async with asyncio.timeout(PASS_SECONDS) as deadline:
                await self.run_pass()
            if deadline.expired():
                raise TimeoutError("compliance pass deadline exceeded")
            if self.stopping:
                raise asyncio.CancelledError
        except (Exception, asyncio.CancelledError):
            self.failed = True
            raise
        self.last_success, self.failed = self.clock(), False

    def start(self) -> None:
        if self.task is not None or self.stopping:
            raise RuntimeError("compliance supervisor cannot restart")
        self.task = asyncio.create_task(self.run())

    async def run(self) -> None:
        while not self.stopping:
            await asyncio.sleep(self.poll_seconds)
            if self.stopping:
                return
            try:
                await self.cycle()
            except Exception:
                logger.error("compliance pass unavailable")

    async def stop(self) -> None:
        self.stopping = True
        if self.task is None:
            return
        self.task.cancel()
        done, _ = await asyncio.wait({self.task}, timeout=CANCEL_SECONDS)
        if not done:
            raise RuntimeError("compliance cancellation deadline exceeded")
        try:
            self.task.result()
        except asyncio.CancelledError:
            pass
        except Exception:
            raise RuntimeError("compliance supervisor unavailable") from None
