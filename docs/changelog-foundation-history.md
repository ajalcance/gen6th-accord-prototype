# Foundation changelog — retained Unreleased entries

### Added

- H2 internal fixture persistence: immutable PostgreSQL versions, membership/ownership
  checks, expected revisions, exact retries and atomic server events. Migration 0003 adds
  tenant policies and immutable-record triggers. Unsealed auditable events survive expiry.
  Scoped receipt inspection reports event/audit-entry presence without a verification claim.
  Durable-event sealing continues through Redis outage; concurrent sealers share a chain lock.
  Internal workspace backlog observations return pending counts/oldest time and record access.
  Owner reported 92 targeted persona/migration tests passing in 20.31s on 2026-10-02.
  No persona HTTP routes or UI integration; full gates and Zynth remain pending.

- H1 local AI Persona Passport preview: five connected screens, original fictional vector
  portraits, browser draft saving, simulated review/retry, scoped campaign acceptance and
  explicitly unsigned JSON export. Owner accepted the frontend; full-gate completion pending.
  Change requests/re-analysis withdraw prior fixture acceptance, incomplete drafts stay
  unreviewed, and creation supports native form submission and keyboard focus.

- AI Persona Passport prototype plan, premium UI/UX direction and fresh-chat handoff
  (ADR-0023), with a submission-scope notice, owner-reported correspondence and later
  publication review. Product features, cloud activation and source publication remain pending.

- Local-first development commands with a localhost-only Compose stack, dedicated ports,
  checkout-specific images/data, private generated configuration and fail-closed startup tests
  (ADR-0022). Owner gate/startup, migration success and HTTP readiness verified locally.

- A copyable Codex sandbox and permissions reference for adapting the proposed
  managed boundary to another repository with its own exact-path profile.
- Initial project scaffold from the `zynth-setup` template: backend skeleton, CI/CD + security
  gates, pre-commit hooks, and the docs-as-code system.
- Accord architecture: design at a glance, Addenda 01–03, retention schedule, and Zynth Auth
  requirements (`docs/architecture/`, `docs/requirements/`).
- ADR-0013 to ADR-0016, recording decisions D-01 to D-33.
- Roadmap with Stage 0 to Stage 9 (`docs/PLAN.md`).
- ADR-0017: primary GCP region is asia-southeast1 (Singapore).
- `trust/`: the Go module for the trust services:
  - its gate: go vet, golangci-lint with gofmt and gosec, govulncheck, race tests;
  - Semgrep rules for Go;
  - `GO-*` standards;
  - the canonical content digest (`trust/internal/digest`).

### Changed

- Cold-store retention counts deleted rows atomically under concurrent writes; internal
  receipt inspection refreshes database references after event expiry.
- Worker errors omit raw exception details; persona rejection-record failures emit a bounded
  request-UUID operational signal and propagate failure.

- `make check` includes the existing Go trust gate alongside backend, frontend and docs.

- Licence changed from Apache-2.0 to proprietary (all rights reserved).
- Every CI job runs on a pinned `ubuntu-24.04` runner instead of `ubuntu-latest`, which was due to
  move to Ubuntu 26 on 2026-10-19. A test refuses a moving runner label.
- The backend tests run on PostgreSQL 17, the production major version, instead of in-memory SQLite:
  - a throwaway container per session, pinned by digest, with a fresh database per test;
  - the migration test now also compares column types.

### Security

- Update frontend and docs-site to exact Next/eslint-config-next 16.3.8 and
  Vitest/@vitest/mocker 4.1.11 for GHSA-vcvr-r3jv-pc5j and GHSA-82fw-gwwq-j7x9.
  Manifests, regenerated locks, installed versions and owner gate/startup verified locally;
  PR/CI review remains pending and no audit or cooldown control is weakened.
- Document an owner-run npm 11.16.0 resolver recovery in the ignored project cache for
  the bundled npm 10.9.8 peer-loader crash; installation and lock regeneration verified.

- Add a reviewed Codex companion policy with a sealed default, an exact-path project
  profile, root-owned managed hook source, policy fault tests and a live sandbox probe
  (ADR-0021). Owner installation and live verification remain pending; Claude Code's
  policy is retained.

- Nothing the agent launches can write `.claude/`, git hooks or `.git/config`. A launched program
  could previously write the owner's approval-scope file. Also:
  - setting a GitHub token variable is refused by static rules as well as by the hook;
  - `scripts/wall_off_siblings.py` refuses the agent's file tools on sibling projects;
  - `docs/runbooks/managed-settings.json` denies every self-edit machine-wide.

  These were adopted from zynth-auth.
- Every package install by the agent asks the owner, whatever the package manager or spelling.
  A new hook, `ask_on_install.py`, parses the command. Eleven install forms had run silently
  past rules that matched only the text `npm install` and `pip install`. `npx` can no longer
  fetch a missing package.
