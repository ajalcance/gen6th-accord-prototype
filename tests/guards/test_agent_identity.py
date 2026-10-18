"""The agent reaches GitHub as its own repo-only token, and never leaves the sandbox (ADR-0020).

`gh` and git's network commands cannot run inside the macOS sandbox, so they run outside it.
Before ADR-0020 they ran as the owner's personal login, which can reach every repository the
owner has. Now they read a fine-grained token scoped to this repository, and nothing else in
the policy can reach the personal one. These tests pin every part of that, and the hook that
stops a command from pointing `gh` back.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import PurePosixPath

import pytest
from conftest import REPO_ROOT

SETTINGS = REPO_ROOT / ".claude" / "settings.json"
HOOK = REPO_ROOT / ".claude" / "hooks" / "block_dangerous_bash.py"
AGENT_GH_DIR = ".config/gen6th-accord-agent-gh"
# The only commands that may run outside the sandbox: the GitHub CLI and git's network verbs,
# which fail TLS or cannot read their credential inside it. Anything else added here would run
# with the owner's full access. gcloud and terraform return only with an agent cloud identity.
REVIEWED_EXCLUSIONS = {"gh *", "git push *", "git fetch *", "git pull *", "git ls-remote *"}

pytestmark = pytest.mark.skipif(
    not SETTINGS.is_file(), reason="the Claude Code agent policy is not enabled in this project"
)


def _settings() -> dict:
    return json.loads(SETTINGS.read_text())


def test_nothing_the_agent_launches_can_rewrite_its_own_authority():
    """A launched program could write `.claude/approved-scope.json` until 2026-09-26.

    That file is the owner's approval scopes: one shell command could have added a scope that
    silences the prompts on guard files. Claude Code's defaults protected only the settings
    files and `.claude/hooks/`; this denies the whole folder, and the git paths that can
    disable hooks, as our own policy rather than a default (zynth-auth's tamper paths).
    """
    deny_write = _settings()["sandbox"].get("filesystem", {}).get("denyWrite", [])
    for path in ("./.claude/", "./.git/hooks/", "./.git/config"):
        assert path in deny_write, f"a launched program can write {path}"


@pytest.mark.parametrize(
    "path",
    [
        ".claude/settings.local.json",
        ".claude/settings.local.json.bak-pre-sandbox",
        ".claude/settings.json.bak",
    ],
)
def test_settings_backups_never_enter_git(path):
    """A backup of the local settings is as machine-specific as the file itself."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", path], cwd=REPO_ROOT, capture_output=True, check=False
    )
    assert result.returncode == 0, f"{path} is not ignored by git"


def test_there_is_no_way_out_of_the_sandbox():
    """No per-command escape hatch, and no silent fallback when the sandbox cannot start."""
    sandbox = _settings()["sandbox"]
    assert sandbox.get("enabled") is True
    assert sandbox.get("allowUnsandboxedCommands") is False, "the escape hatch is open"
    assert sandbox.get("failIfUnavailable") is True, "an unavailable sandbox would run unconfined"


def test_only_reviewed_commands_run_outside_the_sandbox():
    excluded = set(_settings()["sandbox"].get("excludedCommands", []))
    extra = excluded - REVIEWED_EXCLUSIONS
    assert not extra, f"commands running outside the sandbox without review: {extra}"
    assert "gh *" in excluded, "gh fails TLS inside the sandbox; without this it cannot work"


def test_every_exclusion_is_a_pattern_not_a_bare_name():
    """A bare `docker` matched nothing in ZynthQ, so the tool silently stayed sandboxed."""
    bare = [c for c in _settings()["sandbox"].get("excludedCommands", []) if not c.endswith(" *")]
    assert not bare, f"exclusions must be '<tool> *' patterns: {bare}"


def test_gh_reads_the_agent_token_and_never_the_personal_login():
    """On another machine the folder does not exist, so gh reports "not logged in": closed."""
    configured = _settings().get("env", {}).get("GH_CONFIG_DIR", "")
    assert configured, "GH_CONFIG_DIR unset: gh would fall back to the owner's personal login"
    path = PurePosixPath(configured)
    assert path.is_absolute(), "gh does not expand '~' in GH_CONFIG_DIR"
    assert str(path).endswith("/" + AGENT_GH_DIR), f"not the agent's token folder: {configured}"
    assert path.name != "gh", "that is the owner's personal gh login"


def test_the_agent_cannot_read_or_print_its_token():
    """The token acts for the agent; it is not the agent's to copy anywhere."""
    deny = _settings()["permissions"]["deny"]
    assert f"Read(~/{AGENT_GH_DIR}/**)" in deny, "the Read tool could open the token file"
    for verb in ("token", "login", "logout", "switch", "refresh", "setup-git"):
        assert f"Bash(gh auth {verb}*)" in deny, f"gh auth {verb} must be denied"


def test_tools_that_act_outside_the_sandbox_are_removed():
    """Browser and desktop control act as the owner, in the owner's real sessions."""
    deny = _settings()["permissions"]["deny"]
    for server in ("mcp__claude-in-chrome", "mcp__computer-use", "mcp__Claude_Browser"):
        assert server in deny, f"{server} bypasses the sandbox entirely"


def _hook(command: str) -> int:
    payload = json.dumps({"tool_input": {"command": command}})
    return subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, timeout=30
    ).returncode


@pytest.mark.skipif(not HOOK.is_file(), reason="hooks not enabled")
@pytest.mark.parametrize(
    "command",
    [
        "GH_CONFIG_DIR= gh pr list",
        "GH_CONFIG_DIR=~/.config/gh gh api user",
        "export GH_CONFIG_DIR=/tmp/x",
        "unset GH_CONFIG_DIR",
        "env -u GH_CONFIG_DIR gh pr list",
        "env --unset=GH_CONFIG_DIR gh pr list",
        "env -i gh pr list",
        "GH_TOKEN=abc gh pr list",
        "GITHUB_TOKEN=abc git push origin feat/x",
    ],
)
def test_a_command_cannot_switch_the_github_identity(command):
    assert _hook(command) == 2, f"this could reach the owner's personal login: {command!r}"


@pytest.mark.skipif(not HOOK.is_file(), reason="hooks not enabled")
@pytest.mark.parametrize(
    "command",
    [
        "gh pr list",
        "gh auth status",
        "grep -n GH_CONFIG_DIR docs/runbooks/agent-permissions.md",
        "git push origin feat/x",
    ],
)
def test_ordinary_github_work_is_not_blocked(command):
    """The positive control: naming the variable, or using gh as configured, is fine."""
    assert _hook(command) == 0, f"ordinary work was blocked: {command!r}"
