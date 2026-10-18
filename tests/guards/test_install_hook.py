"""Every package install asks the owner, however it is spelled (prompt budget, ADR-0020).

The static `*npm install*` / `*pip install*` asks matched text. On 2026-09-25 eleven install
spellings ran silently past them, one of them through an explicit allow. The hook
`.claude/hooks/ask_on_install.py` parses the command instead. These tests run the real hook,
through the same stdin envelope Claude Code sends, against both directions: every install form
must ask, and routine commands — including ones that merely MENTION an install — must not.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest
from conftest import REPO_ROOT

SETTINGS = REPO_ROOT / ".claude" / "settings.json"
HOOK = REPO_ROOT / ".claude" / "hooks" / "ask_on_install.py"

pytestmark = pytest.mark.skipif(
    not SETTINGS.is_file(), reason="the Claude Code agent policy is not enabled in this project"
)


def _decision(stdin: str) -> str | None:
    result = subprocess.run(
        [sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"the hook must decide by output, not exit code: {result}"
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


def _verdict(command: str) -> str | None:
    return _decision(json.dumps({"tool_input": {"command": command}}))


def test_the_hook_exists_and_sees_every_shell_command():
    """A hook file nobody registered is decoration; so is a registration with no file."""
    assert HOOK.is_file(), f"{HOOK.relative_to(REPO_ROOT)} is missing"
    settings = json.loads(SETTINGS.read_text())
    commands = [
        hook.get("command", "")
        for entry in settings["hooks"]["PreToolUse"]
        if entry.get("matcher") == "Bash"
        for hook in entry.get("hooks", [])
    ]
    assert any("ask_on_install.py" in c for c in commands), "the install hook is not registered"


def test_npx_cannot_download_what_it_does_not_find():
    """With `npm_config_yes=false`, npx refuses to fetch a missing package instead of assuming
    yes, which it otherwise does whenever stdin is not a terminal."""
    env = json.loads(SETTINGS.read_text()).get("env", {})
    assert env.get("npm_config_yes") == "false"


INSTALLS = [
    # The eleven that ran silently on 2026-09-25.
    "npm i -D vitest@4.1.11",
    "npm add vitest",
    "npx npm@10.9.8 install",
    "npx cowsay hello",
    "pip3 install requests",
    "backend/.venv/bin/pip3 install requests",
    "uv add requests",
    "pnpm add left-pad",
    "yarn add left-pad",
    "go install example.com/tool@latest",
    "go get example.com/mod",
    # Every other spelling and manager the hook knows.
    "npm install vitest",
    "npm isntall vitest",
    "npm update",
    "npm audit fix",
    "npm exec -- create-thing",
    "npm init vite",
    "npx -p left-pad node x.js",
    # Names a trusted project tool, but --package fetches something else first.
    "npx --package=evil-pkg prettier --check .",
    "pnpm dlx create-thing",
    "yarn",
    "bun add left-pad",
    "pip install requests",
    "pip download requests",
    "python -m pip install requests",
    "python3.12 -m pip install requests",
    "backend/.venv/bin/python -m pip install requests",
    "python -m ensurepip",
    "uv pip install requests",
    "uv tool install ruff",
    "uv run --with requests script.py",
    "uvx ruff",
    "pipx run cowsay",
    "go run example.com/tool@v1.0.0",
    "gem install rails",
    "cargo install ripgrep",
    "poetry add requests",
    "brew install gitleaks",
    "apt-get install curl",
    # Wrapped, chained or nested.
    "FOO=1 npm i left-pad",
    "env npm i left-pad",
    "cd frontend && npm i left-pad",
    "npm run build; npm i left-pad",
    'sh -c "npm i left-pad"',
    "npm test | npx cowsay",
]

ROUTINE = [
    "npm ci",
    "npm run build",
    "npm test",
    "npm audit --audit-level=high",
    "npx prettier --check .",
    "npx tsc --noEmit",
    "npx vitest run",
    "pip-audit -r requirements.txt",
    "backend/.venv/bin/pip-audit -r backend/requirements.txt",
    "pip list",
    "python scripts/sandbox_probe.py",
    "backend/.venv/bin/python -m pytest tests/guards -q",
    "uv sync",
    "go mod download",
    "go test ./...",
    "go run ./cmd/tool",
    "make backend",
    'git commit -m "npm install notes"',
    'grep -n "pip install" docs/LESSONS.md',
    "echo npm i left-pad",
]


@pytest.mark.skipif(not HOOK.is_file(), reason="the install hook is not applied yet")
@pytest.mark.parametrize("command", INSTALLS)
def test_every_install_asks(command):
    assert _verdict(command) == "ask", f"this installs a package and did not ask: {command!r}"


@pytest.mark.skipif(not HOOK.is_file(), reason="the install hook is not applied yet")
@pytest.mark.parametrize("command", ROUTINE)
def test_routine_commands_do_not_ask(command):
    """The positive control. A hook that asks for everything is a prompt, not a control."""
    assert _verdict(command) is None, f"a routine command was made to ask: {command!r}"


@pytest.mark.skipif(not HOOK.is_file(), reason="the install hook is not applied yet")
def test_an_unparsable_command_asks():
    """It cannot tell whether this installs, so it must not assume it does not."""
    assert _verdict("npm i 'left-pad") == "ask"


@pytest.mark.skipif(not HOOK.is_file(), reason="the install hook is not applied yet")
def test_a_broken_payload_asks_rather_than_passes():
    """Fails by asking: a bug in the hook costs a click, never a silent install."""
    assert _decision("not json") == "ask"
