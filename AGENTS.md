# AGENTS.md

This project's working contract for AI coding agents is **[`CLAUDE.md`](CLAUDE.md)** — read it
first and follow it without exception. This file exists so tools that look for `AGENTS.md` find
the same rules.

New to this repo? Read [`docs/OVERVIEW.md`](docs/OVERVIEW.md) for the plain-language map, then this.

Key points (full detail in `CLAUDE.md`):

- **Secrets & keys never enter git.** Fail closed. Never weaken security to make something work.
- **After every change:** `make check` green, then update `docs/PLAN.md`, `docs/LESSONS.md`,
  `docs/architecture/current-state.md`, add an ADR for new decisions, and `CHANGELOG.md`.
- **Standards:** files ≤ 400 lines, thin routers, type everything, tests for every behaviour. The
  full suite with citable ids is [`docs/standards/`](docs/standards/README.md); each rule states
  whether a gate actually enforces it (`[CI]`) or nobody will catch a violation (`[Review]`).
- **Conventional Commits**, PRs only, `make dod-check` must pass.

## Do NOT disable the guardrails

If a check blocks you, **fix the underlying code — never remove, weaken, suppress, or bypass the
check.** These guards are the product; disabling one deletes the protection the project depends
on (see [`docs/decisions/0004-agent-resistant-guardrails.md`](docs/decisions/0004-agent-resistant-guardrails.md)).
Attempts to weaken a guard are themselves gated and reviewed. What each one protects:

| If this blocks you… | It's protecting against… | The correct fix |
|---|---|---|
| **gitleaks** / secret scan | a leaked password, key, or token | remove the secret; reference an env var instead |
| **Semgrep** (dangerous-ops) | code that can run arbitrary commands / other high-risk patterns | rewrite to the safe pattern; don't add an ignore |
| **bandit / pip-audit / npm audit** | known-insecure code or a vulnerable dependency | fix the code or update the dependency |
| **ruff / black / mypy** | style drift, type errors, latent bugs | make the code conform; don't loosen the config |
| **pytest / coverage floor** · **vitest** | untested behaviour | add the test; don't lower the threshold |
| **dod-check** (`scripts/dod-check.py`) | docs drifting out of sync with code | update the docs to match reality |
| **check_pins** (`scripts/check_pins.py`) | an unpinned / floating dependency | pin the exact version |
| **meta_guard** (`scripts/meta_guard.py`) | silently weakening a guard: new suppressions, code without a test, editing a guard-defining file (`scripts/`, `tests/guards/`, a workflow, a ruleset, an ADR, `requirements-ci.txt`, the `Makefile`, the agent's own policy in `.claude/`, `CLAUDE.md`, `AGENTS.md`), changing a sensitive path (migrations/auth/audit/deploy/`trust/`), or lowering a threshold | address the real cause it flagged — a label is the owner's call, not yours |
| **check_guard_coverage** (`scripts/check_guard_coverage.py`) | a guard that is never run, or has no test proving it can fail — a control in name only | wire it into `make policy` or a workflow and give it a fault test; declare it a non-gate only with a written reason |
| **check_unicode_hazards** (`scripts/check_unicode_hazards.py`) | source that reads differently from how it runs: a bidirectional override, a zero-width or invisible character | delete the character; if you need one as DATA, build it at runtime with `chr()` rather than widening the scanner |
| **make harness** (`ruff-harness.toml`) | style and import drift in the guards, their tests and the hooks — the trees `make backend` does not reach | make the code conform; the rule set already excludes what measures the wrong thing here |
| **actionlint / shellcheck** | broken workflow expressions, unsafe shell | fix the workflow or script; don't add a `# shellcheck disable` |
| **standards_check** (`scripts/standards_check.py`) | a standards rule claiming a `[CI]` gate that doesn't exist, or a citation to a rule that was deleted | name a real mechanism, or lower the marker to `[Review]` and be honest |
| **release_preflight** (`scripts/release_preflight.py`) | releasing past an owner's hold, an open production blocker, a dirty or unmerged tree, a re-pointed tag, missing release notes, or a commit with no green CI run of its own on the default branch | fix what it names — a release is the one path with no PR review behind it |
| **release_evidence** (`scripts/release_evidence.py`) | a release record that names an image by mutable tag, or evidence belonging to a different release | record digests, and promote only the evidence for the tag being promoted |
| **confine_to_project** (`.claude/hooks/confine_to_project.py`) | a change reaching outside this project — a sibling folder, your dotfiles, the machine | do the work inside the project; if a one-liner is refused for being unreadable, write it out plainly rather than widening the hook |
| **ask_on_install** (`.claude/hooks/ask_on_install.py`) | a package install passing silently, whatever the manager or spelling (`npm i`, `npx <pkg>`, `pip3 install`, `uv add`, `go get`…) | nothing to work around: the owner approves each install. Lockfile installs (`npm ci`, `uv sync`) do not ask |
| **approved_scope** (`.claude/hooks/approved_scope.py`) | editing a core or system-altering path with nobody in the loop, or ANY file-tool change outside the project | answer the prompt, or have the owner add a scope to `.claude/approved-scope.json`. A scope buys silence at the keystroke, never at the gate, and never outside the project |
| **agent permission policy + shell sandbox** (`.claude/settings.json`, ADR-0019, ADR-0020) | the agent approving its own work (labels, `--approve`, `--admin`, rulesets), editing its own settings or git hooks, reading home-directory credentials, reaching outside the project from the shell, or switching its repo-only GitHub token for the owner's login | nothing to work around: ask the owner. An `Operation not permitted` is the boundary, and there is no unsandboxed retry |
| **check_agent_local_settings** (`scripts/check_agent_local_settings.py`) | the gitignored local settings widening the reviewed policy, one "don't ask again" click at a time | the owner moves a needed rule into `.claude/settings.json` (reviewed) and deletes it from the local file |
| **cosign verify** | deploying an unsigned / tampered image | build and sign through the release pipeline |
| **spine coverage guards** | an action that isn't recorded / monitored / audited | register the action for emit + detection + audit + compliance |
| **client/server trust boundary** | sealing something a browser *claimed* into the tamper-evident chain, or taking the actor from a request body | keep client-reported actions in `AUDIT_EXEMPT`; attribution comes from the verified request, never the payload |

> Anything that genuinely *should* change a guard is a **design decision** → propose it in an ADR
> for human review, don't do it silently.

## If you find yourself about to edit the thing checking you — stop

The single most dangerous rationalization available to you: a guard blocks your change, you
conclude "this is actually a bug in the guard," and you edit `scripts/`, a CI workflow, a ruleset,
or a scanner config so your own PR goes green. **The reasoning can sound completely plausible and
still be wrong** — you have a strong incentive to see the guard as broken, because that's the
version of events where your task succeeds.

This is not a hypothetical: it has happened, on this project's sibling repos, with an agent
genuinely believing it had found a false positive in `meta_guard.py`. It hadn't — the fix was one
sentence of rewording elsewhere. `meta_guard` now enforces this mechanically (a PR touching a
guard-defining file needs the owner-applied `guardrail-change` label — see the table above), but
the check is a backstop, not a substitute for catching yourself first.

**If your reasoning concludes "therefore I should edit the file that is checking me" — stop and
ask the repo owner before touching it.** A guard change is always its own PR, on its own merits,
with explicit approval. Never bundled into the work it happened to block.
