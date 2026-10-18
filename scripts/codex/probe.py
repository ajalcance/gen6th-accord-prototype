"""Harmless live probe for the proposed Codex permission profile.

The owner creates ~/accord-codex-sandbox-canary before launching this script
through `codex sandbox`. The canary contains no secret and is never printed.
"""

from __future__ import annotations

import pathlib
import socket
import sys
from collections.abc import Callable

PROJECT = pathlib.Path(__file__).resolve().parents[2]
CANARY = pathlib.Path.home() / "accord-codex-sandbox-canary"


def denied(operation: Callable[[], object]) -> bool:
    """Return true only when the kernel refuses the operation."""
    try:
        operation()
    except PermissionError:
        return True
    except OSError as exc:
        return exc.errno in {1, 13, 30}
    return False


def read_canary() -> None:
    """Open the harmless owner canary without returning its contents."""
    with CANARY.open("rb"):
        pass


def try_write(path: pathlib.Path) -> None:
    """Try a new probe file and remove it if the boundary unexpectedly permits it."""
    created = False
    try:
        with path.open("x"):
            created = True
    finally:
        if created:
            path.unlink()


def network_connect() -> None:
    """Attempt one connection to prove command network is closed."""
    with socket.create_connection(("1.1.1.1", 443), timeout=2):
        pass


def main() -> int:
    """Run positive and negative controls, returning failure on any mismatch."""
    checks: list[tuple[str, bool]] = []
    checks.append(("project instructions readable", (PROJECT / "CLAUDE.md").is_file()))
    checks.append(("git metadata readable", (PROJECT / ".git/HEAD").is_file()))
    allowed_path = PROJECT / "codex-sandbox-allowed-probe"
    try:
        try_write(allowed_path)
        project_write = True
    except OSError:
        project_write = False
    checks.append(("project scratch writable", project_write))
    checks.append(("home canary read denied", denied(read_canary)))
    checks.append(
        ("Claude policy write denied", denied(lambda: try_write(PROJECT / ".claude/codex-probe")))
    )
    checks.append(
        ("git hook write denied", denied(lambda: try_write(PROJECT / ".git/hooks/codex-probe")))
    )
    checks.append(
        (
            "outside project write denied",
            denied(lambda: try_write(pathlib.Path.home() / "codex-write-probe")),
        )
    )
    checks.append(("command network denied", denied(network_connect)))
    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
