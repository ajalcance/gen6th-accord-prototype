# Onboarding — one-time setup for Gen6th Accord

Most of this project is green and hardened the moment it is generated. A few controls live in
**GitHub repo settings** rather than in files — by design, so an AI agent working in the repo
cannot edit them away (see [`docs/decisions/0004-agent-resistant-guardrails.md`](docs/decisions/0004-agent-resistant-guardrails.md)).
This is the short list of switches **you** flip once.

## 1. Push the repo to GitHub

```bash
gh repo create ajalcance/gen6th-accord --private --source . --push
```

## 1b. Develop in the sandbox (recommended for AI-assisted work)

Open the repo in the **`.devcontainer/`** (VS Code: *Reopen in Container*). It runs a **default-deny
egress firewall** (`.devcontainer/init-firewall.sh`) so code the agent writes/runs can only reach an
allow-list (GitHub, package registries, sigstore) — a buggy or prompt-injected dependency can't
exfiltrate. The firewall verifies itself at start and refuses to come up open (fail-closed). Widen
the allow-list in that script for hosts your project legitimately needs. **Never put production
credentials in the dev environment** — use throwaway/dev values in `.env`.

> **Not yet for the AI agent itself (2026-09-25).** The image has no Claude Code, the firewall does
> not allow the Anthropic API, and Dev Containers forward your host git credentials. Until the Stage 0
> devcontainer item fixes that, the agent runs on the host inside Claude Code's own sandbox (§1d).

## 1c. Local agent ergonomics — Claude Code hooks

`.claude/settings.json` wires three **session hooks** (they run automatically in Claude Code — no
install step):

- **Auto-format** — after the agent edits a `backend/` Python file, `ruff --fix` + `black` run on it
  (uses `backend/.venv`; skips silently if absent). Fails **open**.
- **Footgun blocker** — a `Bash` call that pushes directly to `main`, force-pushes a protected branch,
  uses `--no-verify`, or `rm -rf`s a dangerous root is blocked with an explanation.
- **Secret-write blocker** — writing a real `.env`, a `*.pem`/`*.key`, or a file containing a PRIVATE
  KEY block is blocked.

> **These are ergonomics, not security.** They shift the existing guards left for a tighter loop; they
> run only in Claude Code, on your machine. **CI, the branch ruleset, and pre-commit remain the
> fail-closed backstop** — the same rules are enforced server-side where an agent can't bypass them.

To disable, delete `.claude/settings.json` (or generate with `include_claude_hooks=false`). The
scripts live in `.claude/hooks/`.

## 1d. The agent is confined to this project (ADR-0019)

`.claude/settings.json` also sandboxes the agent's shell to this project, denies it every way to
approve its own work, and keeps tool caches in `.cache/`. The full account is in
[`docs/runbooks/agent-permissions.md`](docs/runbooks/agent-permissions.md). One-time steps on a new
machine or clone:

1. **Accept the workspace trust dialog** when Claude Code shows it. The project's allow rules take
   effect only after that.
2. **Install the pre-commit hook environments once, in your own terminal.** The sandbox forbids
   the `.git/config` writes that installation makes, and the agent has no way out of it
   (ADR-0020):

   ```bash
   backend/.venv/bin/pre-commit install-hooks
   ```
3. **Give the agent its own GitHub token** (ADR-0020). Without it, the agent's `gh` and
   `git push` report "not logged in", which is the safe default. Create a fine-grained token
   scoped to this repository only:
   - read and write: Contents, Pull requests, Workflows;
   - read only: Actions, Commit statuses, Issues, Dependabot alerts, Metadata;
   - nothing else.

   Store it in your own terminal, never through the agent:

   ```bash
   mkdir -p ~/.config/gen6th-accord-agent-gh && chmod 700 ~/.config/gen6th-accord-agent-gh && read -rs "AGENT_TOKEN?Paste the fine-grained token, then press Enter: " && printf '%s' "$AGENT_TOKEN" | GH_CONFIG_DIR=~/.config/gen6th-accord-agent-gh gh auth login --hostname github.com --git-protocol https --insecure-storage --with-token; unset AGENT_TOKEN
   ```

   The committed settings name `/Users/<owner>/...`. On another machine or user, change that
   path through a reviewed PR. `read -rs` keeps the token out of the clipboard and the shell
   history.
4. **Optional, recommended:** ignore local agent settings in every repository on this machine:

   ```bash
   mkdir -p ~/.config/git && printf '%s\n' '**/.claude/settings.local.json' '**/.claude/settings.local.json.bak*' >> ~/.config/git/ignore
   ```
