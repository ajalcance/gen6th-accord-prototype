"""The machine-wide managed settings may only restrict, and must close every self-edit path.

`docs/runbooks/managed-settings.json` is what the owner installs, with sudo, at
`/Library/Application Support/ClaudeCode/managed-settings.json`. Nothing in any project can
override that file, and it applies to EVERY Claude Code project on the Mac. So it must never
allow, ask or change the sandbox — only deny — and what it denies is the one gap no project
setting can close for itself: an agent rewriting the settings that confine it (zynth-auth).
"""

from __future__ import annotations

import json

from conftest import REPO_ROOT

MANAGED = REPO_ROOT / "docs" / "runbooks" / "managed-settings.json"
WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
TARGETS = (
    "./.claude/settings.json",
    "./.claude/settings.local.json",
    "~/.claude/settings.json",
    "//Library/Application Support/ClaudeCode/**",
)


def _managed() -> dict:
    return json.loads(MANAGED.read_text())


def test_it_only_denies():
    """A machine-wide allow or ask would widen every project on the Mac at once."""
    document = _managed()
    assert set(document) <= {"$schema", "permissions"}, f"unexpected keys: {set(document)}"
    assert set(document["permissions"]) == {"deny"}, "managed settings may only deny"


def test_every_settings_file_is_closed_to_every_write_tool():
    deny = _managed()["permissions"]["deny"]
    missing = [f"{t}({p})" for p in TARGETS for t in WRITE_TOOLS if f"{t}({p})" not in deny]
    assert not missing, f"an agent can rewrite its own confinement through: {missing}"
