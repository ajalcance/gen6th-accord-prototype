# Agent permissions: how Accord confines the AI agent

How this repository controls what the AI agent (Claude Code) may do, what we changed on 2026-09-25 to make it stronger, and how to check it still holds.

The decision record is [ADR-0019](../decisions/0019-agent-confined-to-the-project.md), which amends [ADR-0007](../decisions/0007-agent-permission-model.md). The CI side of the same effort is in [`ci-integrity-checklist.md`](ci-integrity-checklist.md).

---

## 1. The short version

| Question | Before (2026-09-25 morning) | Now |
|---|---|---|
| Can the agent read files outside the project? | Yes, anything your Mac user can read | **Shell: no** (OS sandbox). **File tools:** only after asking you |
| Can it read `~/.ssh`, `~/.aws`, the `gh` token? | Yes | **No**, denied to every tool |
| Can it change files outside the project? | Shell: no. File tools: **yes**, silently in auto mode | **No**, without asking you, every time |
| Can it reach any website? | Yes | **Shell: only an allow-list** (GitHub, PyPI, npm, Semgrep) |
| Can it apply `guardrail-change` or another owner label? | Yes | **No**, denied |
| Can it approve a pull request, merge with `--admin`, or change the ruleset? | `--admin` blocked by a hook; the rest yes | **No**, denied |
| Can it edit its own permission settings? | Yes, with one approving click | **No**, denied. Only you, outside the session |
| Can it skip or rewrite git hooks? | `--no-verify` blocked at the start of `git commit` only | **No**: `--no-verify` or `core.hooksPath` anywhere in a command, and any write to `.git/hooks` or `.git/config` |
| Can a "don't ask again" click quietly widen its access? | Yes, and it did | **`make policy` fails** until you prune it |
| Which GitHub login does its `gh` and `git push` use? | Your personal login: every repository, every setting | **A fine-grained token for this repository only** (ADR-0020). It cannot read, print or switch it |
| Can it run a command outside the sandbox? | Yes, after one approving click | **No** (ADR-0020). Only `gh` and git's network commands run outside it, as the token above |
| Can it drive your browser or desktop? | Yes | **No** in this project: those tools are denied |

**What this is not.** These are local controls on your Mac. The real, fail-closed security is still server-side:
- the branch ruleset (no direct push to `main`, squash only, the required `ci-complete` check);
- CI's guards;
- labels only you apply;
- since ADR-0020, the token's own scope, which GitHub enforces whatever the local rules say.

The token still acts as **your** GitHub account, so GitHub cannot tell its actions from yours. A separate machine account is a Stage 8 launch gate.

---

## 2. The three layers

### Layer 1: permission rules (`.claude/settings.json`, committed)

Claude Code evaluates **deny → ask → allow**; the first match wins. Deny and ask rules also match each part of a compound command (`cd x && rm y`), and they still apply in auto mode.

| Bucket | What goes there | Examples |
|---|---|---|
| **deny**: never, no prompt | Anything with no acceptable answer, and anything that would let the agent approve or widen itself | `Bash(*--add-label*)`, `Bash(*--approve*)`, `Bash(*--admin*)`, `Bash(gh api *rulesets*)`, `Bash(*--no-verify*)`, `Edit(./.claude/settings.json)` (and Write, MultiEdit, NotebookEdit), `Read(~/.ssh/**)` |
| **ask**: you decide each time | Only what CI cannot see (the prompt budget below) | `Bash(gh api *-X *)` and every other API write flag, `Bash(rm -*)`, `Bash(*pip install*)`, `Bash(git tag *)`, `Bash(gh workflow run*)`, `Bash(dangerouslyDisableSandbox:true)`, edits under `.claude/` |
| **allow**: runs without a prompt | Routine work, **scoped to the project** | `Edit(/**)` (`/` means *this project* in project settings), `Bash(make *)`, `Bash(git commit *)`, `Bash(gh pr view*)`, `Bash(gh api repos/ajalcance/gen6th-accord/*)` (reads only) |