5. **Wall off your other projects** from the agent's file tools. The script writes machine-local
   deny rules into `.claude/settings.local.json`; run it without `--apply` first to read them:

   ```bash
   python3 scripts/wall_off_siblings.py --apply
   ```

   Re-run it whenever you add a project next to this one.
6. **Optional, strongest:** install the machine-wide managed settings, so no agent in any project
   can edit its own settings (needs `sudo`). The file only denies; see
   `docs/runbooks/agent-permissions.md` Layer 5:

   ```bash
   sudo mkdir -p "/Library/Application Support/ClaudeCode" && sudo cp docs/runbooks/managed-settings.json "/Library/Application Support/ClaudeCode/managed-settings.json"
   ```

Only you can change the agent's settings: edit `.claude/settings.json` in your editor, then open a
pull request with the `guardrail-change` label. Prune `.claude/settings.local.json` by hand when
`make policy` says it widens the policy.

## 2. Apply the branch ruleset (required)

Makes passing CI + code-owner review a *repo setting*, not a file an agent can rewrite:

```bash
# prerequisites: gh AND jq (bootstrap-repo.sh exits if either is missing)
brew install jq               # or: sudo apt install jq

gh auth login                 # needs 'repo' scope + admin on this repo
./scripts/bootstrap-repo.sh   # applies every .github/rulesets/*.json (idempotent)
```

After the first PR runs CI once, the `ci-complete` check registers and becomes required. From then
on **nothing merges without green CI**, and `main` cannot be force-pushed or deleted.

> **Configured for a solo maintainer.** You answered *yes* to `solo_maintainer`, so code-owner
> review is **not** required. This is deliberate: GitHub forbids approving your own PR, so
> requiring it would block every guardrail change and force `gh pr merge --admin` as routine —
> producing no review *and* normalising `--admin` on exactly the changes that deserve most care.
> `.github/CODEOWNERS` is retained as **advisory** (it still auto-requests your review).
>
> **What this costs:** agent-resistance now rests entirely on CI being fail-closed and enforced in
> repo settings an agent cannot edit — the branch ruleset, `ci-complete`, and the CI meta-guard.
> If you add a second maintainer, re-run with `solo_maintainer=false`.

**Prove it fails closed (do this once).** Confirm the ruleset blocks a direct push to `main`:

```bash
git switch main && echo x >> README.md && git commit -am "test: direct push"
git push        # expect: GH013: Repository rule violations found for refs/heads/main
git reset --hard origin/main
```

If that push succeeds, the ruleset isn't active — fix it before trusting the repo.

## 3. Scorecard token — **required on a private repo**

The `Scorecard` workflow watches that the guardrails themselves don't erode over many PRs.

**On a private repository it cannot run at all without a token.** Scorecard's GraphQL queries are
not permitted to the default `GITHUB_TOKEN` on private repos, so it aborts on `ListCommits` before
writing `results.json` — the whole tool fails, not just one check. The workflow tolerates that
(warns rather than failing), but **guardrail monitoring is inactive until you add a token.**

A **fine-grained** PAT is *not* sufficient — Scorecard fails with `Resource not accessible by
personal access token`. Use a **classic** token with `repo` scope:

```bash
gh secret set SCORECARD_TOKEN --env scorecard   # classic PAT, `repo` scope — environment-scoped
```

> **Security trade-off, stated plainly.** A classic token cannot be scoped to a single repository:
> `repo` grants read **and write** to every private repo the account can reach. It lives in the
> `scorecard` **environment**, not in repository secrets, so only the Scorecard job can read it —
> no other workflow or job ever receives it. Use a short expiry (30 days) and rotate it. If that trade is
> unacceptable, leave the token unset — the workflow stays green and warns that monitoring is
> inactive.

On a **public** repo the default `GITHUB_TOKEN` suffices and no PAT is needed.

## 3b. Track your temporary stand-ins (`PROD-BLOCKER`)

Scaffolding a project means deliberate stubs: a placeholder auth check to unblock frontend work,
`CHANGE_ME` secrets in `.env`, a mutable image tag before the first real release. Each is fine
while building and unacceptable in production — and a plain `TODO` comment is how they get
forgotten. Mark them, and register them:

```python
# PROD-BLOCKER(auth-stub): dev-only bearer check; replace with real OIDC before launch
```

Then add a matching entry to the `BLOCKERS` tuple in `scripts/prod_readiness.py` (it ships
empty). `make dod-check` verifies the two agree **in both directions** — a marker with no
register entry fails, and a register entry whose marker is gone fails too, so the register can't
rot into a list of things fixed months ago.

