"""Owner-installed Codex pre-tool check for this repository.

The OS permission profile is the boundary. This hook gives early, legible
refusals for commands that the owner runs. It must not be treated as a way to
grant access outside the profile.
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from typing import Any

DENY_PROGRAMS = {
    "bash",
    "brew",
    "codex",
    "curl",
    "docker",
    "env",
    "gcloud",
    "gh",
    "npx",
    "rm",
    "rsync",
    "scp",
    "sftp",
    "sh",
    "ssh",
    "sudo",
    "terraform",
    "wget",
    "zsh",
}
DENY_GIT = {
    "checkout",
    "clean",
    "commit",
    "config",
    "fetch",
    "merge",
    "pull",
    "push",
    "rebase",
    "reset",
    "stash",
    "switch",
    "tag",
    "update-ref",
    "worktree",
}
DENY_NPM = {
    "add",
    "exec",
    "i",
    "in",
    "ins",
    "inst",
    "insta",
    "instal",
    "install",
    "publish",
    "uninstall",
    "update",
    "upgrade",
}
DENY_UV = {"add", "pip", "run", "tool"}


def deny(reason: str) -> dict[str, Any]:
    """Return the supported fail-closed PreToolUse denial shape."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def git_verb(args: list[str]) -> str | None:
    """Find git's verb after the common options that precede it."""
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in {"-C", "--git-dir", "--work-tree", "-c"}:
            index += 2
            continue
        if arg.startswith(("--git-dir=", "--work-tree=", "-c")):
            index += 1
            continue
        if arg.startswith("-"):
            index += 1
            continue
        return arg
    return None


def command_denial(command: str) -> str | None:
    """Check one plain shell command; unusual shell syntax is owner-run."""
    if "\n" in command or "\r" in command:
        return "Use one plain command per call; multiline shell input is owner-run."
    if "`" in command or "$(" in command or "${" in command:
        return "Shell expansion is owner-run in this repository."
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
    lexer.whitespace_split = True
    tokens = list(lexer)
    if not tokens:
        return "Empty shell command is refused."
    if any(token and all(char in ";&|<>" for char in token) for token in tokens):
        return "Use one plain command per call; shell composition is owner-run."
    program = os.path.basename(tokens[0]).lower()
    if program in DENY_PROGRAMS:
        return f"{program} is owner-run for this repository."
    args = tokens[1:]
    if program == "git" and git_verb(args) in DENY_GIT:
        return "Git history, refs, and remote changes are owner-run."
    if program == "npm" and args and args[0] in DENY_NPM:
        return "Package installation and publishing are owner-run."
    if program in {"pip", "pip3"} and "install" in args:
        return "Package installation is owner-run."
    if (
        program.startswith("python")
        and args[:2] in (["-m", "pip"], ["-m", "pip3"])
        and "install" in args
    ):
        return "Package installation is owner-run."
    if program == "uv" and args and args[0] in DENY_UV:
        return "Dependency changes and fetched execution are owner-run."
    if (
        program in {"yarn", "pnpm", "bun"}
        and args
        and args[0] in {"add", "install", "remove", "update", "upgrade", "publish", "exec", "dlx"}
    ):
        return "Package installation and publishing are owner-run."
    if program == "go" and args and args[0] in {"get", "install"}:
        return "Package installation is owner-run."
    if program == "cargo" and args and args[0] in {"add", "install", "publish"}:
        return "Package installation and publishing are owner-run."
    return None


def decision(payload: Any) -> dict[str, Any] | None:
    """Evaluate Codex's hook JSON without trusting its claimed command fields."""
    if not isinstance(payload, dict) or payload.get("hook_event_name") != "PreToolUse":
        return deny("Malformed Codex pre-tool event is refused.")
    if payload.get("tool_name") != "Bash":
        return deny("Unexpected tool reached the Bash-only managed hook.")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict) or not isinstance(tool_input.get("command"), str):
        return deny("Malformed shell command is refused.")
    try:
        reason = command_denial(tool_input["command"])
    except (ValueError, OSError):
        return deny("Unparseable shell command is refused.")
    return deny(reason) if reason else None


def main() -> int:
    """Read one event and print a denial only when one is required."""
    try:
        payload = json.load(sys.stdin)
        result = decision(payload)
    except (ValueError, OSError):
        result = deny("Codex hook input could not be read.")
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
