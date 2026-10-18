"""The agent permission policy must be well-formed and actually deny what it claims.

A malformed permission rule does not error — it simply never matches, so the policy silently
grants everything it was written to restrict. These tests make that a build failure. They only
run when the Claude Code policy module is enabled.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

import pytest
from conftest import REPO_ROOT

SETTINGS = REPO_ROOT / ".claude" / "settings.json"
HOOK = REPO_ROOT / ".claude" / "hooks" / "block_dangerous_bash.py"
RULE_RE = re.compile(
    r"^(Bash|Read|Edit|Write|MultiEdit|NotebookEdit|WebFetch|Glob|Grep)\(.+\)$"
    r"|^mcp__[A-Za-z0-9_-]+(__[A-Za-z0-9_-]+)?$"
)
# Every tool that can put bytes on disk. A rule written for Edit alone leaves Write open,
# and a protected path an agent can Write is not protected.
WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")

pytestmark = pytest.mark.skipif(
    not SETTINGS.is_file(), reason="the Claude Code agent policy is not enabled in this project"
)


def _permissions() -> dict:
    return json.loads(SETTINGS.read_text())["permissions"]


def test_every_rule_is_well_formed():
    """A typo'd rule matches nothing and quietly grants what it meant to restrict."""
    malformed = [
        rule
        for bucket in ("deny", "ask", "allow")
        for rule in _permissions().get(bucket, [])
        if not RULE_RE.match(rule)
    ]
    assert not malformed, f"malformed permission rules (these match nothing): {malformed}"


def test_secret_material_is_denied_not_merely_asked():
    """Precedence is deny -> ask -> allow, so secrets must be in deny to be unconditional."""
    deny = " ".join(_permissions()["deny"])
    for expected in ("./.env", "*.pem", "*.key"):
        assert expected in deny, f"{expected} must be denied outright, not left to a prompt"


def test_env_example_stays_readable():
    """A `.env.*` glob would also block the documented placeholder file."""
    deny = _permissions()["deny"]
    assert "Read(./.env.*)" not in deny, (
        "denying ./.env.* also blocks .env.example, which the README tells adopters to copy; "
        "list the real secret filenames instead"
    )


def test_the_agents_own_authority_stays_statically_gated():
    """`.claude/` keeps STATIC rules and no hook may waive them.

    Everything else that needs a human moved to .claude/hooks/approved_scope.py — a static
    `ask` there would outrank the hook's `allow` and the scope would waive nothing (see
    tests/guards/test_approved_scope.py). This one path is the deliberate exception:
    widening the agent's own authority must not depend on the agent's code being correct.
    """
    ask = " ".join(_permissions()["ask"])
    assert (
        "Edit(./.claude/**)" in ask
    ), "the permission policy and the hooks must prompt through a static rule, not a hook"


def test_the_paths_that_need_a_human_are_gated_somewhere():
    """Statically or by the scope hook — but never by neither.

    The reconciliation between the two lives in
    tests/guards/test_protected_path_reconciliation.py, which checks both against a
    population written out by hand rather than against each other.
    """
    ask = " ".join(_permissions()["ask"])
    hook = REPO_ROOT / ".claude" / "hooks" / "approved_scope.py"
    core = hook.read_text() if hook.is_file() else ""
    for path, pattern in (
        ("./.github/**", ".github/**"),
        ("./scripts/**", "scripts/**"),
        ("./CLAUDE.md", "CLAUDE.md"),
        ("./docs/decisions/**", "docs/decisions/**"),
    ):
        assert (
            f"Edit({path})" in ask or f'"{pattern}"' in core
        ), f"{path} is gated by neither a static rule nor the scope hook"


