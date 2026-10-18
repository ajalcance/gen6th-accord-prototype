# CLAUDE.md — Working Contract for Gen6th Accord

This file is the contract every AI assistant (and human) follows when working in this repo.
Claude Code reads it automatically each session. **Follow it without exception.**

> Companion file: [`AGENTS.md`](AGENTS.md) mirrors this for other AI coding tools.

---

## 0. What this project is (context)

Accountability infrastructure for work made by people, institutions and AI agents: governed collaboration, structured claims and independently verifiable trust.
Plain-language map (start here if new): [`docs/OVERVIEW.md`](docs/OVERVIEW.md); jargon in
[`docs/GLOSSARY.md`](docs/GLOSSARY.md). Full design: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
Roadmap: [`docs/PLAN.md`](docs/PLAN.md). How the whole control system fits together:
[`docs/ENGINEERING_PROCESS.md`](docs/ENGINEERING_PROCESS.md).

### Source of truth — when records disagree

The repository, not a chat transcript, is the durable memory. When two records conflict, trust them
in this order, and **treat anything from a session/assistant as a hint to reverify, never authority**:

1. **Running code, migrations, tests, and live GitHub / repository settings** — reality outranks any doc.
2. **[`docs/architecture/current-state.md`](docs/architecture/current-state.md)** — what exists now (as-built).
3. **[`docs/decisions/`](docs/decisions/)** — why durable decisions were made (ADRs).
4. **[`docs/PLAN.md`](docs/PLAN.md)** — completed / current / next work.
5. **[`docs/LESSONS.md`](docs/LESSONS.md)** — dated, reusable learning and gotchas.
6. **[`CHANGELOG.md`](CHANGELOG.md)** — user-visible history.
7. **Assistant / session notes** — hints only; reverify against the above before acting.

Don't copy a repository fact into a note — a second copy is a competing truth that drifts.

---

## 1. 🔴 The non-negotiables

1. **Secrets & keys NEVER enter git.** No `.env`, no `*.pem`, no tokens or passwords in code
   or commits. Only `.env.example` (placeholders) is committed. If you need a secret, reference
   an env var.
2. **Fail closed.** Missing key/config, unreachable dependency, ambiguous auth → deny, never
   degrade to insecure. Outside `development` the config validator *requires* real secrets and
   raises if any are missing — no insecure fallback.
3. **Never weaken security to make something work.** If auth/validation blocks you, fix the
   integration — don't disable checks, widen CORS to `*`, or skip verification.
4. **Reuse over rewrite.** Prefer keeping/adapting existing code over rewriting.

---

## 2. 🟢 The after-every-change ritual (Definition of Done)

**Nothing is "done" until the docs reflect it.** After any meaningful change:

1. ✅ Code compiles / tests pass (`make check` or the relevant runner).
2. ✅ Update **[`docs/PLAN.md`](docs/PLAN.md)** — move the item's status; add follow-ups found.
3. ✅ Append a dated entry to **[`docs/LESSONS.md`](docs/LESSONS.md)** — what changed, what you
   learned, any gotcha. One short entry; always dated.
