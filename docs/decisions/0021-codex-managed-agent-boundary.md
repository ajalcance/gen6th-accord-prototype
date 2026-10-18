# 0021. Codex uses an owner-managed agent boundary beside Claude Code

- **Status:** Accepted
- **Date:** 2026-09-29
- **Deciders:** Albert Alcance (founder)
- **Amends:** ADR-0019 and ADR-0020 for the Codex client

## Context

Claude Code already has repository and machine controls, but Codex does not read `.claude/settings.json`.
The founder wants both clients to work in this repository, with comparable authority and without
removing either client's policy. The Zynth Agent Sandbox Kit Standard v1.0 informed the control
layers; it is design context, not a configuration file.

Codex permission profiles are beta and require a supporting client. The local system requirements
file is outside the project and can be changed only by the owner. The repository cannot install
it through a pull request. GitHub Apps and browser tools use surfaces outside the command sandbox.

## Decision

1. Keep `.claude/`, `CLAUDE.md` and Claude's hooks. Codex reads `AGENTS.md`, which points at the
   same working contract.
2. The owner installs `scripts/codex/requirements.toml` at `/etc/codex/requirements.toml` and
   `scripts/codex/accord_pre_tool.py` in the root-owned managed-hooks directory. The requirements
   allow only two profiles: a sealed default and an exact-path profile for this repository.
   The owner selects the project profile after installation. A clean checkout has no active
   project selector, so Codex can still load configuration while the PR is under review.
3. The project profile denies the rest of the home directory, source secrets, `.claude/`,
   `.codex/`, `.agents/` and `.git/` writes. Network access from launched commands is disabled.
   Managed hooks refuse obvious owner-only shell actions; the OS profile, branch rules and CI are
   the enforcement layers when a command is indirect or a hook cannot observe it.
4. Managed requirements keep approvals from widening the profile, disable automatic review,
   Browser Use, Computer Use, Appshots, device remote control, Apps and plugins. Apps stay off
   until a separate decision gives a specific integration a demonstrably read-only scope.
5. The owner installs and proves the local policy using `docs/runbooks/codex-permissions.md`.
   Repository tests pin the policy bytes and prohibit a premature project selector. The owner
   applies the `guardrail-change` label to the policy pull request; the agent cannot.

## Consequences

- Claude and Codex policy files coexist. Each client keeps its own local enforcement, while
  repository CI and branch rules remain common controls.
- The managed file affects Codex across this Mac. Other projects start sealed and need their own
  reviewed, exact-path profile. This rollout intentionally removes Codex GitHub connector access;
  local repository source and read-only Git metadata remain available.
- Agent-initiated commits, pushes, releases, labels and host administration are unavailable in
  this profile. The hook refuses direct package install commands; pinned local installs can run
  when the required packages are already cached. The owner handles new dependencies.
- Repo source and tests prove the proposed policy, not the live Mac installation. The owner must
  run the live probe after installing it and re-run it after Codex updates. If the probe fails,
  the policy is not claimed active or equivalent.
- `.codex/` itself is not yet in `meta_guard`'s guarded-path expression. A protected guard test
  refuses an active selector before owner installation. A separate owner-approved guard change
  can add direct path coverage if a selector is introduced later.

## Alternatives considered

- **Reuse `.claude/settings.json` as Codex configuration.** Codex does not enforce that format.
- **Allow the current GitHub connector with low-risk actions.** The connector uses the owner's
  account, and its action permission is not a repo-only OS sandbox boundary.
- **Give all projects the same writable profile.** That would make this project's path writable
  from unrelated work and provide no reviewed scope for those projects.