def test_every_protected_path_is_protected_against_every_write_tool():
    """A rule written for Edit only does not stop a Write, and Write overwrites the file whole.

    Trivially exploitable, trivially fixed, and exactly the kind of thing a template should
    get right once for everyone. Only the statically-gated paths are checked here; the scope
    hook matches on the tool NAME, so it cannot have this gap by construction — and
    test_approved_scope.py asserts it is registered for all four.
    """
    ask = _permissions()["ask"]
    paths = {rule[len("Edit(") : -1] for rule in ask if rule.startswith("Edit(")}
    assert paths, "no protected paths found — this assertion would otherwise be vacuous"
    missing = [
        f"{tool}({path})"
        for path in sorted(paths)
        for tool in WRITE_TOOLS
        if f"{tool}({path})" not in ask
    ]
    assert not missing, (
        "protected paths with a gap — an agent can reach them with another write tool: "
        + ", ".join(missing)
    )


def test_an_adr_cannot_be_written_without_a_prompt():
    """ADRs outrank docs/PLAN.md in the source-of-truth order (CLAUDE.md §0).

    A broad `docs/**` allowance waived the prompt, leaving the one record that outranks the
    roadmap the only one an agent could write with nobody in the loop. The prompt now comes
    from the scope hook, which sees every write tool at once — so this asserts the path is
    claimed there rather than listing four static rules.
    """
    hook = REPO_ROOT / ".claude" / "hooks" / "approved_scope.py"
    if not hook.is_file():
        ask = _permissions()["ask"]
        for tool in WRITE_TOOLS:
            assert f"{tool}(./docs/decisions/**)" in ask
        return
    assert (
        '"docs/decisions/**"' in hook.read_text()
    ), "an ADR an agent writes unreviewed silently overrules the roadmap"


def test_settings_gate_edits_to_themselves():
    """ADR-0004: an agent must not be able to quietly widen its own authority."""
    assert "Edit(./.claude/**)" in _permissions()["ask"]


def test_bypass_permissions_mode_is_disabled():
    assert _permissions().get("disableBypassPermissionsMode") == "disable"


def test_release_and_destructive_actions_are_never_silent():
    """Each must prompt or be refused outright — deny is the stronger of the two, not a gap."""
    permissions = _permissions()
    gated = " ".join(permissions["ask"] + permissions["deny"])
    for rule in ("git tag", "git push --force", "rm -", "gh release", "sudo", "docker"):
        assert (
            rule in gated
        ), f"'{rule}' changes state beyond the working tree — it must not be silent"


def test_the_never_acceptable_is_denied_rather_than_asked():
    """A prompt that is always declined is not a control; it is a click that trains reflex.

    Most prompts came from the unlisted, not the dangerous, and clicking through each one
    destroys the signal on the prompts that matter. Where there is no acceptable answer,
    there is no reason to spend a click.
    """
    deny = " ".join(_permissions()["deny"])
    for rule in ("git push --force", "sudo", "npm publish", "gh secret", "--no-verify"):
        assert rule in deny, (
            f"'{rule}' has no acceptable answer, so it must be denied outright rather than "
            f"left to a prompt somebody will eventually approve by reflex"
        )


def test_routine_work_does_not_prompt():
    """Confirmation fatigue is the failure mode: if everything prompts, nothing is read."""
    allow = " ".join(_permissions()["allow"])
    for rule in ("make ", "git status", "git commit", "git diff"):
        assert rule in allow, f"'{rule}' is routine and should not consume an approval"


# --- The agent may not approve its own work (ADR-0019) -----------------------------------


def _settings() -> dict:
    return json.loads(SETTINGS.read_text())


def test_the_agent_cannot_approve_its_own_work():
    """A guard change needs the owner's label; an agent that can apply it needs no owner.

    Denied, not asked: a prompt that must always be refused trains the reflex that approves it.
    """
    deny = _permissions()["deny"]
    for rule in (
        "Bash(*--admin*)",
        "Bash(*--add-label*)",
        "Bash(*--remove-label*)",
        "Bash(gh label *)",
        "Bash(gh api *labels*)",
        "Bash(*--approve*)",
        "Bash(gh ruleset *)",
        "Bash(gh api *rulesets*)",
        "Bash(gh api *protection*)",
    ):
        assert rule in deny, f"{rule} must be denied: it lets the agent approve its own change"


