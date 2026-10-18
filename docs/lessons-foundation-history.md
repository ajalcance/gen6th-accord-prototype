# Earlier lessons — 2026-09-23 through 2026-10-01

Moved intact from [LESSONS](LESSONS.md) to preserve the append-only history within the file cap.

## 2026-10-01 — Request changes must withdraw the prior fixture decision

Review/campaign change requests and a restarted analysis previously left campaign acceptance
visible. Centralized fixture decisions now clear review, confirmation, acceptance and the
verification message together; a new review needs fresh campaign confirmation. Required
creation fields are checked again at review, including sidebar navigation. Native form
submission, selected filter semantics and focus movement are covered by regression tests.
All 26 frontend tests and the production build pass; browser/mobile inspection remains
unavailable because the browser runtime exits. This does not establish a backend approval.

## 2026-10-01 — Fixture approvals must reset with the reviewed draft

- H1 keeps browser interactions explicitly separate from real analysis, authorization and
  signing. Changing creation fields invalidates demo review, campaign acceptance and scan state.
- Journey tests caught stale campaign confirmation; a new review now requires a fresh click.
- The sandbox refused the loopback preview bind with EPERM. Keep that boundary; provide an
  owner-run preview rather than retrying outside it. A compiled build is not visual QA.
- Fresh full checks passed 776 guard tests (18 skipped), policy/harness and backend static
  checks, then stopped at pip-audit bootstrap. This is incomplete full-gate evidence.

## 2026-10-01 — A focused persona prototype preserves honest assurance

- The owner selected AI Persona Passport for the hackathon, with premium UI across the
  whole workflow (ADR-0023). Treat the roadmap subset as planned until it runs end to end.
- A registration ID, image similarity result and platform signature establish different
  things; none automatically establishes originality, IP ownership or claimant passkey assurance.
- Record the exact submitted materials and correspondence before publication. A rights
  notice needs organizer acknowledgment for the intended boundary; making a repository
  private later does not retrieve public forks or cancel surviving permissions.
- Six months is measured from confirmed event conclusion for the publication review,
  not from this planning session. Recheck obligations and obtain an owner decision then.
- This planning update passed policy/documentation checks and guard tests, but the full
  gate stopped at pip-audit's temporary-environment bootstrap. Record the actual stop;
  a prior owner gate is not fresh full verification of a changed checkout.

## 2026-10-01 — Owner evidence closes the local runtime verification gap

- Scoped npm 11.16.0 resolved the upgrade; both manifests, locks and installed copies now
  agree. The fail-fast owner sequence reached startup after the full gate. Existing npm in
  the Node 22 Docker image also completed `npm ci` against the new frontend lock.
- Successful migrations, readiness and HTTP probes establish the local scaffold's startup.
  Docs ready on its loopback port completes the local command sequence. This evidence does
  not activate managed agent policy, prove product journeys or replace required PR/CI review.

## 2026-10-01 — Installed dependencies are not lockfile evidence

- The owner's full gate passed backend and Go, then correctly refused a critical Next.js
  advisory. Fix requested versions and regenerate actual lockfiles; never disable the audit
  or use a forced automatic major upgrade to get past it.
- Vitest was installed as 5.0.1 while both projects locked 3.2.7. Passing tests on that
  installed tree does not prove a clean checkout will pass. Reinstall from regenerated locks.
- Next/eslint-config-next 16.3.8 and the planned Vitest 4.1.11 are requested exactly;
  lock resolution, audits and compatibility tests remain owner verification.
