# 0020. The agent reaches GitHub with its own repo-only token and never leaves the sandbox

- **Status:** Accepted
- **Date:** 2026-09-25
- **Deciders:** Albert Alcance (founder)
- **Amends:** ADR-0019 (agent confined to the project)

## Context

ADR-0019 put the agent's shell in the macOS sandbox. Probed again on 2026-09-25 through a launched program and a grandchild process, the sandbox held on all nine checks:
- no writes to the home directory or the user's Claude settings;
- no reads of `~/.ssh`, the personal `gh` login, or sibling projects;
- no network outside the allow-list.

Two ways around it remained:
1. **`gh` and git's network commands run outside the sandbox**, because the GitHub CLI fails TLS inside it. They ran as the owner's **personal** GitHub login (`~/.config/gh`), which can reach every repository the owner has and every setting of this one. The Read deny on that folder stopped the agent reading the file; it did not stop the unsandboxed `gh` from using it. git's credential helper for github.com is `gh auth git-credential`, so `git push` used the same login.
2. **The per-command escape hatch** (`allowUnsandboxedCommands: true`) let any command be retried outside the sandbox with one approving click. It was also the largest single source of prompts: worktree removal, branch switches across `.claude/`, pip-audit, Docker.

The founder shared the setup from another repository (ZynthQ): a fine-grained token for the agent, the escape hatch off, `failIfUnavailable`, and the browser and desktop-control tools removed. This decision adopts those parts, and keeps this repository's stronger ones: the whole home directory unreadable, caches inside the project, named hosts instead of wildcards.

## Decision

1. **The agent has its own GitHub identity.** `env.GH_CONFIG_DIR` in the committed settings points `gh` (and git, through its helper) at `~/.config/gen6th-accord-agent-gh`. That folder holds a fine-grained token scoped to this repository only:
   - read and write: Contents, Pull requests, Workflows;
   - read only: Actions, Commit statuses, Issues, Dependabot alerts, Metadata;
   - no Administration, Secrets, Variables or Environments.

   The token expires after 90 days.
2. **The agent cannot change or copy that identity.**
   - The Read tool is denied the token folder.
   - `gh auth token/login/logout/switch/refresh/setup-git` are denied; `gh auth status` is allowed.
   - `block_dangerous_bash.py` refuses any command that assigns, unsets or clears `GH_CONFIG_DIR`, `GH_TOKEN` or `GITHUB_TOKEN` (including `env -u` and `env -i`).
3. **There is no way out of the sandbox.** `allowUnsandboxedCommands: false` and `failIfUnavailable: true`. Only `gh` and git's `push`, `fetch`, `pull` and `ls-remote` run outside it, each as a `"<tool> *"` pattern. `docker`, `gcloud` and `terraform` are no longer excluded. Docker is effectively host access, and the two cloud CLIs would run with the owner's full cloud credentials. They return only with an agent cloud identity of their own (the Terraform stage).
4. **Tools that act outside the sandbox are removed in this project**: `mcp__claude-in-chrome` (the owner's real browser sessions), `mcp__computer-use` (the desktop) and `mcp__Claude_Browser` (an unfiltered browser).
5. **Where it fails, it fails closed.** On a machine without the token folder, `gh` reports "not logged in", and the agent has no GitHub access rather than the owner's.

## Consequences

- A mistake or a poisoned dependency acting through the agent's `gh` can reach this repository, and only as far as the token allows. GitHub itself now refuses settings, rulesets, secrets and every other repository, whatever the local rules say.
- The agent still acts *as the owner's account*: GitHub cannot tell its actions from the owner's. The separate machine account stays a Stage 8 launch gate.
- **The token can add labels** (probed by the owner on 2026-09-25: "Pull requests: write" includes it, and a fine-grained token cannot carve it out). So the local deny rules are the whole label control until the Stage 8 machine account. Auditing them against that fact found five silent paths, all closed the same day:
  - `gh pr create -l guardrail-change`;
  - `--label` with `sensitive-change-approved`, `no-tests-needed` or `no-changelog`;
  - GraphQL mutations, which only asked.

  Label flags on `gh pr create` and `gh issue create` are now denied whatever the label, and `gh api graphql` is denied.
- Things the agent can no longer do at all: run the Docker-backed backend tests locally (CI runs them), remove worktrees, or commit changes to `.claude/` (the owner does). The habits in `CLAUDE.md` §6 already avoid all three.
- `allowed github.com` remains a possible exfiltration path (domain fronting); the proxy decides on the hostname only.
- **Maintenance:** the token expires. Renew it by 2026-12-19 (90 days from 2026-09-25, less five). Generate a new one with the same permissions, re-run the login into the same folder, check `gh auth status`, then delete the old token on GitHub. Deleting the token on GitHub revokes all of the agent's GitHub access.

## Alternatives considered

- **Keep the personal login for `gh`.** Rejected: an unsandboxed tool with access to every repository is the widest door left.
- **Keep the escape hatch, asking each time.** Rejected: a prompt the owner approves by reflex is not a control, and it was the main source of prompts.
- **Put `GH_CONFIG_DIR` in `settings.local.json`**, as ZynthQ does. Rejected here: `make policy` fails on any local env entry (ADR-0019). A committed path that does not exist elsewhere fails closed.
- **Wildcard hosts and per-cache home-directory writes** from the ZynthQ template. Rejected: this repository already names each host and keeps every cache in the project.