@pytest.mark.parametrize("target", ["./.claude/settings.json", "./.claude/settings.local.json"])
def test_the_agent_cannot_widen_its_own_settings(target):
    """`ask` would let one approving click widen the policy for good; `deny` needs a human
    at a keyboard, outside the session."""
    deny = _permissions()["deny"]
    missing = [f"{tool}({target})" for tool in WRITE_TOOLS if f"{tool}({target})" not in deny]
    assert not missing, f"the agent can rewrite its own policy through: {missing}"


def test_git_hooks_cannot_be_skipped_or_rewritten():
    """The commit-time scan is only a control if the agent cannot step around it."""
    deny = _permissions()["deny"]
    for rule in ("Bash(*--no-verify*)", "Bash(*core.hooksPath*)"):
        assert rule in deny, f"{rule} must be denied"
    for target in ("./.git/hooks/**", "./.git/config"):
        missing = [f"{tool}({target})" for tool in WRITE_TOOLS if f"{tool}({target})" not in deny]
        assert not missing, f"a git hook or its config can be rewritten through: {missing}"


def test_credentials_in_the_home_directory_are_denied_to_the_file_tools():
    """Read-deny rules also feed the shell sandbox, so each one closes both doors."""
    deny = _permissions()["deny"]
    for path in ("~/.ssh/**", "~/.aws/**", "~/.gnupg/**", "~/.config/gh/**", "~/.netrc"):
        assert f"Read({path})" in deny, f"Read({path}) must be denied"


def test_file_tool_allows_stop_at_the_project():
    """`/**` in project settings means this project. `//` or `~` would mean the machine."""
    allow = _permissions()["allow"]
    file_rules = [rule for rule in allow if rule.split("(", 1)[0] in ("Read", *WRITE_TOOLS)]
    assert file_rules, "no file-tool allow rules found — this assertion would be vacuous"
    wide = [rule for rule in file_rules if not re.match(r"^\w+\((\./|/(?!/))", rule)]
    assert not wide, f"file-tool allows that reach outside the project: {wide}"


def test_installs_prompt_wherever_they_appear():
    """`Bash(pip install *)` missed `backend/.venv/bin/python -m pip install` on 2026-09-25.

    A rule anchored at the start of the command is defeated by any path or wrapper in front.
    """
    ask = _permissions()["ask"]
    for rule in ("Bash(*pip install*)", "Bash(*npm install*)"):
        assert rule in ask, f"{rule} must prompt: an install is a supply-chain event"


# --- The shell is confined to the project (ADR-0019) --------------------------------------

# The only things outside the project a sandboxed command may read. git needs its identity.
REVIEWED_READS = {"./", "~/.gitconfig", "~/.config/git/"}
# An interpreter or shell outside the sandbox is the sandbox switched off.
NEVER_EXCLUDED = ("python", "python3", "node", "npm", "npx", "make", "bash", "sh", "zsh", "pip")


def _sandbox() -> dict:
    return _settings().get("sandbox", {})


def test_the_sandbox_is_on_and_fences_the_home_directory():
    sandbox = _sandbox()
    assert sandbox.get("enabled") is True, "the shell sandbox is off"
    filesystem = sandbox.get("filesystem", {})
    assert "~/" in filesystem.get("denyRead", []), "shell reads are not fenced at the home dir"
    extra = set(filesystem.get("allowRead", [])) - REVIEWED_READS
    assert not extra, f"reads re-opened outside the project without review: {extra}"
    assert "./" in filesystem.get("allowRead", []), (
        "the project itself is not re-opened. Note `.` does NOT work — only `./` does "
        "(verified 2026-09-25): with `.` every sandboxed command fails on the project"
    )
    assert not filesystem.get("allowWrite"), "shell writes widened beyond the project"


