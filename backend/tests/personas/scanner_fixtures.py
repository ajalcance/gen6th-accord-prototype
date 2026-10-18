"""Synthetic children/runtime: never starts a process or contacts a scanner."""

import asyncio
from typing import Literal

from accord.scanner.processes import Child


class SyntheticChild:
    def __init__(self, name: Literal["clamd", "freshclam"], resist_term: bool = False) -> None:
        self.name = name
        self.returncode: int | None = None
        self.exited = asyncio.Event()
        self.signals: list[str] = []
        self.resist_term = resist_term

    def terminate(self) -> None:
        self.signals.append("TERM")
        if not self.resist_term:
            self.exit(0)

    def kill(self) -> None:
        self.signals.append("KILL")
        self.exit(-9)

    def exit(self, code: int) -> None:
        self.returncode = code
        self.exited.set()

    async def wait(self) -> int:
        await self.exited.wait()
        assert self.returncode is not None
        return self.returncode


class SyntheticRuntime:
    def __init__(self) -> None:
        self.daemon, self.updater = SyntheticChild("clamd"), SyntheticChild("freshclam")
        self.children: tuple[Child, ...] = ()
        self.prepared = False
        self.entered = asyncio.Event()
        self.prepare_gate: asyncio.Event | None = None
        self.partial_gate: asyncio.Event | None = None
        self.prepare_failure = False

    async def prepare(self) -> None:
        self.entered.set()
        if self.prepare_gate is not None:
            await self.prepare_gate.wait()
        if self.prepare_failure:
            raise RuntimeError("synthetic private configuration failure")
        self.prepared = True

    async def start(self) -> None:
        assert self.prepared
        self.children = (self.daemon,)
        if self.partial_gate is not None:
            self.entered.set()
            await self.partial_gate.wait()
        self.children = (self.daemon, self.updater)