It does **not** fail merely because blockers are open; that would be red for your entire build
phase and train you to ignore it. The release boundary is where it becomes strict:
`make release-preflight TAG=vX.Y.Z` runs it with `--strict`, so a release does not happen while
one is open.

## 4. Socket.dev — behavioural supply-chain analysis (recommended)

CVE scanners (`pip-audit` / `npm audit`) only know *disclosed* vulnerabilities. Socket flags a
dependency that *newly* runs install scripts or touches the network/filesystem — the poisoned-update
/ typosquat vector that has no CVE yet. Deps are already **fully pinned** (`scripts/check_pins.py`
gate) and installs are deterministic (`==` for Python, `npm ci` + lockfile integrity for JS), so a
version *bump* is always an explicit, code-owner-reviewed diff; Socket judges whether the new version
is *safe*.

1. Install the **[Socket GitHub App](https://github.com/apps/socket-security)** on your org/repo and
   set its policy to **block** (not warn).
2. Once it posts its first check, add **Socket Security** to the required checks — re-run
   `./scripts/bootstrap-repo.sh` after adding `{ "context": "Socket Security" }` to the
   `required_status_checks` in `.github/rulesets/main.json`, or add it in the branch-protection UI.

## 5. Signed deploys (cosign)

Nothing to configure for *signing*: `.github/workflows/release.yml` builds on a `v*` tag, signs each
image **keyless** via GitHub OIDC (no key to manage), and pushes to GHCR with the built-in
`GITHUB_TOKEN`. Signing is cosign-only by design — `deploy/verify.sh` verifies the cosign
signature, so a GitHub attestation (unavailable on some plans/visibilities) would only add a step
that could fail the release without strengthening the deploy gate. Two host-side steps:

- Install **cosign** on the deploy host (`deploy/verify.sh` uses it): <https://docs.sigstore.dev/cosign/system_config/installation>.
- Make the GHCR packages pullable by the host — they inherit repo visibility; for a private repo,
  `docker login ghcr.io` there with a `read:packages` token.

### Cutting a release

```bash
make release-preflight TAG=v0.1.0        # fail-closed; nothing is tagged if it objects
git tag -a v0.1.0 -m v0.1.0 && git push origin v0.1.0
```

The tag builds a **candidate**: each image built once, signed, an SBOM generated, and a signed
`release-evidence.json` naming every image by digest attached to the GitHub Release. Nothing is
promoted yet.

To promote, run the **Release** workflow manually with `promote_tag` and type the same tag into
`confirm`. It verifies the evidence signature, checks the evidence is for that tag, verifies each
image signature, points `:stable` at the same digests, and prints the exact
`BACKEND_IMAGE=…@sha256:…` lines for the host. It contains no build step, by design and by test.

Then follow `deploy/README.md` (**verify signatures → start the base stack**). Pin images by
`@sha256:` digest — never by tag.

> **Holding a release.** Open an issue and apply the `release-blocker` label (provisioned by
> `scripts/bootstrap-repo.sh`). While any such issue is open the preflight refuses, in CI and
> locally. A hold that cannot be read — no `gh`, a failed lookup — counts as active.

> **Release tags must be cut from the default branch.** Pushing a tag is an ordinary git
> operation — it is the one route to production that skips PR review, code-owner review and
> `ci-complete`. Without a guard, `git tag v9.9.9` on an unreviewed branch would produce a
> genuinely signed image that `deploy/verify.sh` accepts: a valid signature attesting
> to the wrong thing. The `guard` job in `release.yml` therefore refuses to build or sign any tag
> whose commit is not an ancestor of the default branch.

**Optional extra hardening — restrict who may push `v*` tags.** The `guard` job lives in a file an
agent could edit; a *tag ruleset* is repo settings, which it cannot reach (the ADR-0004 argument).
To require that only admins cut releases, add a ruleset targeting tags:

```bash
gh api -X POST repos/ajalcance/gen6th-accord/rulesets --input - <<'JSON'
{
  "name": "release-tags", "target": "tag", "enforcement": "active",
  "bypass_actors": [{ "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always" }],
  "conditions": { "ref_name": { "include": ["refs/tags/v*"], "exclude": [] } },
  "rules": [{ "type": "creation" }, { "type": "update" }, { "type": "deletion" }]
}
JSON
```

Confirm you can still tag afterwards (`actor_id: 5` is the repository **admin** role — adjust the
bypass list to whoever must be able to cut releases, or you will lock yourself out of releasing).
This is left as a documented opt-in rather than shipped in `.github/rulesets/`, because the correct
bypass actors differ per repo and a wrong value blocks all releases.
