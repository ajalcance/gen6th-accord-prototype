"""Shared helpers for the guard fault tests.

These tests execute the **real scripts that ship in `scripts/`** — never a reimplementation of
their logic. A test of a copy proves nothing about the guard that actually gates CI.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"


def run(
    cmd: list[str], cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    # `env` is merged over the real environment, never replacing it: a guard that shells out to
    # git or python must keep finding them. Used to put a stub tool earlier on PATH.
    merged = {**os.environ, **env} if env else None
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, check=False, timeout=120, env=merged
    )


def run_guard(
    script: Path, *args: str, cwd: Path | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a guard script and return the completed process (never raises on failure)."""
    return run([sys.executable, str(script), *args], cwd or script.resolve().parents[1], env)


def load_module(path: Path) -> ModuleType:
    """Import a guard or hook as a module, to read its REAL constants rather than restating them.

    The one way the guard tests read another file's constants. Tests used to `exec()` a slice
    of the source text under a `# noqa`; the scan that first covered tests/guards/ (ADR-0018)
    flagged both. Importing runs the file's top level only; guards and hooks act solely under
    `if __name__ == "__main__"`.
    """
    spec = importlib.util.spec_from_file_location(f"guard_{path.stem}", path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def remove_flat_dir(path: Path) -> None:
    """Delete a sandbox directory that holds only files — never recursively.

    Replaces `shutil.rmtree` in the fault tests (Semgrep sec-python-destructive-fs, found once
    tests/guards/ was scanned — ADR-0018). Narrower by construction: it removes plain files one
    at a time, then the now-empty directory, and FAILS on a subdirectory instead of descending.
    """
    for entry in path.iterdir():
        assert not entry.is_dir(), f"{entry} is a directory; remove_flat_dir never recurses"
        entry.unlink()
    path.rmdir()


def install_guard(sandbox: Path, name: str) -> Path:
    """Copy a real guard into a sandbox repo so its ROOT resolves to that sandbox.

    Guards compute ``ROOT = Path(__file__).resolve().parents[1]``, so placing the script at
    ``<sandbox>/scripts/<name>`` makes it scan the sandbox instead of this repository.
    """
    scripts = sandbox / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    dest = scripts / name
    shutil.copy2(SCRIPTS / name, dest)
    return dest


def set_register(guard: Path, entries: tuple[tuple[str, str], ...]) -> None:
    """Replace the BLOCKERS register in an installed prod_readiness.py, whatever it holds.

    The fixtures used to `str.replace` the literal EMPTY register. `str.replace` fails
    silently: the moment the real register held an entry, nothing was replaced, every fixture
    inherited the real register, and six guard tests failed for a reason none of them named.
    This splices by syntax instead and refuses when the register cannot be found exactly once.
    """
    source = guard.read_text()
    found = [
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.AnnAssign | ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "BLOCKERS"
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        )
    ]
    assert len(found) == 1, f"{guard} defines BLOCKERS {len(found)} times, not once"
    node = found[0]
    assert node.end_lineno is not None
    lines = source.splitlines(keepends=True)
    rendered = f"BLOCKERS: tuple[tuple[str, str], ...] = {entries!r}\n"
    lines[node.lineno - 1 : node.end_lineno] = [rendered]
    guard.write_text("".join(lines))


def app_package() -> str:
    """The backend package name baked into dod-check.py when the project was generated."""
    match = re.search(r'^APP_PKG = "([^"]+)"', (SCRIPTS / "dod-check.py").read_text(), re.M)
    assert match, "APP_PKG constant not found in scripts/dod-check.py"
    return match.group(1)


def git_init(path: Path) -> None:
    """Initialise a hermetic git repo — no user config, no signing, no hooks."""
    run(["git", "init", "-q", "-b", "main"], path)
    run(["git", "config", "user.email", "guard-tests@example.com"], path)
    run(["git", "config", "user.name", "Guard Tests"], path)
    run(["git", "config", "commit.gpgsign", "false"], path)


def git_commit(path: Path, message: str) -> None:
    run(["git", "add", "-A"], path)
    run(["git", "commit", "-q", "--no-verify", "-m", message], path)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