Why **deny** rather than **ask** for self-approval: a prompt that must always be refused trains the reflex that one day approves it.

### The prompt budget

CI and the branch ruleset are the enforcement. A prompt that repeats a check they already make stalls the session while the owner is away, and trains the reflex that approves the prompt that matters. A prompt belongs only where CI cannot see the risk:

| A prompt is for… | Because CI cannot see… | Rules |
|---|---|---|
| leaving the project | the Mac outside the repository | file-tool writes outside the project (scope hook), unlisted `gh` (runs outside the sandbox). Leaving the sandbox is no longer possible at all (ADR-0020) |
| outward actions that are hard to undo | anything that never becomes a commit | `git tag`, tag and branch deletes, `gh release` writes, `gh workflow run`, every `gh api` write flag and `graphql`, `gh pr close`, `gh repo`, `gh variable` |
| the agent's own authority | its own settings and hooks (a static rule, never a hook) | `.claude/**` |
| code from outside entering the machine | what runs locally before any PR exists | every package install, whatever the spelling (`ask_on_install.py`, with `*pip install*` and `*npm install*` as a static second layer, and `npm_config_yes=false` so `npx` never fetches silently), `docker`, `brew`, `ssh` |
| destructive local commands | uncommitted work | flagged `rm`, `git reset --hard`, `git clean` |

Everything else is either denied (self-approval, secrets) or silent. `tests/guards/test_agent_prompt_budget.py` resolves real commands through the policy, applying the precedence, and fails if a routine command would prompt, an outward one would not, or a self-approval one is not refused. Every ask and deny rule it covers was removed once to watch it fail.

### Layer 2: hooks (`.claude/hooks/`, run on every tool call)

| Hook | Stops |
|---|---|
| `block_dangerous_bash.py` | a push whose target is `main`/`master` on any remote (not a branch merely named after it), force-push, `--no-verify`, `--admin` in any position, `rm -rf` of a dangerous root |
| `confine_to_project.py` | a **shell** command that changes anything outside the project (it resolves `cd`, `..`, `~` and redirects first) |
| `ask_on_install.py` | a package install passing silently. It parses each program and verb, and asks for any install under any spelling and package manager: npm's eleven aliases for `install`, `npx <pkg>`, `pip3`, `python -m pip`, `uv add`, `go get`/`install`, and more. Lockfile installs don't ask. It also asks on any error of its own. |
| `approved_scope.py` | an edit to a core or system-altering path unless your approved scope covers it, and **now any file-tool change outside the project**, which no scope can cover |
| `block_secret_write.py` | writing a `.env`, a key file, or a private key into any file |

### Layer 3: the OS sandbox for the shell (macOS Seatbelt)

Every shell command the agent runs is wrapped by the operating system:
- **Reads:** the home directory is blocked (`denyRead: ["~/"]`). Only three places are re-opened: the project (`./`), `~/.gitconfig` and `~/.config/git/`, which git needs for your name and email.
- **Writes:** only the project and the session's temp folder. Inside the project, `denyWrite` refuses `.claude/`, `.git/hooks/` and `.git/config` (taken from zynth-auth's "tamper paths"). Until 2026-09-26 a launched program could write `.claude/approved-scope.json`, the owner's approval scopes. Claude Code's defaults had protected only the settings files and `.claude/hooks/`.
- **Network:** only the allow-list in `sandbox.network.allowedDomains`.
- **Excluded commands:** only `gh` and git's `push`/`fetch`/`pull`/`ls-remote`, each as a `"<tool> *"` pattern (a bare name matches nothing). They cannot work inside the sandbox, so they run outside it, as the agent's repo-only token, and go through the permission rules. `docker`, `gcloud` and `terraform` are no longer excluded (ADR-0020). Docker is effectively host access, and the cloud CLIs would run with your full cloud credentials.
- **Leaving the sandbox is impossible** (`allowUnsandboxedCommands: false`), and if the sandbox cannot start the agent refuses to run (`failIfUnavailable: true`).

