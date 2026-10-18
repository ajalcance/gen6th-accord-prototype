"""Prompts belong where CI cannot see the risk, and nowhere else.

The owner is the only approver and is often away, so a prompt that duplicates a CI check costs
a stalled session and trains the reflex that approves the prompt that matters. A prompt earns
its place for four things only:
- leaving the project (sandbox, network, files elsewhere);
- an outward action that is hard to undo (tags, releases, workflow runs, API writes);
- the agent's own authority (`.claude/`);
- code from outside entering the machine (installs, docker).

These tests resolve real commands through the committed policy with Claude Code's precedence
(deny, then ask, then allow; the first match wins) and assert where each lands. The command
lists are the population; the rules are what is tested. A rule that is merely present proves
nothing if a broader rule elsewhere wins first.
"""

from __future__ import annotations

import fnmatch
import json
import subprocess
import sys

import pytest
from conftest import REPO_ROOT

SETTINGS = REPO_ROOT / ".claude" / "settings.json"
HOOK = REPO_ROOT / ".claude" / "hooks" / "block_dangerous_bash.py"
REPO_API = "repos/ajalcance/gen6th-accord"

pytestmark = pytest.mark.skipif(
    not SETTINGS.is_file(), reason="the Claude Code agent policy is not enabled in this project"
)


def _settings() -> dict:
    return json.loads(SETTINGS.read_text())


def _bucket(command: str) -> str:
    """Where a Bash command lands: deny, ask, allow, or unlisted."""
    permissions = _settings()["permissions"]
    for bucket in ("deny", "ask", "allow"):
        for rule in permissions.get(bucket, []):
            if rule.startswith("Bash(") and fnmatch.fnmatchcase(command, rule[5:-1]):
                return bucket
    return "unlisted"


def _sandboxed(command: str) -> bool:
    sandbox = _settings()["sandbox"]
    excluded = sandbox.get("excludedCommands", [])
    return sandbox.get("enabled") is True and not any(
        fnmatch.fnmatchcase(command, pattern) for pattern in excluded
    )


def _silent(command: str) -> bool:
    """Allowed outright, or unlisted and auto-allowed because it runs inside the sandbox.

    An unlisted command outside the sandbox (every `gh` call) prompts.
    """
    bucket = _bucket(command)
    auto = _settings()["sandbox"].get("autoAllowBashIfSandboxed") is True
    return bucket == "allow" or (bucket == "unlisted" and auto and _sandboxed(command))


SILENT = [
    f"gh api {REPO_API}/actions/runs",
    f'gh api "{REPO_API}/actions/workflows/ci.yml/runs?head_sha=abc&event=push"',
    f'gh api "{REPO_API}/dependabot/alerts?state=open&per_page=50"',
    "gh pr edit 35 --body-file .git/ACCORD_PR_BODY.md",
    "gh pr create --base main --head feat/x --title y --body-file .git/ACCORD_PR_BODY.md",
    "gh run rerun 36130126065 --failed",
    "gh issue list --label release-blocker",
    "gh release view v0.1.0",
    "gh workflow list",
    "gh auth status",
    "rm .cache/scratch.txt",
    # Naming the identity variables is fine; only assigning or removing them is refused.
    "grep -n GH_CONFIG_DIR docs/runbooks/agent-permissions.md",
    "git grep -n -e GH_TOKEN -- .github/workflows",
]

PROMPTS = [
    f"gh api -X PUT {REPO_API}/vulnerability-alerts",
    f"gh api {REPO_API}/issues -f title=x",
    f"gh api {REPO_API}/issues -F body=@notes.md",
    f"gh api {REPO_API}/pulls --method POST",
    f"gh api {REPO_API}/issues --field title=x",
    f"gh api {REPO_API}/issues --raw-field title=x",
    f"gh api {REPO_API}/contents/x --input body.json",
    f"gh api {REPO_API}/../../orgs/other",
    "gh release create v1.0.0",
    "gh release upload v1.0.0 sbom.json",
    "gh release edit v1.0.0 --draft",
    "gh release delete v1.0.0",
    "gh workflow run release.yml",
    "gh workflow enable ci.yml",
    "gh workflow disable ci.yml",
    "gh variable set X --body y",
    "gh pr close 30",
    "gh repo edit --visibility public",
    "rm -rf build",
    "rm -f notes.txt",
    "git tag v1.0.0",
    "docker ps",
    "pip install requests",
    "uv pip install requests",
    "backend/.venv/bin/python -m pip install requests",
]