4. ✅ **Keep the as-built page true:** [`docs/architecture/current-state.md`](docs/architecture/current-state.md).
   If the change adds/moves/removes a module, route, stored shape, dependency, or the deploy
   shape → update it in the same PR. (`make dod-check` / CI `doc-guards` enforces that every
   `backend/accord/` module, every `frontend/` directory, + top-level dir is named there.)
   - **New design decision** (not just implementing an already-decided plan) → add an **ADR** in
     [`docs/decisions/`](docs/decisions/) (next number, template) and reconcile
     [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
5. ✅ **Coverage — telemetry + detection + audit + compliance** — every new/changed action must
   **emit** an envelope event, have a **detection decision**, an **audit decision**, and a
   **compliance decision** (all backend-gate-enforced). See the spine's coverage guards.
6. ✅ Update **[`CHANGELOG.md`](CHANGELOG.md)** under `## [Unreleased]`.
7. ✅ Commit with a **Conventional Commit** message (see §5).

> This ritual keeps plans, lessons, and architecture in lockstep with the code. Skipping it is a
> defect, not a shortcut.

---

## 3. Enterprise coding standards (summary — full: [`docs/CODING_STANDARDS.md`](docs/CODING_STANDARDS.md))

- **File length:** target ≤ 300 lines, hard cap **400**. Over that → split by concern.
- **Function length:** ≤ 50 lines. Keep cyclomatic complexity low.
- **One router per resource.** Handlers are **thin** — business logic in `services/`, data access
  in the DB layer. No fat controllers.
- **Type everything** (Python type hints, strict TS). No untyped public functions.
- **No dead code, no `.bak` files, no commented-out blocks** committed.
- **Tests** for every new behaviour; security-relevant code requires tests.

Every rule has a stable id in [`docs/standards/`](docs/standards/README.md) — cite `BE-004`, don't
paraphrase it. Each rule also states **how it is actually enforced**: `[CI]` means a gate catches a
violation today; `[Review]` means nothing will, and most rules are `[Review]`. Never mark a rule
`[CI]` without naming a mechanism that exists — `scripts/standards_check.py` fails the build if you
do, for the same reason the control map's markers exist.

---

## 4. How to run / test

```bash
make check          # full local gate
make policy         # the repository-wide guards — the SAME list CI runs, not a copy of it
make harness        # lint the guards, their fault tests and the session hooks
make backend        # backend only (ruff, black, mypy, bandit, pip-audit, pytest)
make trust          # trust services (go mod verify, vet, golangci-lint+gosec, govulncheck, race tests)
make fmt            # auto-format
make dod-check      # doc-consistency guards (a subset of `make policy`)
```

`make check` (and CI) is the source of truth. The backend tests run on a throwaway PostgreSQL
and need **Docker running**, or `ACCORD_TEST_DATABASE_URL` pointing at a server they may create
databases on. Inside the agent's sandbox the Docker socket is unreachable and there is no way out
of the sandbox (ADR-0020), so the agent leaves the backend tests to CI. Local dev:

```bash
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn accord.main:app --reload
```

---

## 5. Git & branching

- **Trunk-based.** `main` is the single long-lived branch and is always releasable. Short-lived
  `feat/*`, `fix/*`, `security/*`, `refactor/*`, `docs/*`, `chore/*` branch off `main` and
  squash-merge back
  (see [`docs/decisions/0005-trunk-based-branching.md`](docs/decisions/0005-trunk-based-branching.md)).
- **Never push directly to `main`.** PRs only — enforced server-side by the branch ruleset, not
  by convention. **One exception:** the very first commit of a freshly generated project is the
  root commit and has nowhere else to go; push it, then work in branches from then on.
- Release tags are cut **from `main`** — `release.yml` refuses to sign a tag that isn't an
  ancestor of the default branch.
- **Conventional Commits:** `type(scope): summary` — types: `feat`, `fix`, `refactor`, `docs`,
  `test`, `chore`, `security`, `perf`.
- Keep commits focused: one logical change each.
- **Green on a pull request says nothing about green on `main`.** The pull-request run and the
  push run take different paths through the same workflow. After a merge, look at the push
  run — and evaluate a check rollup by completion time, because a superseded run leaves a
  misleading entry beside the live one. See rule 18 in §8.

---

## 6. Security workflow

- Run `gitleaks detect` / pre-commit before pushing (hooks do this automatically).
- Any security-relevant change → note it in [`docs/SECURITY.md`](docs/SECURITY.md) and tag the
  commit `security:`.
- **Local Claude Code hooks** (`.claude/settings.json`) auto-format backend Python, block
  footguns (direct push to `main`, `--no-verify`, dangerous `rm -rf`) and secret writes, and
  confine every *change* to this project. Reading elsewhere is fine; changing anything outside
  is not. These are *ergonomics* that shift the guards left — **CI and the branch ruleset are
  the real, fail-closed enforcement.**

### Permission precedence — read this before touching `.claude/`

> **Precedence is `deny` → `ask` → `allow`. A hook's `allow` is one more allow, and it LOSES to
> any static `ask` rule matching the same path.**

That single fact cost a full day elsewhere: a scope hook returned `allow` correctly, was
verified by hand, had a hundred passing assertions — and waived nothing for an entire day
because a static `ask` rule outranked it, while three documents described it as live. So the
design here is inverted: for the core paths a scope may cover there is **no static `ask` rule
at all**, and `.claude/hooks/approved_scope.py` does the asking itself.

Two consequences:

- That hook **fails closed by asking**. It is the only thing prompting on those paths, so every
  error in it must become `ask` — its blanket exception handler is required, not sloppy.
- `.claude/settings.json`, `.claude/hooks/` and `.claude/approved-scope.json` keep their static
  rules and the hook says nothing about them. Widening the agent's own authority must not
  depend on the agent's code being correct.

### The agent is confined to the project and cannot approve its own work (ADR-0019)

- **Only the owner changes the agent's policy.** Both settings files, git hooks and git config are
  denied to every write tool. So are labels, `--approve`, `--admin`, rulesets and branch
  protection. Never try another route to the same end; ask the owner.
- **The shell is sandboxed, with no way out** (ADR-0020). The home directory is unreadable,
  writes stay in the project, and the network is an allow-list. A command that fails with
  `Operation not permitted` has hit the boundary. There is no unsandboxed retry: say what is
  missing instead. Never suggest widening the sandbox to credentials or dotfiles.
- **The agent has its own GitHub identity** (ADR-0020). `gh` and `git push` use a repo-only
  token through `GH_CONFIG_DIR`. Never set, clear or unset `GH_CONFIG_DIR`, `GH_TOKEN` or
  `GITHUB_TOKEN`; the hook refuses it, and the owner's personal login is not the agent's.
- **Changes outside the project always ask**, whatever the scope file says.
- **The local settings file may only restrict.** `make policy` fails if
  `.claude/settings.local.json` widens anything. The owner prunes it by hand.
- **Tool caches live in `.cache/`.** The owner commits changes to `.claude/`, and a new clone runs
  `pre-commit install-hooks` once in the owner's own terminal.

### Approval is per unit of work, not per keystroke

[`.claude/approved-scope.json`](.claude/approved-scope.json) ships empty. A scope names the
work, cites the decision it serves, gives a reason, lists its paths and expires — and the owner
approves that one file, once. A scope that is malformed, uncited, unbounded or expired waives
nothing. A broad pattern never reaches a system-altering area; those are covered only by a
pattern that names them. A scope buys silence at the keystroke, **never at the gate**.

### Working habits the hooks imply

- The scope waives `Edit`/`Write`/`MultiEdit`/`NotebookEdit` only. `sed -i`, redirects and `tee`
  go through Bash, which no scope covers — reaching for the shell to change a file turns an
  approved, silent edit into a prompt. The answer is never to widen the allow list.
- **One plain command per Bash call.** Pipes and `&&` defeat sub-command matching and prompt
  even when each part is individually allowed.
- Write records with the file tools, not through a shell heredoc. A hook that scans prose will
  refuse prose: quoting a forbidden flag in a lessons entry looks exactly like using it.

### Working habits that keep the owner out of the loop (2026-09-25)

The owner is the only approver and is often away. A prompt that CI would have caught anyway is
a stalled session (see the prompt budget in `docs/runbooks/agent-permissions.md`). So:

- **Scratch files go in `.cache/`**, never the session scratchpad or `/tmp`. A file-tool write
  outside the project always asks; `.cache/` is inside, gitignored and sandbox-writable.
- **Let CI verify what the sandbox cannot run** (Docker-backed backend tests). There is no
  retry outside the sandbox (ADR-0020); queue anything that truly needs the owner for one batch.
- **Never switch the checkout across a change to `.claude/`.** The sandbox refuses the rewrite
  halfway, leaving HEAD unmoved and the files half-switched. Bring such a branch up to date with
  git plumbing (`merge-tree`, a temporary `GIT_INDEX_FILE`, `commit-tree`, then push
  `SHA:refs/heads/<branch>`), which never touches the checkout.
- **Create branches with `git switch --no-track -c <name> origin/main`.** Without `--no-track`,
  git's upstream write to `.git/config` is refused and the switch stops halfway. Check
  `git status --branch` before every commit.
- **No agent worktrees.** `.git/worktrees/` is not writable from the sandbox, so the agent could
  never remove one.
- **Prefer the allowed `gh` subcommands** (`pr view/list`, `run list/view/watch`) and
  read-only `gh api` on this repository. Avoid `--jq` with pipes or quotes: the confinement hook
  cannot parse them, and refuses. `gh pr checks` fails under the agent's token: it needs
  `checks:read`, which no fine-grained token can hold. Read CI through `gh run`.
- **Ask for owner actions once**, in one message with ready-to-paste commands: labels, settings,
  repository toggles. **Name the branch in every push command** (`git push origin <branch>`):
  branches made with `--no-track` have no upstream, so a bare `git push` fails.
- **Owner commands check their own preconditions** (zynth-auth's practice). A block that copies
  a proposed policy file first checks it is on the expected branch and that the file's SHA-256
  matches the one the tests ran against, and does nothing otherwise:
  `[ "$(git branch --show-current)" = "<branch>" ] && echo "<sha256>  <file>" | shasum -a 256 -c && cp …`.
  The owner then installs exactly what was tested, or nothing.


---

## 7. When in doubt

- **Going long / getting complex?** Stop and split — new file, new module, new ADR.
- **Unsure of a decision?** Write an ADR proposing it rather than deciding silently.
- **Proactively recommend the professional approach** even if not asked.

---

## 8. Rules that cost real time before they were written down

Each of these was learned the expensive way. They are ordered by how often they recur, not by
importance.

1. **A gate scanning an empty set is the failure mode to design against first.** Print the
   denominator, fail on an empty required set, and where a set is legitimately empty for now,
   say so and name the constant that makes it real.
2. **A control is real when something exercises it end to end**, not when its unit tests pass.
   When something is about to run for the first time, watch it run.
3. **Test a guard at the point it has to hold**, not the point that is easiest to test.
4. **A surviving mutant is a missing test** unless provably equivalent — and a mutant that
   fails the *wrong* test has not tested what you think. A setting that ships empty is a
   setting nobody has tested.
5. **Negative tests are satisfied by any fault**, including one nobody meant to introduce.
   Invert a test occasionally to check it was passing for the reason you think.
6. **Diff two lists the project already maintains**, and reconcile them against the population
   they are meant to cover — not merely against each other.
7. **An escape hatch must never be wider than the gate it escapes.**
8. **Encode the premise an argument rests on**, or the argument is decoration.
9. **A stale comment on a security list is an instruction to the next person to leave the
   hole.**
10. **Check whether the gate is right before deciding it is inconvenient.** Changing a guard
    because it blocked you, in the pull request it blocked, is the shape this failure takes.
11. **Fix it or register it — never mention it.** A remark is forgotten with the session; a
    registered blocker stops a release until someone closes it.
12. **"No suppressions" is the right default and the wrong absolute.** The test is whether the
    rule applies, not whether the marker is present.
13. **A fixture that trips a scanner teaches the next person to add an exemption.** Assemble it
    at runtime so no literal exists — do not widen the scanner.
14. **An unfinished refactor is worse than none.** Revert it rather than repairing it in place.
15. **When a rule already exists somewhere in a file, extend it rather than writing a parallel
    one**, or the two will disagree about everything the first one learned.
16. **Read what the thing says about itself first.** The conflation usually lives in the
    caller, not in the thing being called.
17. **Verify by SHA, never from a cached status**, and evaluate a check rollup by completion
    time — a superseded run leaves a misleading entry.
18. **Green on a pull request says nothing about green on `main`.** The two triggers take
    different paths through the same workflow: a path filter reads the diff through the API on
    one and through git on the other, a re-run replays the *original* event payload, and a
    cancelled run reports a non-success result. Defects here are invisible until the first
    merge.
