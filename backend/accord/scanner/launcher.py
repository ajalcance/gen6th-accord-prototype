"""Fixed exec vectors, explicit environment and ownership across cancelled process acquisition."""

import asyncio
from dataclasses import dataclass
from typing import Literal

from accord.scanner.processes import KILL_SECONDS, TERM_SECONDS

Command = Literal["main", "daily", "bytecode", "bootstrap", "load", "clamd", "freshclam"]
COMMANDS: dict[Command, tuple[str, ...]] = {
    "main": ("/usr/bin/sigtool", "--info=/var/lib/accord-scanner/main.cvd"),
    "daily": ("/usr/bin/sigtool", "--info=/var/lib/accord-scanner/daily.cvd"),
    "bytecode": ("/usr/bin/sigtool", "--info=/var/lib/accord-scanner/bytecode.cvd"),
    "bootstrap": ("/usr/bin/freshclam", "--config-file=/etc/accord-scanner/bootstrap.conf"),
    "load": ("/usr/bin/clamscan", "--database=/var/lib/accord-scanner", "--no-summary", "-"),
    "clamd": ("/usr/sbin/clamd", "--config-file=/etc/accord-scanner/clamd.conf"),
    "freshclam": (
        "/usr/bin/freshclam",
        "--config-file=/etc/accord-scanner/freshclam.conf",
        "--daemon",
        "--foreground",
    ),
}
ENVIRONMENT = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "HOME": "/var/lib/accord-scanner",
    "TMPDIR": "/var/lib/accord-scanner-tmp",
}
ACQUIRE_SECONDS = 1


class NativeHandle:
    def __init__(self, process: asyncio.subprocess.Process) -> None:
        self.process = process

    @property
    def returncode(self) -> int | None:
        return self.process.returncode

    def terminate(self) -> None:
        self.process.terminate()

    def kill(self) -> None:
        self.process.kill()

    async def wait(self) -> int:
        return await self.process.wait()

    async def close(self) -> None:
        failed = False
        if self.returncode is None:
            try:
                self.terminate()
            except ProcessLookupError:
                pass
            except Exception:
                failed = True
        try:
            await asyncio.wait_for(self.wait(), TERM_SECONDS)
        except Exception as error:
            failed = failed or not isinstance(error, TimeoutError)
            try:
                self.kill()
            except ProcessLookupError:
                pass
            except Exception:
                failed = True
            await asyncio.wait_for(self.wait(), KILL_SECONDS)
        if failed or self.returncode is None:
            raise RuntimeError("scanner helper unreaped")


class NativeChild(NativeHandle):
    def __init__(
        self, process: asyncio.subprocess.Process, name: Literal["clamd", "freshclam"]
    ) -> None:
        super().__init__(process)
        self.name = name


@dataclass
class Acquisition:
    abandoned: bool = False


class Launcher:
    def __init__(self) -> None:
        self.handles: list[NativeHandle] = []
        self.pending: set[asyncio.Task[NativeHandle]] = set()
        self.failed = False

    async def acquire(self, command: Command, attempt: Acquisition) -> NativeHandle:
        process = await asyncio.create_subprocess_exec(
            *COMMANDS[command],
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            cwd="/var/lib/accord-scanner",
            env=ENVIRONMENT.copy(),
        )
        handle = (
            NativeChild(process, command)
            if command in ("clamd", "freshclam")
            else NativeHandle(process)
        )
        self.handles.append(handle)  # No yield between acquisition and registration.
        if attempt.abandoned:
            await handle.close()
        return handle

    def completed(self, task: asyncio.Task[NativeHandle]) -> None:
        self.pending.discard(task)
        try:
            task.result()
        except (Exception, asyncio.CancelledError):
            self.failed = True

    async def spawn(self, command: Command) -> NativeHandle:
        if self.failed or self.pending:
            raise RuntimeError("scanner launcher unavailable")
        attempt = Acquisition()
        task = asyncio.create_task(self.acquire(command, attempt))
        self.pending.add(task)
        task.add_done_callback(self.completed)
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            attempt.abandoned = True
            self.failed = True
            done, _ = await asyncio.wait({task}, timeout=ACQUIRE_SECONDS)
            if done and not task.cancelled() and task.exception() is None:
                await protected_close(task.result())
            raise


async def protected_close(handle: NativeHandle) -> None:
    task = asyncio.create_task(handle.close())
    try:
        await asyncio.shield(task)
    except asyncio.CancelledError:
        await asyncio.shield(task)
        raise