### Layer 4: the agent's own GitHub identity (ADR-0020)

- `env.GH_CONFIG_DIR` points `gh`, and git through its credential helper (`gh auth git-credential`), at `~/.config/gen6th-accord-agent-gh`. That folder holds a fine-grained token for this repository only. It has no Administration, Secrets, Variables or Environments access.
- The agent cannot read the folder (Read deny), print or switch the token (`gh auth token/login/logout/switch/refresh/setup-git` denied), or point `gh` elsewhere. It is refused twice over, when a command assigns a token variable or removes `GH_CONFIG_DIR` (including `env -u` and `env -i`):
  - `block_dangerous_bash.py` refuses it;
  - static deny rules refuse it too. That hook lets a command through if it fails on an error, and a deny rule can't (zynth-auth's pattern, narrowed to assignments so that reading the variable's name stays allowed).
- On a machine without the folder, `gh` reports "not logged in": no access rather than yours.
- **Renew the token by 2026-12-19** (90 days from 2026-09-25, less five). Generate one with the same permissions, re-run the login from `ONBOARDING.md` §1d into the same folder, check `GH_CONFIG_DIR=~/.config/gen6th-accord-agent-gh gh auth status`, then delete the old token on GitHub. Deleting the token revokes all the agent's GitHub access at once.

Tool caches that would normally live in your home folder (pre-commit, pip, npm, uv, black) are redirected into the project's gitignored `.cache/`. A writable cache outside the project would be a place where a sandboxed command could leave code for something unsandboxed to run later.

### Layer 5: machine-wide, and per machine (from zynth-auth, 2026-09-26)

- **Managed settings** (`/Library/Application Support/ClaudeCode/managed-settings.json`, installed by the owner with `sudo` from [`managed-settings.json`](managed-settings.json)).
  - Every write tool is denied on both project settings files, the user settings file (`~/.claude/settings.json`) and the managed folder itself.
  - Nothing in any project can override it, and it covers **every** Claude Code project on this Mac, including ones without their own deny rules.
  - It only denies. `tests/guards/test_managed_settings.py` fails on any allow, ask or sandbox key, because a machine-wide widening would reach every project at once.
- **Sibling projects walled off** (`scripts/wall_off_siblings.py`, owner-run).
  - It writes deny rules for every folder next to this project, and for every other project's Claude memory, into the gitignored `settings.local.json`.
  - The file tools are then refused there, instead of asking. The shell sandbox already blocks the whole home folder.
  - Re-run it after adding a new project next to this one.

### Settings split

| File | Committed? | Job |
|---|---|---|
| `.claude/settings.json` | Yes, reviewed like code, `guardrail-change` label | The whole policy |
| `.claude/settings.local.json` | No (gitignored) | May only **restrict**. `scripts/check_agent_local_settings.py` (in `make policy`) fails on any allow rule, extra directory, permission mode, env var, hook, sandbox exception, or unknown key |

---

## 3. What we did, step by step (2026-09-25)

1. **Checked the claim instead of trusting it.** You asked whether the agent had project-only access. Reading the real settings showed:
   - only shell *writes* were confined;
   - reads, the network, the file tools and self-approval were open.
2. **Took the Zynth Auth setup as a reference, not a copy.** Adopted verbatim, it would have weakened three things here:
   - its guard-path asks cover two of the four write tools;
   - a static ask on a scope-hook path silently disables the hook;
   - a bare `Bash` allow is broader than our explicit list.

   We kept our stronger pieces and added Zynth's good ideas: self-approval denied, the settings split, project-scoped allows and the sandbox.
