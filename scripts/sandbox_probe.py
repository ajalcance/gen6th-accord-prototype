#!/usr/bin/env python3
"""Probe the agent's OS sandbox from a LAUNCHED program (ADR-0019, ADR-0020).

Permission rules and hooks see only the command the agent types. The sandbox must also hold
for every child and grandchild process: a test runner, a build script, a poisoned dependency.
This runs as such a program and checks each boundary from the inside.

    backend/.venv/bin/python scripts/sandbox_probe.py

Run it in a live agent session after any change to `.claude/settings.json`. Outside the
sandbox every "blocked" probe fails, which proves the probe can fail. It cannot run in CI
(Linux, no Seatbelt), so it is a diagnostic, not a gate; the runbook records each run.

Only OS and HTTP errors count as "blocked". Any other exception is a bug in this probe, and it
propagates: a probe that counts its own crash as a refusal would pass for the wrong reason.
Prints no secret.
"""

from __future__ import annotations

import base64
import os
import socket
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from urllib.parse import unquote, urlsplit

HOME = Path.home()
PROJECT = Path(__file__).resolve().parents[1]
BLOCKED = (OSError,)


def _write(path: Path) -> Callable[[], None]:
    """Create a NEW file and remove it. Never aim this at an existing file: if the boundary
    failed, it would overwrite and then delete it."""

    def act() -> None:
        if path.exists():
            raise RuntimeError(f"refusing to probe an existing file: {path}")
        path.write_text("probe\n")
        path.unlink()

    return act


def _open_for_append(path: Path) -> Callable[[], None]:
    """Open an existing file for writing without writing anything: its content is untouched."""

    def act() -> None:
        with open(path, "a"):
            pass

    return act


def _reach(host: str) -> Callable[[], None]:
    """Ask for a connection to <host>:443 the way any launched program's traffic goes.

    Inside the sandbox that is a CONNECT to its filtering proxy, and the proxy's answer is the
    decision being probed. No HTTP client and no URL: nothing here can become a `file://` read.
    Outside the sandbox there is no proxy, so the connection is direct and succeeds, and every
    "blocked" network probe fails, as it should.
    """

    def act() -> None:
        proxy = urlsplit(os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or "")
        if not proxy.hostname or not proxy.port:
            socket.create_connection((host, 443), timeout=10).close()
            return
        auth = ""
        if proxy.username:
            login = f"{unquote(proxy.username)}:{unquote(proxy.password or '')}"
            auth = f"Proxy-Authorization: Basic {base64.b64encode(login.encode()).decode()}\r\n"
        request = f"CONNECT {host}:443 HTTP/1.1\r\nHost: {host}:443\r\n{auth}\r\n"
        with socket.create_connection((proxy.hostname, proxy.port), timeout=10) as sock:
            sock.sendall(request.encode())
            status = sock.recv(256).decode(errors="replace").split("\r\n", 1)[0]
        if status.split(" ")[1:2] != ["200"]:
            raise ConnectionRefusedError(f"the sandbox proxy refused {host}: {status}")

    return act


def _grandchild_write() -> None:
    target = HOME / "accord-sandbox-probe-grandchild"
    code = f"open({str(target)!r}, 'w').write('x')"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, check=False)
    if result.returncode != 0:
        raise PermissionError(result.stderr.decode(errors="replace").strip()[-90:])
    target.unlink()


PROBES: list[tuple[str, bool, Callable[[], object]]] = [
    ("write a file in the home directory", True, _write(HOME / "accord-sandbox-probe.txt")),
    ("write the user's Claude settings", True, _write(HOME / ".claude" / "settings.probe")),
    ("write inside the project (.cache/)", False, _write(PROJECT / ".cache" / "probe.txt")),
    ("list ~/.ssh", True, lambda: list((HOME / ".ssh").iterdir())),
    ("read the personal gh login", True, lambda: (HOME / ".config/gh/hosts.yml").read_text()),
    (
        "read the agent's own token file",
        True,
        lambda: (HOME / ".config/gen6th-accord-agent-gh/hosts.yml").read_text(),
    ),
    ("list a sibling project folder", True, lambda: list((HOME / "Documents").iterdir())),
    # The agent's own authority: its approval scopes live in .claude/ (zynth-auth tamper paths).
    ("create a file in .claude/", True, _write(PROJECT / ".claude" / "sandbox-probe.tmp")),
    ("create a git hook", True, _write(PROJECT / ".git" / "hooks" / "sandbox-probe")),
    ("open .git/config for writing", True, _open_for_append(PROJECT / ".git" / "config")),
    ("a grandchild process writing to home", True, _grandchild_write),
    ("reach pypi.org:443 (allow-listed)", False, _reach("pypi.org")),
    ("reach example.com:443 (not allow-listed)", True, _reach("example.com")),
]


def main() -> int:
    for var in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN"):
        print(f"env   {var}: {'SET (unexpected)' if os.environ.get(var) else 'not set'}")
    print(f"env   GH_CONFIG_DIR: {os.environ.get('GH_CONFIG_DIR') or 'not set'}")
    failures = 0
    for name, want_blocked, action in PROBES:
        try:
            action()
            blocked, detail = False, "succeeded"
        except BLOCKED as exc:
            blocked, detail = True, f"{type(exc).__name__}: {str(exc)[:90]}"
        ok = blocked == want_blocked
        failures += not ok
        want = "blocked" if want_blocked else "allowed"
        print(f"{'PASS' if ok else 'FAIL'}  {name} (want {want}) -> {detail}")
    print(f"\nsandbox-probe: {len(PROBES) - failures}/{len(PROBES)} probes behaved as required")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
