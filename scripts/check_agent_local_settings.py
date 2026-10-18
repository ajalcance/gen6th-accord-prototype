#!/usr/bin/env python3
"""The agent's local settings may only restrict it, never widen it.

`.claude/settings.local.json` is gitignored and outranks the committed policy
(`.claude/settings.json`) in Claude Code's precedence. Every "Yes, and don't ask again" writes
a literal rule into it, so it drifts by clicks rather than by review. On 2026-09-25 a click
stored `Bash(ls /Users/<owner>/Documents)` there, a standing read of the folder above this
project, minutes after the project-only policy was written. Nobody reviews a gitignored file.
This does.

The rule is an allow-list of KEYS, not a deny-list of dangerous ones: a local file may add
`permissions.deny` / `permissions.ask` rules and sandbox read/write/domain denials, and
nothing else. Every other key with a non-empty value — an allow rule, an extra directory, a
permission mode, an env var, a hook, a sandbox exception — is a widening and fails. An unknown
key fails too, so a setting Claude Code adds tomorrow is reviewed before it is trusted.

The fix is never to relax this check: move a genuinely needed rule into the committed policy,
where it is reviewed, and delete it from the local file.

A missing file is not a failure and not an empty scan: CI never has one, by design, and a
fresh clone has none until its owner creates it. That case is reported by name.

Usage:  python3 scripts/check_agent_local_settings.py [path]
Exit 0 when the file restricts only (or is absent), 1 when it widens or cannot be read.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / ".claude" / "settings.local.json"

# The only keys a local file may give a non-empty value. Each one can only take capability
# away. Everything else is a widening.
RESTRICTIVE = {
    ("permissions", "deny"),
    ("permissions", "ask"),
    ("sandbox", "filesystem", "denyRead"),
    ("sandbox", "filesystem", "denyWrite"),
    ("sandbox", "network", "deniedDomains"),
}
# Containers that hold the keys above. Present-and-empty is fine; what is inside is checked.
CONTAINERS = {("permissions",), ("sandbox",), ("sandbox", "filesystem"), ("sandbox", "network")}


def _leaves(node: object, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], object]]:
    """Every (key path, value) in the document, descending only into known containers."""
    if path in CONTAINERS or not path:
        if not isinstance(node, dict):
            return [(path, node)]
        out: list[tuple[tuple[str, ...], object]] = []
        for key, value in node.items():
            out.extend(_leaves(value, (*path, str(key))))
        return out
    return [(path, node)]


def widenings(document: object) -> tuple[list[str], int]:
    """(each widening, how many keys were inspected)."""
    if not isinstance(document, dict):
        return ["the document is not a JSON object"], 0
    leaves = [(path, value) for path, value in _leaves(document) if path != ("$schema",)]
    found = [
        f"{'.'.join(path)} = {json.dumps(value)}"
        for path, value in leaves
        if path not in RESTRICTIVE and value not in ([], {}, None, "")
    ]
    return found, len(leaves)


def main(argv: list[str]) -> int:
    target = Path(argv[1]) if len(argv) > 1 else DEFAULT
    if not target.is_file():
        print(
            f"agent-local-settings: {target.name} is absent — nothing to check (CI never has "
            f"one; a clone has none until its owner creates it)"
        )
        return 0
    try:
        document = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"agent-local-settings: FAIL — {target} cannot be read ({exc})", file=sys.stderr)
        return 1
    found, inspected = widenings(document)
    print(f"agent-local-settings: inspected {inspected} key(s) in {target.name}")
    if found:
        print(
            "agent-local-settings: FAIL — the local file widens the committed agent policy. "
            "Move a needed rule into .claude/settings.json (reviewed) and delete it here:",
            file=sys.stderr,
        )
        for item in found:
            print(f"  · {item}", file=sys.stderr)
        return 1
    print("agent-local-settings: OK — it only restricts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
