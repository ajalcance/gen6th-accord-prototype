# Agent boundary — retained as-built evidence

- **Agent permission model + hooks** (`.claude/settings.json`): routine work (gate, tests,
  ordinary git) runs without prompting; policy/release/destructive/privileged actions **ask**;
  reading real secret material is **denied**; `--admin` is blocked by a PreToolUse hook (regex,
  and it runs before permission rules). Hooks also auto-format backend Python and block secret
  writes. A strong default, **not** an unbypassable control — **CI and the branch ruleset remain
  the fail-closed backstop.** See ADR-0007.
- **Agent confined to the project** (ADR-0019):
  - **No self-approval.** The agent is denied labels, `--approve`, `--admin`, rulesets and
    branch protection. It cannot edit its own settings files, git hooks or git config.
  - **Project-only file tools.** Their allow rules are project-scoped. A change outside the
    project always asks, and home-directory credentials are denied.
  - **Sandboxed shell** (macOS Seatbelt):
    - the home directory is unreadable, except the project and git's own config;
    - writes stay in the project;
    - the network is an allow-list;
    - only `gh` and git's network commands are excluded; there is no per-command escape
      hatch, and the agent refuses to run if the sandbox cannot start (ADR-0020).
  - **Its own GitHub identity** (ADR-0020): `gh` and `git push` use a fine-grained token scoped to
    this repository (`GH_CONFIG_DIR`), never the owner's personal login. The agent cannot read,
    print or switch it.
  - **No browser or desktop control** in this project: those tools act outside the sandbox.
  - **No writes to its own authority from the shell:** the sandbox refuses `.claude/`,
    `.git/hooks/` and `.git/config`. Per machine, sibling projects are refused to the file tools
    (`scripts/wall_off_siblings.py`), and machine-wide managed settings
    (`docs/runbooks/managed-settings.json`) deny every self-edit in every project.
  - **Tool caches** live in `.cache/`.
  - **Local settings check.** `make policy` fails when the gitignored local settings widen the
    policy.
  - **Owner-only changes at the PR.** The meta-guard demands the `guardrail-change` label for any
    pull request touching `.claude/`, `CLAUDE.md`, `AGENTS.md`, the `Makefile`, `tests/guards/`,
    `ruff-harness.toml` or the devcontainer firewall.
  - **Verified live 2026-09-25:** a label, `--no-verify`, a `~/.ssh` read, a settings edit and a
    home-directory shell read were each refused.