REFUSED = [
    "gh pr edit 35 --add-label guardrail-change",
    "gh pr edit 35 --remove-label guardrail-change",
    "gh pr create --label guardrail-change --title x",
    "gh pr create --label allow-suppressions --title x",
    # The agent's token CAN label on GitHub (probed 2026-09-25: "Pull requests: write" includes
    # it), so these local rules are the whole label control. Every label, every flag form.
    "gh pr create --title x -l guardrail-change",
    "gh pr create --title x -lguardrail-change",
    "gh pr create --title x --label sensitive-change-approved",
    "gh pr create --title x --label=no-tests-needed",
    "gh pr create --title x --label no-changelog",
    "gh issue create --title x --label release-blocker",
    "gh issue create --title x -l allow-exemptions",
    "gh api graphql -f query=mutation",
    "gh api graphql --paginate",
    # Switching the GitHub identity (ADR-0020). The hook refuses these too, but that hook lets a
    # command through if it fails; these static rules are the layer that cannot (zynth-auth).
    "GH_CONFIG_DIR= gh pr list",
    "GH_CONFIG_DIR=/Users/x/.config/gh gh api user",
    "export GH_CONFIG_DIR=/tmp/x",
    "GH_TOKEN=abc gh pr list",
    "GITHUB_TOKEN=abc git push origin feat/x",
    "GH_ENTERPRISE_TOKEN=abc gh pr list",
    "unset GH_CONFIG_DIR",
    "env -u GH_CONFIG_DIR gh pr list",
    "env --unset=GH_CONFIG_DIR gh pr list",
    "env -i gh pr list",
    "cd frontend && env -i gh pr list",
    "gh label create owner-only",
    "gh pr review 35 --approve",
    "gh ruleset list",
    "gh secret set TOKEN",
    "gh auth token",
    "gh auth switch --user someone",
    f"gh api {REPO_API}/rulesets",
    f"gh api {REPO_API}/branches/main/protection",
    f"gh api {REPO_API}/issues/1/labels -f labels=x",
    "gh pr merge 35 --admin --squash",
    "git push origin feat/x --force-with-lease",
    "git commit -m x --no-verify",
]


@pytest.mark.parametrize("command", SILENT)
def test_routine_reads_and_edits_do_not_prompt(command):
    assert _silent(command), f"{command!r} is routine; it should not cost a prompt"


@pytest.mark.parametrize("command", PROMPTS)
def test_outward_or_irreversible_actions_still_prompt(command):
    assert _bucket(command) == "ask", f"{command!r} changes state beyond the tree; it must ask"


@pytest.mark.parametrize("command", REFUSED)
def test_self_approval_stays_refused(command):
    assert _bucket(command) == "deny", f"{command!r} lets the agent approve itself; deny it"


def test_the_api_allow_never_reaches_another_repository():
    """gh runs outside the sandbox, so its allow rules are the whole boundary."""
    api_allows = [
        rule for rule in _settings()["permissions"]["allow"] if rule.startswith("Bash(gh api")
    ]
    assert api_allows, "no gh api allow rules — the silent list above could not pass"
    wide = [rule for rule in api_allows if REPO_API not in rule]
    assert not wide, f"gh api allows reaching beyond this repository: {wide}"
    for command in ("gh api repos/someone/else/contents/x", "gh api user"):
        assert not _silent(command), f"{command!r} must prompt: it leaves this repository"


@pytest.mark.parametrize(
    "path",
    [
        "~/.docker/config.json",
        "~/.kube/**",
        "~/.config/gcloud/**",
        "~/.npmrc",
        "~/.pypirc",
        "~/Library/Keychains/**",
    ],
)
def test_every_credential_store_is_denied_to_the_read_tool(path):
    """test_agent_policy.py checks five of these; the mutation pass found the rest unchecked."""
    assert f"Read({path})" in _settings()["permissions"]["deny"], f"Read({path}) must be denied"


def test_no_blanket_gh_allow():
    """`Bash(gh *)` or `Bash(gh pr *)` would silently allow every write verb that exists."""
    allow = _settings()["permissions"]["allow"]
    blanket = [r for r in allow if r in ("Bash(gh *)", "Bash(gh api *)", "Bash(gh pr *)")]
    assert not blanket, f"blanket gh allows: {blanket}"


def test_the_sandboxed_tools_can_reach_what_they_need():
    """A tool that cannot run inside the sandbox is retried outside it, and that asks."""
    settings = _settings()
    env = settings.get("env", {})
    for key in ("PIP_CERT", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"):
        assert env.get(key) == "/etc/ssl/cert.pem", f"{key} must name the system CA bundle"
    domains = settings["sandbox"]["network"]["allowedDomains"]
    for domain in ("proxy.golang.org", "sum.golang.org", "vuln.go.dev"):
        assert domain in domains, f"make trust needs {domain} inside the sandbox"


# --- The push hook: block pushes TO main, not branches named after it ----------------------


def _hook(command: str) -> int:
    payload = json.dumps({"tool_input": {"command": command}})
    return subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, timeout=30
    ).returncode


@pytest.mark.skipif(not HOOK.is_file(), reason="hooks not enabled")
@pytest.mark.parametrize(
    "command",
    [
        "git push origin main",
        "git push -u origin main",
        "git push origin HEAD:main",
        "git push origin +main",
        "git push origin feat/x:main",
        "git push origin 213d61b:refs/heads/main",
        "git push origin master",
        "git push upstream main",
        "git push origin main --tags",
    ],
)
def test_a_push_to_main_is_blocked(command):
    assert _hook(command) == 2, f"a push to the default branch passed: {command!r}"


@pytest.mark.skipif(not HOOK.is_file(), reason="hooks not enabled")
@pytest.mark.parametrize(
    "command",
    [
        "git push origin security/release-requires-green-main",
        "git push -u origin feat/main-page",
        "git push origin 213d61b:refs/heads/feat/trust-go-module",
        "git push origin chore/mainline-docs",
    ],
)
def test_a_branch_named_after_main_is_not_blocked(command):
    """The false block forced a branch rename on 2026-09-25; the positive control."""
    assert _hook(command) == 0, f"a push to an ordinary branch was blocked: {command!r}"