def test_no_interpreter_escapes_the_sandbox():
    excluded = " ".join(_sandbox().get("excludedCommands", []))
    escaped = [name for name in NEVER_EXCLUDED if re.search(rf"(^|\s){name}(\s|\*|$)", excluded)]
    assert not escaped, f"an interpreter runs unsandboxed, which disables the sandbox: {escaped}"


def test_leaving_the_sandbox_always_asks():
    """The retry escape hatch goes to the owner, never to the auto-mode classifier."""
    assert "Bash(dangerouslyDisableSandbox:true)" in _permissions()["ask"]


def test_the_network_allowlist_has_no_wildcard_that_opens_everything():
    domains = _sandbox().get("network", {}).get("allowedDomains", [])
    assert domains, "no allowed domains — the sandbox would prompt for every fetch"
    assert not [d for d in domains if d in ("*", "*.*") or d.startswith("*.com")], domains


def test_tool_caches_stay_inside_the_project():
    """A cache outside the project is where a sandboxed command leaves code for later."""
    env = _settings().get("env", {})
    assert env.get("PRE_COMMIT_HOME"), "pre-commit would fall back to the home directory"
    caches = {k: v for k, v in env.items() if "cache" in k.lower() or k.endswith("_HOME")}
    outside = {k: v for k, v in caches.items() if str(v).startswith(("/", "~"))}
    assert not outside, f"tool caches outside the project: {outside}"


def test_tls_trust_comes_from_the_system_not_from_inside_the_project():
    """Inside the sandbox, `Read(./**/*.pem)` also hides every vendored CA bundle.

    pip and requests then fail on PyPI. Point them at the OS bundle, which is outside the
    project and is not a secret. Never narrow the `*.pem` deny instead.
    """
    env = _settings().get("env", {})
    for key in ("PIP_CERT", "REQUESTS_CA_BUNDLE"):
        if key in env:
            assert env[key] == "/etc/ssl/cert.pem", f"{key} must name the system CA bundle"
    assert "Read(./**/*.pem)" in _permissions()["deny"], "the private-key deny was narrowed"


def _fake_key(kind: str) -> str:
    """A private-key block assembled at RUNTIME, so this file contains no literal.

    A fixture that trips the secret scanner teaches the next person to add an allowlist
    entry, and the allowlist is always easier than the fix — which is exactly why the
    ratchet exists. `detect-private-key` and gitleaks both scan this file on the adopter's
    very first commit, so a literal here means their first commit is rejected.
    """
    marker = "-" * 5
    head = " ".join(x for x in ("BEGIN", kind, "PRIVATE", "KEY") if x)
    tail = " ".join(x for x in ("END", kind, "PRIVATE", "KEY") if x)
    return f"{marker}{head}{marker}\nAAAA\n{marker}{tail}{marker}\n"


def _hook_verdict(command: str) -> int:
    """Run the real PreToolUse hook against a command; 2 means blocked."""
    payload = json.dumps({"tool_input": {"command": command}})
    return subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, timeout=30
    ).returncode


@pytest.mark.skipif(not HOOK.is_file(), reason="hooks not enabled")
@pytest.mark.parametrize(
    "command",
    [
        "gh pr merge --admin 5",
        "gh pr merge 5 --admin",
        "gh pr merge --squash --admin --delete-branch 5",
    ],
)
def test_admin_flag_is_blocked_in_any_position(command):
    """Permission rules are globs; `--admin` can appear anywhere, so the hook enforces it."""
    assert _hook_verdict(command) == 2, f"--admin must be blocked, but this passed: {command!r}"


@pytest.mark.skipif(not HOOK.is_file(), reason="hooks not enabled")
def test_ordinary_merge_is_still_allowed():
    """The positive control: the hook must not block the normal path."""
    assert _hook_verdict("gh pr merge --squash 5") == 0


