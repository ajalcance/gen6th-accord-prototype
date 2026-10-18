# Agent boundary controls

Retained without changing control scope; see [SECURITY.md](SECURITY.md).

## The AI agent's boundary (ADR-0019)

Codex has a separate, owner-installed companion boundary (ADR-0021). The repository
contains its proposed managed requirements, hook, tests and runbook at
[`runbooks/codex-permissions.md`](runbooks/codex-permissions.md). It is **not a live
control** until the owner installs it on this Mac and the probe passes. Claude's
controls below remain in force for Claude Code.

- **The agent cannot approve its own work.** Labels, `--approve`, `--admin`, rulesets and branch protection are denied, and so are edits to its own settings, git hooks and git config. Denied rather than asked, so one reflexive click cannot grant it.
- **It works inside the project only.**
  - The shell runs in the macOS sandbox: the home directory is unreadable, writes stay in the project, and the network is an allow-list.
  - File-tool changes outside the project always ask.
  - Home-directory credentials (`~/.ssh`, `~/.aws`, the `gh` token and more) are denied to every tool.
- **Its local settings can only tighten the policy.** `make policy` fails otherwise.
- **The agent reaches GitHub as its own repo-only token, and never leaves the sandbox** (ADR-0020). Until 2026-09-25 its unsandboxed `gh` and `git push` used the owner's personal login, which can reach every repository. Now:
  - a fine-grained token for this repository only, with no Administration, Secrets, Variables or Environments;
  - the agent cannot read, print or switch it;
  - there is no per-command escape hatch, and it refuses to run without the sandbox;
  - browser and desktop control are denied.

  `scripts/sandbox_probe.py` checks the sandbox from a launched program and a grandchild.
- **Nothing the agent launches can write its own authority** (from zynth-auth, 2026-09-26). The sandbox refuses `.claude/`, `.git/hooks/` and `.git/config`. Until then a launched program could write `.claude/approved-scope.json`, the owner's approval scopes. Also:
  - the token variables have static deny rules beside the hook, which lets a command through if it fails;
  - sibling projects are refused to the file tools, per machine;
  - managed settings deny every self-edit in every project on the Mac.
- **Every package install asks** (`ask_on_install.py`): the hook parses each program and verb, rather than matching the text `npm install`, which eleven other spellings slipped past. It asks on any error of its own, and `npm_config_yes=false` stops `npx` fetching silently.
- **The agent's token can add labels on GitHub** (probed 2026-09-25), so the local deny rules are the whole label control until the machine account. Label flags at PR or issue creation are denied whatever the label, and so are label and GraphQL API calls.
- **Prompts are spent only where CI cannot see the risk.** They cover leaving the project, outward actions that are hard to undo, the agent's own authority, and outside code entering the machine. `tests/guards/test_agent_prompt_budget.py` resolves real commands through the policy to hold that line in both directions. The local push hook blocks a push *to* `main` on any remote; until 2026-09-25 it missed every remote but `origin`.
- **The same files are owner-only at the pull request.** Any PR touching them needs the `guardrail-change` label: the agent's policy, `CLAUDE.md`, `AGENTS.md`, the `Makefile` gate list and the guard tests.
- **The limits of this boundary:**
  - These are ergonomic, local controls. The branch ruleset, required CI and owner-only labels remain the fail-closed controls.
  - File-tool *reads* outside the project are prompt-gated, not refused (see ADR-0019).
  - The agent still acts through the owner's GitHub account until the Stage 8 machine account.