3. **Verified the docs before writing.** The sandbox docs showed that sandboxed commands can read the *whole computer* by default. A helper agent had claimed the opposite. Project-only reads therefore need an explicit fence.
4. **Built the policy and probed both sides of the boundary live.** Four real findings:
   - The docs' example `allowRead: ["."]` left the project unreadable to every command. `./` works.
   - `blockReadsOutsideWorkingDirectories` overrides every `allowRead`, so git lost your identity and commits failed. It is off, and registered in PLAN.
   - `Bash(pip install *)` did not match `backend/.venv/bin/python -m pip install`, which ran with no prompt. The rules now match `*pip install*` and `*npm install*` anywhere.
   - pre-commit's cache in `~/.cache` was unreachable, so caches moved into the project. Hook installation needs one unsandboxed run, which asks.
   - `pip-audit` could not verify PyPI's certificate. macOS system trust is unreachable under the sandbox, and the committed `*.pem` secret-deny also hides the bundled CA list. The fix is the OS bundle (`/etc/ssl/cert.pem`), set through two env vars that only the owner can add (§6). The private-key deny stays as it is.
5. **Fixed what the work uncovered, rather than noting it.**
   - **File-tool gap:** the scope hook stayed silent about paths outside the project, claiming another hook owned them. It now asks, with a test for all four write tools.
   - **Overlap test gap:** the test that stops a static rule silently disabling the scope hook only recognised the `./path` spelling. It now reads every spelling, with a positive control.
   - **Local-scope test:** the shipped-scope test read your working copy, so your local approval scope turned the gate red. It now reads what git ships.
   - **Fragile venv:** the backend venv pointed at a shim in a *session temp folder*, so a reboot would have broken `make check`. The interpreter now lives in `.tools/python`, inside the project.
   - **Inflated denominator:** `prod_readiness.py` started counting 2,236 third-party files once those folders existed. It skips them again (130 files).
   - **Node drift:** the devcontainer installed Node 20 against 22 everywhere else. The alignment test read the wrong file. Both are fixed.
6. **Caught drift in the act.** Minutes after the project-only policy was written, a "don't ask again" had stored `Bash(ls /Users/<owner>/Documents)` in the local settings. That gave us the local-settings check.
7. **Locked it last.** The rule that stops the agent editing its own settings went in as the final step, after everything was tested. From then on only you can change the policy.

---

## 4. Verified live (2026-09-25)

| Asked the agent to… | Expected | Result |
|---|---|---|
| read a home-folder file from the shell (`head ~/.zshrc`) | refused by the sandbox | ✅ `Operation not permitted` |
| list a sibling folder (`ls ~/Documents`) | refused by the sandbox | ✅ `Operation not permitted` |
| read a project file, and git's identity | allowed | ✅ |
| read `~/.ssh/known_hosts` with the Read tool | denied | ✅ |
| `gh pr edit 24 --add-label guardrail-change` | denied | ✅ |
| `git commit --no-verify` | refused | ✅ (hook, with the deny rule behind it) |
| edit `.claude/settings.local.json` | denied | ✅ |
| run the guard tests, `make policy`, `make harness`, pre-commit | allowed, sandboxed | ✅ |
| `gh` and `git push` | allowed, outside the sandbox | ✅ |
| commit a change to `.claude/hooks/` | asks you (unsandboxed retry) | ✅ (before ADR-0020; now the owner commits it) |

