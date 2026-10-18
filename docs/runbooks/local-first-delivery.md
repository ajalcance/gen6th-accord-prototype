# Local-first delivery on the owner's Mac

**Scope:** development tooling for the current scaffold (ADR-0022). No application server,
cloud account, domain or public deployment is required. Run Docker commands in your own
Mac Terminal. They operate only on this checkout's Compose project. Keep the agent sandbox.

## Verified local status — 2026-10-01

The owner's submitted output reached Docker startup and docs after the full gate in the
supplied fail-fast block. Images built, migrations exited 0, PostgreSQL/Redis/API were healthy,
all six long-lived services ran, and app/health probes returned 200. Docs started successfully.
Live inventory confirms all four listeners bound to 127.0.0.1 on 18660–18663.
Both manifests, generated locks and installed versions agree on Next/eslint-config-next
16.3.8 and Vitest/@vitest/mocker 4.1.11. Scoped npm 11.16.0 is installed and its recovery
sequence succeeded. The previous pending observations below describe earlier attempts.

Local scaffold startup is verified. Manual browser journeys and PR/CI review remain pending.
Changes are uncommitted. This does not activate managed agent policy or provision cloud services.
Keep the docs terminal running to keep docs available; `local-down` only stops Docker services.

## Ports and data

| Service | Address | Lifecycle |
| --- | --- | --- |
| App + proxied API | `http://127.0.0.1:18660` | `local-up` / `local-down` |
| Public docs | `http://127.0.0.1:18661` | `local-docs` / Ctrl+C |
| PostgreSQL 17 | `127.0.0.1:18662` | `local-up` / `local-down` |
| Redis 7 | `127.0.0.1:18663` | `local-up` / `local-down` |

These ports were absent from the Mac's listening-port inventory on 2026-10-01. That snapshot
does not reserve them. Each relevant start command probes both loopbacks again and refuses
occupied or ambiguous ports. An existing binding from this exact Compose project is allowed
for repeated core startup; another project's binding never receives that exemption. The
process must still successfully bind, closing the check/start race.

Caddy proxies `/health` and `/api/*` to the API, and other paths to the frontend. Only Caddy,
PostgreSQL and Redis publish host ports. API, worker and frontend stay inside the local network.

Generated secrets live in `.cache/local-stack/`, ignored by git. Do not paste that file or
`docker compose config` output into chat. Root `.env` is neither read nor replaced. Credentials
are random and development-only; the database URL must name the local `postgres` service.
Volumes, networks and image tags use the canonical checkout path's hash. Moving the checkout
needs a reviewed local-data migration; copied runtime files are refused. ADR-0041 now requires
an empty integration baseline and actual authored records; historical sample stores need
[read-only inventory and provenance review](creation-and-storage-preparation.md).
Never import a production dump. Shutdown preserves the database; no automated volume deletion exists.

## First startup

Docker Desktop must be running, with Compose >= 2.24.4. Python 3.12 and Node 22 remain the
repository baselines. Lockfile dependencies should already be installed. First builds require
image/package registry access; offline use assumes cached images and dependencies. No global
policy, Git hook or host certificate installer is added.

Run this block in **Mac Terminal**:

```bash
(
  set -euo pipefail
  cd "/path/to/gen6th-accord"
  export PATH="/opt/homebrew/opt/node@22/bin:$PWD/.tools/bin:$PATH"
  make local-init
  make local-doctor
  make local-up
  make local-status
)
```

Expected: `local-doctor: OK`, then `local-smoke: OK`; long-lived services running,
PostgreSQL/Redis/API healthy and `migrate` exited successfully. Open the app above. This proves
startup and basic reachability, not a complete product journey or worker event-processing
correctness. Report printed status lines; omit secrets and logs with request data. A refused
prerequisite is a failure, never a reason to loosen policy.

In a **second Mac Terminal tab**, start docs:

```bash
(
  set -euo pipefail
  cd "/path/to/gen6th-accord"
  export PATH="/opt/homebrew/opt/node@22/bin:$PATH"
  make local-docs
)
```

The existing site publishes only `docs/public/`. Ctrl+C stops it. `make local-down` stops only
this checkout's core stack and preserves its database. Do not delete runtime secrets while
keeping the volume: PostgreSQL does not change an existing password from a new env file.

## Daily work and PR preparation

1. Start feature branches from clean, synchronized `main`. Land this tooling in its own
   owner-reviewed PR; keep uncommitted setup changes out of the existing Codex security PR.
2. Rebuild after changes with `make local-up`, use the real app and run `make local-smoke`.
   The app uses production-style images; public docs use a separate development process.
3. Run `make check` with Node 22 selected. It now includes backend, Go trust, frontend, docs,
   fault tests and policy/harness gates. Go and the pinned local Go linters must be available.
   Backend tests use their own throwaway PostgreSQL, not the application database.
