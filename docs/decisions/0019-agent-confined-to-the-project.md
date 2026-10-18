# 0019. The agent is confined to the project and cannot approve its own work

- **Status:** Accepted
- **Date:** 2026-09-25
- **Deciders:** Albert Alcance (founder)
- **Amends:** ADR-0007 (agent permission model)

## Context

The founder asked whether the agent had only project-level access on this laptop. It did not. Checked on 2026-09-25:
- **Changes:** confined to the project for Bash only (`confine_to_project.py`). The file tools had no such rule; the scope hook stayed silent about paths outside the project and said the Bash hook "owns that question". The Bash hook never sees a file tool.
- **Reads:** not confined. Anything the macOS user can read, the agent could read, including `~/.ssh`, `~/.aws`, the `gh` token and every other project.
- **Shell:** unsandboxed. Commands ran as the founder with full network access.
- **Self-approval:** nothing stopped the agent applying the owner's `guardrail-change` label, approving a pull request, or editing its own settings file with one approving click.

The founder shared the permission model used in the Zynth Auth repository as a reference ("allow broadly, ask narrowly, deny precisely", self-approval denied, settings split into committed and local), and asked for it to be applied through this repository's own process and strengthened where possible.

Adopting it verbatim would have weakened three things here:
1. Its guard-path `ask` rules cover Edit and Write only. MultiEdit and NotebookEdit stay open, which `test_every_protected_path_is_protected_against_every_write_tool` exists to catch.
2. A static `ask` on a path the scope hook claims silently voids the hook (ADR-0007, CLAUDE.md §6).
3. Bare `Bash` allow, relying on deny and ask alone, is broader than this repository's explicit allow list.

## Decision

1. **The agent cannot approve its own work.** Denied outright, never asked:
   - `--admin`;
   - adding or removing any label, `gh label`, and label API calls;
   - `--approve`;
   - rulesets and branch-protection API calls;
   - `--no-verify` and `core.hooksPath` anywhere in a command;
   - any write to `.git/hooks/**` or `.git/config`;
   - any write to `.claude/settings.json` or `.claude/settings.local.json`, with all four write tools.

   Only the owner, outside the session, changes the agent's policy.
2. **Reads and writes stop at the project.**
   - The file-tool allow rules are project-scoped (`Tool(/**)`).
   - A write outside the project always asks (`approved_scope.py`), and no scope can cover it.
   - Home-directory credentials are denied to every tool.
3. **The shell runs in the OS sandbox** (macOS Seatbelt).
   - The home directory is unreadable (`denyRead: ["~/"]`), with three exceptions: the project (`./`) and git's own config (`~/.gitconfig`, `~/.config/git/`).
   - Writes are confined to the project and the session temp directory.
   - The network is limited to an allow-list (GitHub, PyPI, npm, Semgrep).
   - `gh`, `docker`, `gcloud`, `terraform` and git's network commands cannot run sandboxed. They are excluded and go through the permission flow instead.
   - Leaving the sandbox always asks the owner, never the auto-mode classifier.
4. **Tool caches live in the project** (`.cache/`, via `env`), never the home directory. A cache outside the project is where a sandboxed command could leave code for an unsandboxed one.
5. **Settings split** as in the Zynth model:
   - The committed file is the reviewed policy.
   - The gitignored local file may only restrict it. `scripts/check_agent_local_settings.py`, part of `make policy`, fails on any local entry that widens the policy, and on any unknown key.
6. **Installs prompt wherever they appear in a command** (`*pip install*`, `*npm install*`), not only at its start.
7. **Kept from ADR-0007:**
   - the explicit allow list, rather than bare `Bash`;
   - the scope hook for core paths;
   - every protected path covered for all four write tools.

## Consequences

- The agent now reaches your other projects, your credentials and the network beyond the allow-list only by asking you.
- It can no longer change its own settings, and it can no longer apply the label that approves a guard change.
- Changing the agent's policy is now always the owner's act, outside the session.
- Committing a change to `.claude/hooks/` or the settings files needs one unsandboxed commit, which asks the owner. The sandbox forbids writes there, and pre-commit opens every staged file for writing.
- A new clone runs `pre-commit install-hooks` once outside the sandbox. The sandbox forbids the `.git/config` writes that installation makes.
- `permissions.blockReadsOutsideWorkingDirectories` would also stop the file tools *reading* outside the project in every mode, but it overrides every sandbox `allowRead`. With it on, git cannot read its identity and every commit fails (verified 2026-09-25). It is off. File-tool reads outside the project are prompt-gated instead of refused. This is registered in `docs/PLAN.md`.
- Two findings, both tested:
  - Sandbox `allowRead: ["."]`, the docs' own example, does not re-open the project; `./` does.
  - `Bash(pip install *)` did not match `backend/.venv/bin/python -m pip install`.
- This is still not the real security boundary. CI, the branch ruleset and the owner-only labels remain the fail-closed controls (ADR-0004, ADR-0018). The devcontainer (Stage 0) is the stronger isolation still to come.

## Alternatives considered

- **Adopt the Zynth settings verbatim.** Rejected for the three weakenings listed in Context.
- **Bare `Bash` allow with a sandbox.** Fewer prompts, but anything not named in ask or deny would run silently whenever it had to leave the sandbox. Rejected for now.
- **`blockReadsOutsideWorkingDirectories` instead of path rules.** It broke every commit, as described above.
- **Exclude `git commit` from the sandbox so policy commits don't ask.** Rejected. It would run every pre-commit hook environment unsandboxed. A policy change should cost the owner a click.
- **Run the agent only in the devcontainer.** It is the stronger boundary, but not ready. Claude Code isn't installed in the image, the Anthropic API isn't allow-listed, and host credentials are forwarded. Its Node 20 drift is fixed in this change. It stays a Stage 0 item.