- Lockfile-only resolution still triggered the known crash on npm 10.9.8. Its installed
  Arborist lacks the upstream detached-node fix (npm/cli#8448). A pinned, project-local npm
  11.16.0 resolver is the proposed recovery; its success needs an owner run. Preserve locks
  and peer validation rather than deleting evidence or changing the tool's source.

## 2026-10-01 — Local stacks need explicit isolation, not just different URLs

- Compose normally appends ports, but custom replacement tags fail the existing YAML guard.
  A standalone local config with a fault-tested production-parity check avoids both hazards;
  inspect its resolved model before startup (ADR-0022). Keep the YAML guard intact.
- A free-port inventory is a snapshot. Recheck IPv4 and IPv6 and refuse ambiguity; never
  kill another project's process. Only this checkout's known Docker bindings get exemptions.
- Preserve local passwords alongside persistent volumes; regenerating a file does not
  update PostgreSQL's existing password. Keep live Docker proof distinct from fault tests.

## 2026-09-29 — A portable policy needs a single managed source

- **A copied repository file is documentation, not enforcement.** Codex's managed
  requirements live once per Mac under `/etc/codex/`. Reuse means adding a reviewed,
  exact-path profile there, then probing it live for each project. The copyable
  parameters are in `runbooks/codex-sandbox-template.md`.
- **Keep shared limits and project scope separate.** The sealed default, disabled
  external surfaces and managed hook apply across the Mac. Each repository supplies
  its own path, credential denials, agent contract, CI and branch controls.

## 2026-09-29 — A second agent needs a separate machine policy

- **A shared working contract is not a shared sandbox.** Codex reads `AGENTS.md`, but
  Claude's `.claude/settings.json` does not constrain it. The companion policy uses
  owner-installed managed requirements; both clients keep their own settings (ADR-0021).
- **Do not select an undefined profile in a PR.** Before the Mac-wide requirements are
  installed, a project `default_permissions` referring to a managed-only profile prevents
  Codex from loading configuration. Keep the checkout usable and select the profile after install.
- **Prove the installed boundary.** A repository test can pin proposed bytes, while
  only a Terminal probe can show that the Mac enforces home, policy, Git and network
  denials. Mark that proof pending until the owner runs it.

## 2026-09-26 — Borrowing another repo's hardening starts with probing your own

- **Probe before comparing.** Before judging zynth-auth's notes against this repository, a launched program tried each tamper path. `.claude/settings.json`, `.claude/hooks/`, `.git/hooks/` and `.git/config` were refused, but by Claude Code's defaults, not by our policy. The rest of `.claude/` was writable, **including the owner's approval-scope file**. The comparison would have missed that if it had only read the settings.
- **A probe must not be able to do the damage it tests for.** The probe's write test creates a file and then deletes it. Aimed at an existing file that the boundary failed to protect, it would have deleted the owner's scopes. The tamper probes create new files only, and `.git/config` is opened for append and never written.
- **A static rule beside a hook that fails open.** `block_dangerous_bash.py` lets a command through if it hits an error of its own, so the rules against switching the GitHub identity now also exist as deny rules. The mutation pass then removed three rules that guarded variables which are never set. A rule with nothing to protect is clutter.
- **Attribute what you borrow correctly.** The first reply credited zynth-auth's ideas to ZynthQ, carrying over the name of an earlier guide. The owner caught it. Check the document's own first line.
- **Fix the as-built page when you notice it is wrong.** `scripts/sandbox_probe.py` (#43) was never listed in `current-state.md`; `dod-check` checks directories and modules, not scripts. It is listed now.

## 2026-09-26 — An install rule written as text cannot see an alias

- **The gap was found by nearly using it.** Preparing the vitest move, the natural command was `npm i -D vitest@4.1.11`. Resolving it against the policy showed it ran silently. So did ten other install spellings, and `backend/.venv/bin/pip3 install` was explicitly *allowed* by the project-tools rule. A rule that matches `npm install` protects that exact text and nothing else.
- **Parse the command, don't match its text.** npm accepts eleven spellings of `install`, and other managers add their own verbs. The hook finds each program and its verb through shlex, separators, wrappers and `sh -c`. It asks on the install set, and also on anything it cannot parse or any error of its own.
- **A clause that no mutation can kill is either untested or unneeded; find out which.** The `-p`/`--package` clause survived because the spaced form puts the package first among positionals, where the main check already sees it. Only `--package=x` hides it. That form got a test, and the redundant half was removed.
- **A mutation that never ran proves nothing.** One mutation target was mis-escaped and silently matched nothing; the script reported it as "found 0 times" rather than as a pass. Fixed, and it was killed.

## 2026-09-25 — A runner label is a dependency too

- **`ubuntu-latest` is a floating version of everything under the gates.** GitHub announced the move to Ubuntu 26 only as a job annotation, on every run. `test_runtime_alignment.py` pinned Python, Node and PostgreSQL, but not the machine they run on. All 13 jobs now run on `ubuntu-24.04`, and the same test refuses any `-latest`.
- **A fine-grained token cannot read check runs.** `gh pr checks` and job annotations answer 403 under the agent's token, because no fine-grained permission covers `checks:read`. `gh run list/view/watch` read the same results through Actions.
- **`--no-track` branches have no upstream.** The owner's bare `git push` failed on one. Every push command given to the owner now names the branch.

## 2026-09-25 — A deny list that names labels misses the ones it forgot

- **Probe the server before trusting the client.** The owner ran the agent's token against the labels API: 200. Fine-grained "Pull requests: write" includes labelling, and nothing can remove it. Every local label rule became load-bearing at once.
- **Then audit the local rules against every way in.** Resolving label commands through the committed policy found five that ran silently:
  - `gh pr create -l guardrail-change`: the short flag slipped past `*--label*`;
  - `--label` with `sensitive-change-approved`, `no-tests-needed` or `no-changelog`: the rules named only `guardrail-change` and `allow-*`;
  - `gh api graphql`, which only asked.
- **Deny the verb, not the value.** The fix refuses any label flag on the two commands that can set one at creation. The two rules that named labels were then provably redundant, and the mutation pass showed it, so they are gone.

## 2026-09-25 — The sandbox held; the identity behind the excluded tools did not (ADR-0020)

- **Check what an excluded command runs as.** Every sandbox probe passed, including a grandchild process. But `gh` and `git push` are excluded from the sandbox, and they used the owner's personal login. A Read deny on `~/.config/gh` stopped the agent reading the file, not the unsandboxed `gh` using it. git's credential helper was `gh auth git-credential`, so one token setting covers both.
- **Probe from a launched program, not only a typed command.** Hooks and rules read what the agent types; a test runner or a poisoned dependency types nothing. `scripts/sandbox_probe.py` now checks every boundary from a child and a grandchild process.
- **A missing credential folder should mean no access.** The token path is committed. On any other machine the folder does not exist, so `gh` reports "not logged in" instead of falling back to a personal login.
- **CI caught three defects in the probe itself.**
  - Three `# noqa` markers suppressed rules the harness linter never selects, so they were pure noise, and the meta-guard counted them.
  - `urllib` was given a URL from a variable, and urllib also reads `file://`.
  - The catch-all `except` would have scored a crash in the probe as a refusal: a PASS for the wrong reason (rule 5).

  The probe now asks the sandbox's proxy for a tunnel over a plain socket, and counts only OS errors as "blocked".
- **Borrow the parts that are stronger, keep the parts that already are.** The ZynthQ template brought the repo-only token, the closed escape hatch, `failIfUnavailable`, and removing browser and desktop control. It also brought wildcard hosts, home-folder cache writes and local-only env settings. Here those would have been weaker, so they were left out.

## 2026-09-25 — Most prompts were the agent's habits, not the policy

- **Count where the prompts came from before trimming rules.** Of about a dozen prompts in one session, most came from the agent: scratch files outside the project, retries outside the sandbox, branch switches across a `.claude/` change, and `gh api` where an allowed command existed. Trimming rules alone would have left most of them. The habits are now in `CLAUDE.md` §6.
- **A prompt that repeats CI is a cost, not a control.** It stalls work while the owner is away and trains the click that approves the prompt that matters. The policy keeps prompts only where CI cannot see the risk. A test resolves real commands through deny, then ask, then allow, instead of checking that a rule string exists.
- **Model the sandbox too.** The first version of that test said a plain `rm` would prompt. It does not: sandboxed commands are auto-allowed, and only `gh`, which runs outside the sandbox, prompts when unlisted.
- **The push hook had no tests, a false block and a gap.** It matched `main` as a word anywhere, so a branch named `…-green-main` could not be pushed. It also required the remote to be `origin`, so `git push upstream main` passed. The proposed hook matches the target ref, on any remote. Tests cover both directions, and they fail on the current hook.
- **Test a policy the agent cannot write in a copy it can.** The drafts were checked in `.cache/pp/`, a throwaway tree of the guard tests, hooks and proposed settings. The mutation pass there found 21 rules no test exercised. Each now has an example command.

## 2026-09-25 — A comment named two controls that did not exist

- **The justification for a narrower gate is a claim to verify.** `npm audit --omit=dev` came with a comment: dev tooling was covered by Dependabot and a daily self-test. Dependabot alerts were off for the repository, and no workflow runs on a schedule except Scorecard. Three high advisories sat in both npm trees. Rule 9 in its purest form: the comment told the next reader to leave the hole.
- **Read the install log, not only the gate's verdict.** `npm ci` printed "5 vulnerabilities (2 moderate, 3 high)" in a green job. The gate below it audited a subset and reported 0.
- **Keep the cooldown when fixing advisories.** `npm audit fix --before=<7 days ago>` resolved each fix to a version older than the cooldown. The lockfile diff was 30 lines per project, all of them the advisory packages and browserslist's data files.
- **Check the wider population before widening.** `pip-audit` over the dev requirements was clean, so the backend gate could widen without breaking anything. The scanner lock is the remaining unaudited population.

## 2026-09-25 — A merge with no push run, and a release that would not have noticed

- **GitHub can deliver no push run at all.** The merge of #31 has zero workflow runs of any kind. There was no path filter, no skip marker and no failure. The event simply never produced a run. Rule 18 says to verify main by SHA. That check lived in a person's habit, and the release workflow checked only ancestry, so a tag on that commit would have been signed.
- **Ancestry proves the pull request, not the branch.** The release preflight now requires the tagged commit's latest CI push run on `main` to be completed and green. It re-checks every run the API returns for commit, event and branch rather than trusting the query filters. Nine mutations each failed their own test, and the live API refused `ed97f14` by name.
- **A sandboxed `gh` fails closed, not open.** Inside the sandbox, `gh` cannot read its config, and the new check reported "could not read the CI runs". That is the intended failure. The live proof needed one unsandboxed run.
- **Switching branches across a PR that touches `.claude/hooks/` needs an unsandboxed run.** The sandbox refused to rewrite the hook file mid-checkout, so git stopped halfway: HEAD had not moved, but the index and some files already matched the target. Nothing was lost, because the branch was pushed. To bring such a branch up to date without a prompt, build the merge with git plumbing: merge-tree, a temporary index, then commit-tree. The checkout is never switched.

## 2026-09-25 — Adding a language exposes every list that assumed the old ones

- **Each list that named the existing languages missed the new one.** Go reached the suppression ratchet, the top-level directory check and the standards prefixes, and all three had hand-written the languages or directories they knew:
  - the ratchet scanned `.py/.ts/.js` and matched only `# nosemgrep`, so `//nolint`, `#nosec` and `// nosemgrep` in the signing code would have passed with no label;
  - `dod-check` listed five top-level directories and reported "OK" with `trust/` undocumented;
  - the standards test kept a copy of the prefix list the guard accepts.

  All three now derive from the source, and each was proven by sabotage.
- **"0 findings" from Semgrep on 0 files.** The Go-rule probe sat in gitignored `.cache/`, and Semgrep scans only tracked files by default. It reported success having read nothing. With `--no-git-ignore` it found all six planted defects.
- **A cooldown applies to CI tools too.** golangci-lint v2.14.0 was a day old; v2.13.2 is pinned instead, with its published checksum.
- **A careless edit split a Semgrep rule.** Inserting the Go rules after a pattern that was not the rule's last one cut the JavaScript rule in two, and YAML parsing caught it. Check a rules-file diff is purely additive.
- **A rule id read as an exemption.** The meta-guard's exemption check matches the word `skip` in scanner config. It flagged the new detection rule `sec-go-tls-skip-verify` as a net new exemption. The id is now `sec-go-tls-insecure-verify`, and the rule is unchanged. The check failing closed on a false positive is the right default. Asking the owner for `allow-exemptions` would have recorded an exemption that does not exist.
- **The `trust` job passed on its first GitHub run.** golangci-lint 2.13.2, gosec, govulncheck and the race tests ran on Linux with Go 1.27.1, as they had locally.

## 2026-09-25 — Docs-site test harness

- **An allowlist of a directory is not an allowlist of files.** `docs/public/` was the only root, but the loader still published a symlinked `.md` inside it with the target's content, and `readDoc` followed `..`. Neither showed in the build's route list, which listed only what existed. A fixture tree that plants each escape found both on its first run. The loader now refuses symlinks and any slug segment that is not a plain name, and checks the real path stays inside the root.
- **Run the real module against a fixture by moving what it already reads.** The loader derives its root from `process.cwd()`. The tests spy on `process.cwd()` and re-import the module, so no test-only switch exists in production code (TA-011).
- **The negative test passed when the site published nothing.** Sabotaging the root to a missing directory left "publishes no internal document" green. That is why the denominator test and the "publishes every file in `docs/public/`" test exist (TA-010). Each safeguard was sabotaged once and failed by name (TA-021): a widened root failed 6 tests, and dropping the symlink rule, the plain-name rule, the real-path check or `lstat` each failed its own test.
- **A security fix can widen what the bundler ships.** Reading a computed path made Turbopack warn that it would trace the whole project into the server build, internal docs included. The read stays a `path.join` under `DOCS_DIR`, so the bundler can see its scope. The tests cannot see this, so checking the build output is registered in PLAN.
- **Check the age of the whole tree, not just the package you asked for.** vitest 3.2.7 is 81 days old, but its tree pulled `rollup` 4.63.5, published the day before. `npm install --before=<date>` resolved every new entry from before the 7-day cooldown; the youngest is now 10 days old.
- **No `--if-present` on a gate that must exist.** The frontend runs `npm test --if-present`. For the docs site that would pass if the test script were deleted, so `make docs-site` and CI run a plain `npm test`.

## 2026-09-25 — A silent replace, and a second agent's worktree

- **`str.replace` is a silent no-op when its target is absent.** The prod-readiness fixtures replaced the literal *empty* register. With a real entry, nothing matched, every fixture inherited the real register, and six tests failed for a reason none of them named. `set_register()` now splices by syntax and refuses if it cannot find the register exactly once. The release-preflight fixtures had the same flaw.
- **Prove the fix in the state that broke.** A real register entry and its marker were put in the repository and the whole guard suite run: 502 passed. Then they were removed.
- **Running two agents found a defect one agent never would.** Claude Code places agent worktrees in `.claude/worktrees/`, inside the project. `prod_readiness` walked into one, doubling its count and flagging the copy's markers, and `dod-check` failed on a README in the worktree's `node_modules`. Both now skip any directory with its own `.git`. Tests prove both directions: a worktree is skipped, an ordinary subdirectory is not.
- **Match skip lists against the relative path.** `prod_readiness` compared names against the absolute path, so a project living under a folder called `build` would have skipped every file.

## 2026-09-25 — Tests on PostgreSQL

- **The migration test could not see type drift on SQLite.** Its own docstring said so. On PostgreSQL it now compares column types. Widening `audit_log.event_id` without a migration was caught by name (`VARCHAR(32) → String(40)`).
- **A convenience image can carry the most privilege.** Testcontainers' Ryuk reaper is pulled by a movable tag and handed the Docker socket. It is off; cleanup is the fixture's job.
- **Put an image pin where the update bot can see it.** The test PostgreSQL is pinned in a one-line Dockerfile that is never built. That lets Dependabot refresh the digest and hadolint lint it. The Dependabot coverage test then *demanded* an entry for it, but only once the file was tracked: a test that reads `git ls-files` passes on an untracked file.
- **"All dots" is not a count.** `-q` in both `pyproject.toml` and the command hid pytest's summary line, so CI never printed how many backend tests ran (TA-013). The config's `-q` is gone and CI now prints "N passed". A test also asserts the engine is the pinned PostgreSQL major, so a fixture that quietly fell back to anything else fails by name.
- **Docker is outside the sandbox.** The database tests reach the Docker socket, so locally they run with one approval per run, or against `ACCORD_TEST_DATABASE_URL`. CI runs them on every backend PR.

## 2026-09-25 — A pinned manifest was not a locked one

- **Pinning the top level pins the top level.** `requirements-ci.txt` pinned four tools, and as a constraints file it let their 76 dependencies float. It is now a hashed lock generated from `requirements-ci.in`, installed with `--require-hashes`.
- **Trust the lock only after watching it refuse.** Whether pip enforces hashes through a *constraints* file could not be tested in the local sandbox, so CI proves it on every run. It moves one package to another version, keeps the old hashes, and requires pip to refuse and to name hashes. A refusal for any other reason proves nothing and fails the step.
- **Sabotage the input, not only the code.** Adding `evilpkg==1.0` to the real lock showed `check_pins` printing OK: its "both directions" check only examined entries annotated with the input, and this one named nothing. Every locked entry must now carry `# via` provenance naming the input or a locked package. A forged `# via` naming a real package is still possible; the owner's label on the lock is that backstop.
- **The private-key deny also hides public CA bundles.** Inside the sandbox, `Read(./**/*.pem)` breaks pip wherever certifi's `cacert.pem` is read or replaced. That is registered as an owner decision in PLAN, not worked around.

## 2026-09-25 — The agent's policy could change at the pull request without a label

- **Locking a file in the session is half a lock.** After ADR-0019 the agent could not edit its settings. But the meta-guard's guard-file list had never included `.claude/`, `CLAUDE.md`, `AGENTS.md`, the `Makefile` (the one list of gates CI runs) or `tests/guards/`. A pull request could change any of them without the owner's label. The keystroke prompt and the PR gate are two different controls; check both.
- **A test's docstring said "both" and tested one.** The meta-guard's self-referential test claimed its own fault test was a guard file. It was not, and the test only checked the script. It now checks both, and each new pattern was removed once to watch its test fail.
- **The reconciliation population missed what it most needed.** Its hand-written list had no `.claude/` path, so it could not notice the gap above. It also missed `.semgrepignore`, which needed a label at the PR but raised no keystroke prompt. The population grew, and a new test requires every consequential path to reach the label gate, not just a prompt.
- **A settings reload briefly turned the sandbox off.** When `gh pr merge` fast-forwarded the checkout and rewrote `.claude/settings.json`, the harness reported the sandbox disabled for a moment. Three read-only commands ran unsandboxed before it came back. Nothing changed in the committed policy. Treat a checkout that rewrites the agent's settings as a moment when the local controls are not in force; CI and the ruleset are what hold then.

## 2026-09-25 — The agent had machine-wide access; now it has the project (ADR-0019)

- **"Confined to the project" meant Bash writes only.** The file tools had no such rule, and the scope hook stayed silent outside the project, citing a Bash-only hook that never sees a file tool. Reads, the network and the shell were unconfined. Check a boundary against every tool that can cross it, not the one it was written for.
- **The docs' own example did not work.** Sandbox `allowRead: ["."]` left the project unreadable to every command; `./` works. `blockReadsOutsideWorkingDirectories` overrides every `allowRead`, so git lost its identity and commits failed. Each was found only by probing both sides of the boundary live. The final shape is asserted by tests.
- **A rule anchored at the start of a command is defeated by a path in front.** `Bash(pip install *)` did not stop `backend/.venv/bin/python -m pip install`. Match the distinctive token anywhere: `Bash(*pip install*)`.
- **A secret-deny also hides public files from the sandbox.** Read-deny rules feed the shell sandbox, so `Read(./**/*.pem)` hid certifi's CA bundle, and pip-audit could not reach PyPI (macOS system trust is also unreachable under Seatbelt). The fix is the OS bundle via `PIP_CERT` and `REQUESTS_CA_BUNDLE` (`/etc/ssl/cert.pem`), never a narrower private-key deny.
- **A gitignored file drifts by clicks.** Minutes after the project-only policy was written, a "don't ask again" had stored a standing read of `~/Documents` in `settings.local.json`. `make policy` now fails on any local entry that widens the policy.
- **The venv pointed into a session temp folder.** On generation day it was built through a shim in the session scratchpad, so a reboot would have broken `make check`. The interpreter now lives in `.tools/python`, and tool caches in `.cache/`, both inside the project and readable under the sandbox.
- **An alignment test that reads one file per component misses a second source.** The devcontainer installs Node through a `devcontainer.json` feature, not its Dockerfile, so it sat on Node 20 against 22 everywhere else. The test now reads both.
- **Adopting a reference setup can weaken yours.** Zynth's guard-path `ask` rules cover two of the four write tools, and here they would have silently voided the scope hook. Reconcile a borrowed policy against your own tests before adopting it.

## 2026-09-25 — Linters found real defects in the CI config itself

- **zizmor found template injection in our own workflows.** `${{ github.base_ref }}` was expanded inside `run:` scripts in `ci.yml`, and cosign steps did the same with step outputs in `release.yml`. The fix is always the same: pass values through `env:` and reference `$VAR`.
- **Never write an expression inside a `run:` comment.** A literal expression in a shell comment is still evaluated by Actions. zizmor caught the one I wrote before it could break the job.
- **Exceptions are reviewed, in place, with a reason.** Two credentialed checkouts (zizmor `artipacked`) and the devcontainer's unpinned apt packages (hadolint DL3008) are inline ignores with a written reason. The suppression ratchet now counts hadolint and zizmor ignores, so each one needs the owner's `allow-suppressions` label.
- **Triage before making a scan blocking.** Semgrep community rules over the whole repository: 141 rules, 176 files, 0 findings. A diff-aware gate hides nothing that already existed.
- **"Suppressed" is a count of findings you did not read.** zizmor's default persona hid 18 findings: another template injection (the `ci-complete` aggregator), `read-all` permissions and an unused `id-token: write` in Scorecard, undocumented permissions, unnamed jobs, a missing concurrency limit, and a PAT readable repository-wide. All are fixed, and CI now runs the strictest persona (`auditor`).
- **A tool's default ignore list is an unreviewed exemption.** Semgrep's built-in list skipped 32 tracked files, including every test suite. An explicit `.semgrepignore` (generated trees only) brought them into scope. It immediately found two `exec()` calls under `# noqa` and two recursive deletes in the template's own guard tests; both were fixed with narrower code, not suppressions.
- **My local "no findings" was an offline run; CI's was not.** Without a token, zizmor silently skips the audits that check pins against the network. CI had a token, and its first run failed:
  - `dorny/paths-filter` was pinned to the v4.0.3 SHA but commented `# v3` since the template shipped, so every reviewer read the wrong major version;
  - two version comments were unreadable because an ignore marker shared the comment.

  Every pin now carries its exact `# vX.Y.Z`, checked offline by a test. The CI step refuses to run without a token, and fails if zizmor reports offline mode. The runbook says to run it online.
- **The aggregator had the audit's failure shape.** A loop over an empty result list printed "All gates green." It now counts the gates it inspected, refuses zero, and names each failed gate.
- **Approval scopes are local, not committed.** The template's own test requires the committed scope file to be empty (a repository must not ship pre-approvals). The owner's scope lives in the working tree only (`git update-index --skip-worktree`).

## 2026-09-24 — Pins and drift: my own control did less than I believed

- **The Dependabot ignore rule from #15 missed its first target.** The devcontainer tag `1-3.12-bookworm` makes Dependabot read 3.12 → 3.13 as a patch bump, so the minor-version ignore never applied, and #19 arrived anyway. The tag is now `3.12-bookworm`, and `test_runtime_alignment.py` fails on the drift itself rather than trusting the bot configuration to prevent it.
- **Derive coverage; do not hand-list it.** The docs path filter named two directories that never existed while the real one (`docs/public/`) went unbuilt. Dependabot coverage and the docs filter are now derived from the repository by tests, in both directions.
- **An agent reaching for `eval` and `# noqa` in a guard test is the failure mode the guards exist for.** Loading the meta-guard's regex through `importlib` did the same job with neither.
- **Command shape decides approval prompts.** `cd … && cmd`, pipes and `VAR=… cmd` defeat the permission allow-list, so every such command prompts the owner. The session already runs in the repository: use one plain command per call, and the Read tool for files.

## 2026-09-24 — The CI secret scan was blind (ADR-0018)

- **A green check proves the check ran, not that it checked anything.** CI ran the gitleaks pre-commit hook, whose command is `gitleaks protect --staged`. A CI checkout has nothing staged, so every run read nothing and passed. The replacement scans commits and plants a canary token in every tracked directory first; on its first run the canary refused, naming the six `docs/` directories that `.gitleaks.toml` exempted.
- **The fix had its own silent failure.** When the scanner could not be executed, the new guard crashed with exit 1, the code that means "secrets found". It now refuses with exit 2. Found only because each row of the pass/fail matrix was watched, and each refusal rule was sabotaged to confirm its test failed by name (TA-021).
- **A shebang cannot hold a path with a space.** This repo lives under `Software Applications/`, so a test stub using `#!{sys.executable}` could not be executed. Stubs use `#!/usr/bin/env python3`.
- **Bot PRs: `@dependabot recreate`, never "update branch".** Updating a Dependabot branch from the owner's account makes its commits unattributed, and the ruleset (`require_extra_approval_for_unattributed_changes`) then blocks the merge.

## 2026-09-24 — Dependabot proposed new runtime lines

- **Pin runtime lines, keep refreshing digests.** On day one Dependabot opened PRs moving the frontend image to Node 25 and the devcontainer to Python 3.14. Both would split the toolchain: CI runs 3.12, and the Node gate fails on 23+. Both were closed with a reason. `dependabot.yml` now ignores major Node and major or minor Python bumps for base images while still refreshing their digests. A runtime upgrade is its own deliberate PR across the Dockerfiles, CI and the local toolchain.
- **ADRs are guard-defining files.** The meta-guard refuses a PR that adds an ADR unless the owner applies `guardrail-change`. That is intended: an ADR can change what the guards enforce, so the owner approves it. The agent must not apply that label itself.

## 2026-09-23 — Docs site publishes only docs/public/

- **Publish by allowlist, never by denylist.** The template's docs site rendered every Markdown file under `docs/`, which would have made the internal architecture, ADRs and Zynth requirements public on deploy. It now reads only `docs/public/`, so a new internal file stays private by default. Proof today is the `next build` route list; a docs-site test harness is a Stage 0 follow-up so the rule becomes CI-enforced.

## 2026-09-23 — Generating the repo from zynth-setup

- **Pin the toolchain before `copier copy --trust`.** On the founder's Mac, `python3` was 3.14 and `node` was 23. The template needs 3.12 and 22. A PATH shim (`python3` → `python3.12`, then `/opt/homebrew/opt/node@22/bin`) put them first, and generation and `make check` were green on the first run.
- **The docs site publishes all of `docs/`.** Internal architecture would go public on deploy. It is tracked in `PLAN.md` Stage 0 as a must-fix before `/docs` deploys.
- **The production-readiness register can't hold a real entry yet.** Its fault tests replace the literal empty-register string, so a real entry leaks into their sandbox and six guard tests fail. The entry was reverted rather than editing guard tests in the initial commit. Fixing the tests is a Stage 0 task, as its own owner-approved change (SEC-040).
- **The confine-to-project hook refuses file copies from outside the repo.** Even a read-only source counts. The architecture PDFs therefore stay outside the repo, and ADR-0013 names them. Add them by hand if they are wanted here; never weaken the hook to do it.
- **`.copier-answers.yml` still records `license: Apache-2.0`.** The licence was replaced after generation (ADR-0016). Expect a conflict on `LICENSE` if `copier update` is ever run; keep the proprietary text.

<!-- ## YYYY-MM-DD — <short title>
- **<lesson>** — what happened, what you learned, how to avoid/repeat it. -->

## 2026-10-01 — A scaffold principal and telemetry stream do not complete H2

- The existing HMAC principal is explicitly development scaffolding, not verified Zynth
  login or workspace authorization. Inspect the real provider before connecting persona writes.
- Fail-open telemetry is useful operationally but cannot guarantee a durable creation record.
  Commit version and event together; distinguish committed evidence from eventual audit sealing.
- Pure persona contract tests cover validation/immutability only. They do not prove database
  isolation, OIDC sessions or live event delivery; retain the full gate and integration tests.

## 2026-10-01 — Durable events need retention as well as atomic writes

Persona versions now commit with their server event and exact-retry receipt. Inspection
found the worker could expire an event before sealing an audit backlog; expiry now keeps
auditable server events until a matching audit entry exists. Versions retain identifiers
without preventing cold-store expiry. Membership must be rechecked even for exact retries.
Offline migration rendering passes; Docker access prevents database execution, so locks,
triggers, RLS and rollback tests remain pending rather than reported as proven controls.
Receipt inspection checks matching server records before exposing references. Redis outage
also blocked sealing durable PostgreSQL events; separate those concerns. Concurrent sealers
need a transaction advisory lock because an empty chain has no row to lock.
Actor references now match the database's 64-character limit. One immutable receipt per
version is enforced by uniqueness. Migration tests inspect protections installed by actual
DDL, since ordinary metadata comparison does not compare tenant policies or triggers.
Backlog observations use one aggregate snapshot, stay tenant-scoped and record their own
observation afterward. Counts explicitly exclude that subsequent event. An index supports
workspace filtering; registering a rule still does not implement a detection engine.
Receipt states now reject contradictory presence, incomplete audit references and ambiguous
timestamps. Distinguish a client's retry UUID from server-built record and observation IDs.
Retention now counts its deleted rows in one PostgreSQL statement: separate table counts
were vulnerable to concurrent inserts. Receipt inspection queries the database afresh so
an ORM identity-map entry cannot report an expired cold event as still present.

## 2026-10-02 — Keep owner-run evidence distinct from full-gate evidence

- The owner reported `92 passed in 20.31s` for the persona/migration PostgreSQL suite.
  Record the command and provenance; it clears targeted database execution uncertainty,
  but does not establish a green dependency audit, full gate or revision-bound CI result.
  The original five-hour build window elapsed; preserve the next slice for continuation.

## 2026-10-02 — A failed rejection record still needs a safe operational signal

If recording a denial itself fails, the exception arose inside the original error handler
and bypassed its normal failure log. Rejection recording now has a bounded request-UUID
log before propagating failure. Worker-loop errors report only the exception class, not raw
database details. Pure worker logging tests pass; the database rejection-fault test remains
pending owner/CI execution. No successful or durable rejection is claimed on database outage.
Semgrep's empty trust-anchor startup was resolved using the OS public CA bundle already
documented in the reviewed agent configuration. No guard or TLS verification changed.
Pip-audit still fails at bootstrap. Migration protection tests now exercise seeded migrated
tables directly, because model-created schemas do not prove migration policy enforcement.

## 2026-10-02 — Palette variants are not independent benchmark originals

- H1 uses one original SVG drawing with three color variants. A retrieval evaluation must
  split by source family to avoid measuring the same artwork on both sides as independent
  examples. The protocol records counts and failure cases; no model result is fabricated.

## 2026-10-02 — Bind campaign scope through tenant and version together

- Independent tenant/version foreign keys can still permit an asset from the wrong version.
  Campaign bindings now use composite references for the offer and fixture asset. Permission
  status also rechecks the exact latest review and server time; evidence presence is separate.

## 2026-10-02 — A historical receipt is not current approval

- Review retries return the immutable recorded decision after fresh authorization. Current
  permission must separately check the persona head and latest review; otherwise retrying an
  old request can revive approval withdrawn by an edit or a later change request.
