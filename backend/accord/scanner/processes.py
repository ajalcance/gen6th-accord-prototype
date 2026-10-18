"""Typed child boundary and bounded termination; no executable/argv or shell input."""

import asyncio
from typing import Literal, Protocol

TERM_SECONDS = 3
KILL_SECONDS = 2


class Child(Protocol):
    name: Literal["clamd", "freshclam"]

    @property
    def returncode(self) -> int | None: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...

    async def wait(self) -> int: ...


class ManagedRuntime(Protocol):
    """Future reviewed packaging owns validation/launch, registering children before yielding."""

    @property
    def children(self) -> tuple[Child, ...]: ...

    async def prepare(self) -> None: ...

    async def start(self) -> None: ...


def children_live(children: tuple[Child, ...]) -> bool:
    return (
        len(children) == 2
        and {child.name for child in children} == {"clamd", "freshclam"}
        and all(child.returncode is None for child in children)
    )


def signal_children(children: tuple[Child, ...], *, kill: bool) -> bool:
    failed = False
    for child in children:
        if child.returncode is not None:
            continue
        try:
            child.kill() if kill else child.terminate()
        except ProcessLookupError:
            pass  # Still require wait/reaping below; a lookup race is not clean exit proof.
        except Exception:
            failed = True
    return failed


async def shutdown_children(children: tuple[Child, ...]) -> None:
    """Signal every child even after another fails; never acknowledge an unreaped child."""
    if not children:
        return
    failed = signal_children(children, kill=False)
    tasks = {asyncio.create_task(child.wait()) for child in children}
    try:
        _, pending = await asyncio.wait(tasks, timeout=TERM_SECONDS)
        failed = signal_children(children, kill=True) or failed
        if pending:
            _, pending = await asyncio.wait(pending, timeout=KILL_SECONDS)
        if pending or any(child.returncode is None for child in children):
            failed = True
        for task in tasks - pending:
            try:
                task.result()
            except (Exception, asyncio.CancelledError):
                failed = True
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
    if failed:
        raise RuntimeError("scanner child cleanup unavailable") from None
