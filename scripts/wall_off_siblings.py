#!/usr/bin/env python3
"""Refuse the agent's file tools on sibling projects and their Claude memory (owner-run).

The shell sandbox already blocks the whole home folder. The agent's own Read/Edit/Write tools
are not shell commands: outside the project a write asks and a read asks, and a reflex click
lets one through. This writes explicit DENY rules for every sibling project folder and every
other project's Claude memory. A deny cannot carve an exception out of a parent, so each is
listed by name (adapted from zynth-auth's make-sandbox-settings.sh).

The list is machine-specific, so it goes in the gitignored `.claude/settings.local.json`,
which `scripts/check_agent_local_settings.py` allows to add deny rules and nothing else.

    python3 scripts/wall_off_siblings.py            # print the rules, change nothing
    python3 scripts/wall_off_siblings.py --apply    # back up, then merge them in

Run it in YOUR terminal: the agent is denied from writing its settings, by design. Re-run it
after adding a new project next to this one. Existing deny rules are kept.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
ROOT = Path(__file__).resolve().parents[1]


def memory_dir_name(project: Path) -> str:
    """Claude Code's folder name for a project's memory: `/`, space and `.` become `-`."""
    return re.sub(r"[/ .]", "-", str(project))


def rules_for(project: Path, home: Path) -> list[str]:
    """Deny rules for every sibling of `project` and every other project's Claude memory."""
    rules: list[str] = []
    for sibling in sorted(project.parent.iterdir()):
        if sibling.is_dir() and not sibling.name.startswith(".") and sibling != project:
            target = f"/{sibling}/**"  # `//abs` means the machine's root; `/rel` the project's
            rules += [f"{tool}({target})" for tool in ("Read", *WRITE_TOOLS)]
    memories = home / ".claude" / "projects"
    own = memory_dir_name(project)
    if memories.is_dir():
        for memory in sorted(memories.iterdir()):
            if memory.is_dir() and memory.name != own:
                target = f"~/.claude/projects/{memory.name}/**"
                rules += [f"{tool}({target})" for tool in ("Read", *WRITE_TOOLS)]
    return rules


def merge(settings_path: Path, rules: list[str]) -> tuple[int, Path | None]:
    """Add `rules` to the file's permissions.deny. Returns (rules added, backup made)."""
    document = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    if not isinstance(document, dict):
        raise ValueError(f"{settings_path} is not a JSON object; nothing was changed")
    deny = document.setdefault("permissions", {}).setdefault("deny", [])
    new = [rule for rule in rules if rule not in deny]
    if not new:
        return 0, None
    backup = None
    if settings_path.exists():
        backup = settings_path.with_name(settings_path.name + ".bak-pre-siblings")
        shutil.copy2(settings_path, backup)
    deny.extend(new)
    settings_path.write_text(json.dumps(document, indent=2) + "\n")
    return len(new), backup


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="merge into settings.local.json")
    parser.add_argument("--project", type=Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    project = args.project.resolve()
    rules = rules_for(project, args.home)
    targets = len(rules) // (1 + len(WRITE_TOOLS))
    print(f"wall-off: {targets} folder(s) to refuse ({len(rules)} rules), from {project.parent}")
    if not args.apply:
        print("\n".join(rules))
        print("Nothing changed. Re-run with --apply to merge these into settings.local.json.")
        return 0
    settings_path = project / ".claude" / "settings.local.json"
    added, backup = merge(settings_path, rules)
    print(f"wall-off: added {added} rule(s) to {settings_path}")
    if backup:
        print(f"wall-off: backup at {backup}")
    print("Restart Claude Code for the new rules to load.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