**From a launched program** (`scripts/sandbox_probe.py`, 2026-09-25, before ADR-0020's files landed): 10/10. Home-folder writes, the user's Claude settings, `~/.ssh`, both GitHub logins (the personal one and the agent's token file), sibling projects and a *grandchild* process writing home were all refused. Project writes and PyPI worked, and `example.com` was refused at the proxy. Re-run it after every settings change. Run outside the sandbox, every "blocked" probe fails, which proves the probe can fail.

**After ADR-0020's files are applied**, check each of these in the new session:

| Probe | Expected |
|---|---|
| `backend/.venv/bin/python scripts/sandbox_probe.py` | 13/13, and `GH_CONFIG_DIR` shows the agent folder. The three tamper probes (`.claude/`, a git hook, `.git/config`) are refused |
| the Edit tool on `~/.claude/settings.json`, with an `old_string` that does not exist | denied by managed settings (not a prompt). The edit could not apply either way, so the probe is harmless |
| the Read tool on a file in a sibling project | denied (not a prompt), once the wall-off has run |
| `npm i left-pad` / `npx cowsay` | asks (the install hook); decline it |
| `npm ci` in `docs-site/` | silent |
| `gh auth status` | logged in from `gen6th-accord-agent-gh/hosts.yml` |
| `gh pr list` | works, as the repo-only token |
| `git push origin <existing branch>` | "Everything up-to-date" (proves write access) |
| `gh api repos/ajalcance/gen6th-accord/rulesets` | denied locally; the token has no Administration either |
| any command with `GH_CONFIG_DIR=` | refused by the hook |
| a request needing `dangerouslyDisableSandbox` | refused: no escape hatch |

The structure is also pinned by tests that fail by name if a rule is removed. Each new check was sabotaged once to prove it can fail (TA-021):
- `tests/guards/test_agent_policy.py`
- `tests/guards/test_approved_scope.py`
- `tests/guards/test_agent_local_settings.py`
- `tests/guards/test_runtime_alignment.py`
- `tests/guards/test_agent_prompt_budget.py`
- `tests/guards/test_agent_identity.py`

---

## 5. Living with it

- **An `Operation not permitted` error is the boundary working.** There is no retry outside the sandbox (ADR-0020). The agent says what it could not do, and you decide whether to do it in your own terminal. Never widen the sandbox to credentials or dotfiles.
- **Changing the policy** is yours: edit `.claude/settings.json` in your editor, then open a PR with the `guardrail-change` label.
- **When `make policy` flags the local file**, open `.claude/settings.local.json`, move anything you really want into the committed policy (reviewed), and delete the rest.
- **New machine or clone:** the one-time steps are in [`ONBOARDING.md`](../../ONBOARDING.md) §1d:
  - accept the trust dialog;
  - run `pre-commit install-hooks` once, in your own terminal;
  - give the agent its own repo-only GitHub token;
  - optionally, add a global gitignore entry for local settings.

## 6. Still open (registered in `docs/PLAN.md`)

- **The backend tests need Docker**, which the sandbox cannot reach. The agent leaves them to CI, which runs them on every backend PR; you can run `make backend` yourself. The devcontainer removes this.
- **The agent's token can add labels on GitHub** (probed 2026-09-25). Only the local deny rules stop it: `--add-label`/`--remove-label` anywhere, any label flag on `gh pr create` or `gh issue create`, `gh label`, label and GraphQL API calls. The separate machine account (Stage 8) is what makes this server-side.
- **File-tool reads outside the project** ask rather than being refused, until `blockReadsOutsideWorkingDirectories` works alongside `allowRead`. Sibling projects and other projects' memory are refused outright once the wall-off has run (Layer 5); the rest of the Mac still asks.
- **The devcontainer** is the stronger boundary. It needs Claude Code installed, the Anthropic API allow-listed, DNS restricted, no host-credential forwarding, and a repo-scoped token.
- **A separate machine account for the agent** (Stage 8 launch gate), so the identity that writes is not the identity that approves.

## 7. Reusing this in another repository

1. Server-side first: a branch ruleset with a required aggregate check, and a guard-integrity check that fails guard changes without an owner-only label.
2. Copy `.claude/settings.json` and `.claude/hooks/`, then list your own guard files in the scope hook's `CORE`.
3. Copy the tests named in §4, and run them before trusting anything.
4. Probe both sides of the sandbox live (§4): the docs and the implementation disagreed twice here.
5. Add the self-edit deny rules last.