- The agent can no longer apply a label when it creates a pull request or an issue, whatever
  the label or flag form, and GraphQL calls are denied. Its token can label on GitHub, so the
  local rules are the whole label control. Five silent paths are closed, including
  `gh pr create -l guardrail-change` and `--label sensitive-change-approved`.
- The agent reaches GitHub with its own fine-grained token for this repository only, not the
  owner's personal login (ADR-0020). It cannot read, print or switch the token. The shell
  sandbox has no escape hatch and refuses to run without the sandbox. Browser and desktop
  control are removed in this project. `scripts/sandbox_probe.py` checks the sandbox from a
  launched program.
- The agent's permission prompts are limited to what CI cannot see: leaving the project,
  outward actions that are hard to undo, its own authority, and outside code entering the
  machine. A new guard test resolves real commands through the policy to hold that line. The
  local push hook now blocks a push *to* `main` on any remote; it had missed
  `git push upstream main`, and it blocked branches merely named after `main`. The owner applies
  the policy files.
- The dependency audits now read the whole tree: `npm audit` includes dev dependencies in the
  frontend and the docs site, and `pip-audit` reads `requirements-dev.txt`. Three high advisories
  in npm build tooling (brace-expansion, browserslist, js-yaml) are fixed in both projects.
- A release now requires the tagged commit's own CI run on `main` to have completed green
  (REL-035). Ancestry of `main` proved only that the pull request passed, and a missing push run
  now denies the release.
- The docs site now publishes only `docs/public/`. Previously it would have published every file
  under `docs/`, including internal architecture and requirements.
- The docs site's public-only rule is now CI-enforced by a vitest harness (`docs-site/tests/`), run
  by `make docs-site` and the CI `docs` job. Writing it closed two loader escapes: a symlinked
  `.md` in `docs/public/` was published with its target's content, and a `..` slug could read
  outside `docs/public/`.
- CI now really scans for secrets. The previous CI scan ran gitleaks against the staging area of a
  clean checkout and read nothing. It is replaced by a scan over the commits of every PR and push,
  pinned by version and SHA-256, and proven on every run by canary tokens planted in every tracked
  directory (ADR-0018). `.gitleaks.toml` no longer exempts `docs/**/*.md` or `.env.example`, and
  inline allow comments and `.gitleaksignore` are disabled.
- CI lints its own configuration:
  - zizmor, at its strictest persona, audits the workflows;
  - hadolint, at threshold `info`, lints the Dockerfiles;
  - both tools are pinned and checksum-verified.

  The findings are fixed:
  - template injection in `ci.yml` and `release.yml`;
  - `read-all` and unused `id-token` permissions in Scorecard;
  - the Scorecard token is now scoped to an environment;
  - both images run as a numeric non-root user.
- The community Semgrep scan now blocks new findings and keeps a SARIF report. An explicit
  `.semgrepignore` brings the test suites into scope, which Semgrep's default list had skipped.
- The `ci-complete` aggregator refuses to pass when it inspected no gates.
- Linter ignores in Dockerfiles and workflows count as suppressions and need the owner's label.
- CI zizmor refuses to run offline, and every action pin carries its exact version (a `# v3`
  comment sat on a v4.0.3 SHA).
- The AI agent is confined to the project (ADR-0019):
  - its shell runs in the macOS sandbox (home directory unreadable, network allow-listed);
  - file-tool changes outside the project always ask;
  - it cannot apply labels, approve pull requests, bypass rulesets, or edit its own settings,
    git hooks or git config;
  - `make policy` fails when local agent settings widen the committed policy.
- The devcontainer installs Node 22, matching CI and the images (it was 20).
- The production-readiness register can now hold real entries: its guard tests set the register
  by syntax, not by a string replace that silently did nothing.
- Go suppressions (`//nolint`, `#nosec`, `// nosemgrep`) now need the owner's label, and a change
  to `trust/` needs the sensitive-path label.
- `dod-check` derives the top-level directories it requires documented, instead of listing five.
- `prod_readiness` and `dod-check` no longer scan nested repositories, such as agent worktrees
  inside the project, as this project's source.
- The CI scanner manifest is a hash-locked lock of all 80 packages, not four top-level pins.
  CI installs it with `--require-hashes`, and a canary proves on every run that pip refuses a
  tampered lock. `check_pins` rejects lock lines with no provenance.
- A pull request that changes any of the following now needs the owner's `guardrail-change` label:
  - the agent's own policy (`.claude/`, `CLAUDE.md`, `AGENTS.md`);
  - the `Makefile` gate list;
  - the guard fault tests;
  - the harness lint config;
  - the devcontainer firewall.