4. Before submitting, run pre-commit, `make secret-scan BASE=origin/main` over real commits,
   and PR declaration checks with the real base and PR body. These diff-based checks are
   distinct from `make check`. Record actual evidence; never skip a failed gate.
5. Open the PR when locally ready. Preserve PR and `main` CI and owner labels/review.
   Account billing failures still prevent merge/release readiness.
6. Rehearse interacting branches on a disposable integration branch when necessary. Record
   commits and rerun checks; submit separate feature PRs, never bypass protected `main`.

## Deferred work and verification boundary

Populated older-schema migration/rollback rehearsal, reconciled merged-tree evidence,
provider integration, cloud staging and digest-preserving promotion are not implemented by
these commands. Track them in `docs/PLAN.md`. Local HTTP on loopback cannot prove TLS,
Cloud Run IAM or the future identity/trust-service architecture.

Source tests and resolved Compose validation run inside the agent sandbox. Live container
startup, full database-backed checks and manual use require owner verification. Record actual
results in the PR before calling this setup operational.

### Verification recorded on 2026-10-01

- `make guard-tests policy harness`: 776 passed, 18 skipped; policy and harness green.
- New local setup/parity tests: 46 passed. Strict mypy: 3 source files passed.
- Existing public docs tests: 11 passed. Resolved Compose model validated using Compose 5.3.1,
  with secrets captured privately. Listening-port inventory still had no 18660–18663 listener.
- `make check` stopped at backend `pip-audit` temporary-tool installation. Separate frontend
  and trust gates stopped at registry/vulnerability endpoint DNS failures. These are failures,
  not clean audits. No dependency gate was skipped or weakened.
- Live Docker startup, database-backed full gate and browser rehearsal are pending owner action.
  Changes are local and uncommitted; they have not been added to the existing security PR.

### Owner follow-up on 2026-10-01

The owner's `make check` passed backend (52 tests, 82.81% coverage) and Go (including
vulnerability checks and race tests). Frontend audit then refused Next 16.3.5 (critical)
and the locked Vitest tree (moderate). Both manifests now request Next/eslint-config-next
16.3.8 and Vitest 4.1.11; the existing lockfiles still need npm to regenerate them.
Regenerate each lock with lifecycle scripts disabled, install using `npm ci`, then run
the complete gate before startup. Do not use a forced audit fix. Runtime verification
remains pending until that entire sequence passes.

- [Next advisory](https://github.com/advisories/GHSA-vcvr-r3jv-pc5j)
- [Next 16.3.8 security release](https://github.com/vercel/next.js/releases/tag/v16.3.8)
- [Vitest advisory](https://github.com/advisories/GHSA-82fw-gwwq-j7x9)

### npm resolver recovery

The owner lockfile-only install also crashed with `Cannot read properties of null (reading
'edgesOut')`. The selected Node 22 installation bundles npm 10.9.8; its Arborist peer loader
still dereferences `node.parent` without the upstream detached-node fix. Use a pinned npm
11.16.0 copy under ignored `.cache/npm-resolver/` for this recovery. It supports Node >=22.9;
the checked local runtime is 22.23.1. No global install, deletion of locks, forced resolution
or peer-dependency suppression is needed. The owner subsequently verified this recovery;
see the current status above.

Run the following in **Mac Terminal**:

```bash
(
  set -euo pipefail
  cd "/path/to/gen6th-accord"
  export PATH="/opt/homebrew/opt/node@22/bin:$PWD/.tools/bin:$PATH"
  npm install --prefix "$PWD/.cache/npm-resolver" --no-save --ignore-scripts npm@11.16.0
  test "$(node "$PWD/.cache/npm-resolver/node_modules/npm/bin/npm-cli.js" --version)" = "11.16.0"
  node "$PWD/.cache/npm-resolver/node_modules/npm/bin/npm-cli.js" --prefix frontend install --package-lock-only --ignore-scripts
  node "$PWD/.cache/npm-resolver/node_modules/npm/bin/npm-cli.js" --prefix docs-site install --package-lock-only --ignore-scripts
  node "$PWD/.cache/npm-resolver/node_modules/npm/bin/npm-cli.js" --prefix frontend ci
  node "$PWD/.cache/npm-resolver/node_modules/npm/bin/npm-cli.js" --prefix docs-site ci
  make local-init
  make local-doctor
  make check
  make local-up
  make local-status
  make local-docs
)
```

The normal gate still invokes the Node 22 installation's npm; its audit/test/build commands
do not request a dependency upgrade. CI and Docker continue to use committed locks through
`npm ci`. Review the generated dependency diff and record passing audits/tests/builds before
submission. Stop and report any failure. Owner evidence of the successful run is recorded above.

- [Upstream peer-loader fix](https://github.com/npm/cli/pull/8448)
- [Pinned npm release](https://github.com/npm/cli/releases/tag/v11.16.0)
