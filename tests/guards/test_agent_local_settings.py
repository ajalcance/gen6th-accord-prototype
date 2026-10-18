"""scripts/check_agent_local_settings.py must fail on every way a local file can widen.

The local settings file is gitignored and outranks the committed policy, so it is the one
place a permission can grow with nobody reviewing it. These tests prove the check refuses
each widening by name, accepts what only restricts, and does not mistake absence for a scan.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "scripts" / "check_agent_local_settings.py"


def run(tmp_path: Path, document: object | str | None) -> subprocess.CompletedProcess[str]:
    target = tmp_path / "settings.local.json"
    if document is not None:
        target.write_text(document if isinstance(document, str) else json.dumps(document))
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(target)],
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.parametrize(
    ("document", "named"),
    [
        ({"permissions": {"allow": ["Bash(ls /Users/me/Documents)"]}}, "permissions.allow"),
        ({"permissions": {"additionalDirectories": ["~/elsewhere"]}}, "additionalDirectories"),
        ({"permissions": {"defaultMode": "acceptEdits"}}, "defaultMode"),
        ({"sandbox": {"enabled": False}}, "sandbox.enabled"),
        ({"sandbox": {"excludedCommands": ["python *"]}}, "excludedCommands"),
        ({"sandbox": {"filesystem": {"allowRead": ["~/"]}}}, "allowRead"),
        ({"sandbox": {"filesystem": {"allowWrite": ["~/.zshrc"]}}}, "allowWrite"),
        ({"sandbox": {"network": {"allowedDomains": ["evil.example"]}}}, "allowedDomains"),
        ({"env": {"PRE_COMMIT_HOME": "/tmp/x"}}, "env"),
        ({"hooks": {"PreToolUse": [{"matcher": "Bash"}]}}, "hooks"),
        ({"aSettingInventedTomorrow": True}, "aSettingInventedTomorrow"),
    ],
)
def test_every_widening_fails_by_name(tmp_path, document, named):
    result = run(tmp_path, document)
    assert result.returncode == 1, f"{named} widened the policy and passed: {result.stdout}"
    assert named in result.stderr, f"the failure must name {named}: {result.stderr}"


def test_restrictions_pass(tmp_path):
    """The positive control: a local file may always take capability away."""
    document = {
        "$schema": "https://json.schemastore.org/claude-code-settings.json",
        "permissions": {"allow": [], "ask": ["Bash(git push*)"], "deny": ["Read(~/notes/**)"]},
        "sandbox": {
            "filesystem": {"denyRead": ["~/private"], "denyWrite": ["./docs"]},
            "network": {"deniedDomains": ["example.com"]},
        },
    }
    result = run(tmp_path, document)
    assert result.returncode == 0, result.stderr
    assert "inspected 6 key(s)" in result.stdout, "the denominator must count what was read"


def test_absence_is_reported_not_passed_silently(tmp_path):
    """CI never has the file. Say so by name rather than printing a scan of nothing."""
    result = run(tmp_path, None)
    assert result.returncode == 0
    assert "absent" in result.stdout


def test_an_unreadable_file_fails_closed(tmp_path):
    """Claude Code may skip a malformed file — or may not. Either way nobody can review it."""
    result = run(tmp_path, "{not json")
    assert result.returncode == 1
    assert "cannot be read" in result.stderr


def test_a_file_that_is_not_an_object_fails(tmp_path):
    result = run(tmp_path, ["allow everything"])
    assert result.returncode == 1


def test_it_runs_in_the_policy_gate():
    """A guard nothing runs is documentation."""
    makefile = (REPO_ROOT / "Makefile").read_text()
    policy = makefile.split("\npolicy:", 1)[1].split("\n\n", 1)[0]
    assert "check_agent_local_settings.py" in policy