# --- The secret-write hook ---------------------------------------------------------------
#
# Added because scripts/check_guard_coverage.py found it: this hook shipped as a control,
# was cited as a control, and nothing had ever demonstrated it could block anything.

SECRET_HOOK = REPO_ROOT / ".claude" / "hooks" / "block_secret_write.py"

secret_hook = pytest.mark.skipif(not SECRET_HOOK.is_file(), reason="hooks not enabled")


def _write_verdict(file_path: str, content: str = "") -> int:
    """Run the real PreToolUse hook against a Write payload; 2 means blocked."""
    payload = json.dumps({"tool_input": {"file_path": file_path, "content": content}})
    return subprocess.run(
        [sys.executable, str(SECRET_HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
    ).returncode


@secret_hook
@pytest.mark.parametrize(
    "path",
    [
        "/repo/.env",
        "/repo/.env.production",
        "/repo/certs/server.pem",
        "/repo/certs/server.key",
        "/repo/.ssh/id_ed25519",
        "/repo/.npmrc",
    ],
)
def test_secret_material_is_blocked_on_write(path):
    assert _write_verdict(path) == 2, f"a Write to {path} must be blocked, not allowed"


@secret_hook
def test_a_private_key_in_the_content_is_blocked_whatever_the_filename():
    """The filename is the easy half; a key pasted into notes.txt is the interesting one."""
    body = _fake_key("OPENSSH")
    assert _write_verdict("/repo/docs/notes.txt", body) == 2


@secret_hook
@pytest.mark.parametrize("path", ["/repo/.env.example", "/repo/backend/app/main.py"])
def test_ordinary_writes_are_not_blocked(path):
    """The positive control. .env.example is the file the README tells adopters to copy."""
    assert _write_verdict(path) == 0, f"{path} must not be blocked"


@secret_hook
def test_a_private_key_inserted_by_an_edit_is_blocked():
    """Registered for Write only, this hook never saw an Edit — and an Edit inserts bytes too.

    Extending the matcher without reading Edit's own field would be worse than leaving it:
    the hook would run, inspect nothing, and report clean.
    """
    body = _fake_key("RSA")
    payload = json.dumps(
        {"tool_name": "Edit", "tool_input": {"file_path": "/repo/notes.txt", "new_string": body}}
    )
    result = subprocess.run(
        [sys.executable, str(SECRET_HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2, "an Edit carrying a private key must be blocked"


@secret_hook
def test_a_private_key_inserted_by_a_multiedit_is_blocked():
    body = _fake_key("EC")
    payload = json.dumps(
        {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": "/repo/notes.txt",
                "edits": [{"old_string": "x", "new_string": body}],
            },
        }
    )
    result = subprocess.run(
        [sys.executable, str(SECRET_HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2, "a MultiEdit carrying a private key must be blocked"


@secret_hook
def test_the_secret_hook_sees_every_write_tool():
    """A tool the matcher misses is an unguarded way in."""
    settings = json.loads(SETTINGS.read_text())
    matchers = [
        entry.get("matcher", "")
        for entry in settings["hooks"]["PreToolUse"]
        if any("block_secret_write.py" in h.get("command", "") for h in entry.get("hooks", []))
    ]
    assert matchers, "the secret-write hook is registered for nothing"
    joined = "|".join(matchers)
    for tool in WRITE_TOOLS:
        assert tool in joined, f"the secret-write hook does not see {tool}"


@secret_hook
def test_a_malformed_payload_does_not_halt_every_write():
    """This hook fails OPEN by design: a bug in it must not brick the session.

    Its backstops are gitleaks in pre-commit and the CI hygiene job, which do not fail open.
    Recorded here so the direction is a decision somebody made, not an accident.
    """
    result = subprocess.run(
        [sys.executable, str(SECRET_HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
