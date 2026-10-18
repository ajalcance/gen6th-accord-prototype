# Record-bound governance preparation — 2026-10-03

Historical checkpoint, followed by [write preparation](h2-write-preparation-review.md).
Its source preconditions and test totals do not certify the later changed tree; use the
new checkpoint's owner command for current SQL/full-gate proof.

The owner authorized recommended tasks **2–4**: record-aware saved governance, missing prepared
backend reads and isolated integration validation. The expired 08:57:39 window was explicitly
renewed **09:16:54–11:16:54 Asia/Manila, 2026-10-03**. No automatic extension or activation.
Decision: [ADR-0036](../decisions/0036-record-bound-governance-reads.md).

## Working result

The browser **Evidence & decisions** demo remains a separately labelled fictional record.
In a trusted injected **Saved records** source, open **Read version → Inspect governance records**.
Select a discovered saved version, then **Version / Reviews / Campaigns / Evidence**.
Version and history pages are bounded; campaign references are party-authorized and private
evidence metadata is owner-only. Status uses current backend reasons rather than example text.
All records remain fixtures and unsigned; there is no real rights determination or signing.

Changing version/section/campaign/page clears prior panel queries and ignores late responses.
Workspace, persona and trusted session context keys reset the surface. Permission loss in any
governance/audit read clears the selected saved view, with a clear connection recovery message;
browser drafts remain untouched. Empty pages and unavailable services offer useful navigation
or explicit retry. An invalid response is never replaced with example history.

Default **Saved records** remains unavailable: no trusted source/provider is installed. Both
router factories are unmounted; the new factory prepares eight governance query POSTs alongside
the original two gallery/version queries. The separate prepared transport rejects writes, uses
same-origin credentials/mode, no cache/redirects and no implicit POST retry. No upload/download
path or private payload/key reference is exposed.

The source preview is [loopback 18664](http://127.0.0.1:18664/); port 18660 is the older Docker
image. No terminal command is needed to inspect the existing fictional demo. The new saved
surface is exercised with explicit test-only source injection; it cannot be presented as a live
connection. Mobile/zoom/touch/keyboard/reduced-motion geometry acceptance remains owner-deferred.

## Current validation and provenance

- **204 standard frontend tests / 19 files pass**. The existing Node-only command and
  configuration are unchanged. Nine discovery-contract and three saved-context cases add
  tenant/persona/version/cursor/size/privacy checks, version selection and session/late-result cleanup.
- **8 additional ASGI-to-UI integration cases pass**, using the explicit two-runtime command
  `npm run test:governance-integration`. It requires the installed backend venv and Node 22.
  Real FastAPI/Pydantic responses pass through the HTTP transport, gateway and saved panels.
  Cases include audit pending, permission/session loss, preserved draft, unavailable/no retry,
  rejected/expired evidence and revoked/expired campaign status. Writes remain disconnected.
- **89 backend contract/session/ASGI tests pass**. Governance tests cover all eight query paths,
  verifier failure before database access, bounded inputs, strict validation, false authority rejection and
  actual response serialization. Six new real-service PostgreSQL discovery/ASGI journey tests
  collect successfully and await owner/CI; collection is not passing execution evidence.
- Frontend lint, full Prettier, strict types and production webpack build pass. Shared client
  bundle remains **166.4 kB gzip / 250 kB**. Backend Ruff/Black, strict mypy (**141 files**) and
  Bandit pass; file/function bounds and diff hygiene pass.
- Fresh `make check`: preflight, **776 guards / 18 skips**, policy, harness and backend static/
  security checks pass, then pip-audit stops at `Failed to upgrade pip`. No SQL or later gate
  success is claimed. Fresh `make frontend`: lint/format/types pass, then npm audit stops at
  `ENOTFOUND registry.npmjs.org`. No audit is bypassed or dependency installed/changed here.
  Only a frontend npm script was added; dependency versions and lockfiles are preserved.
- Backend fingerprint (**154 inputs**):
  `b4293e6736cb2af8699adf5e68fd02f0a4b6195268065fa357a3be568114412c`.
- Frontend fingerprint (**114 inputs**):
  `b16012fea11160abb998d29289b8226f940e5dab8803eb92e7fe449b209b20ca`.
  The prior owner **454 tests / 96.55%** checkpoint belongs to the previous backend source.
  New SQL/full-gate, current audits, revision-bound CI and rendered acceptance remain incomplete.

## Owner SQL/full-gate and integration command

Use **Mac Terminal** with Docker running and the already-installed repository dependencies.
This runs throwaway PostgreSQL tests, local audits/builds and the isolated ASGI bridge. It does
not mount persona routes, activate providers, apply migrations to persistent data or deploy.
No new package installation is requested. Keep source stable and report the full result plus
both leading/trailing fingerprint pairs. Preconditions stop if source drifted.

```bash
cd "/path/to/gen6th-accord" &&
test "$(backend/.venv/bin/python .cache/workflow-source-evidence.py)" = "backend_source_sha256=b4293e6736cb2af8699adf5e68fd02f0a4b6195268065fa357a3be568114412c files=154" &&
test "$(backend/.venv/bin/python .cache/frontend-source-evidence.py)" = "frontend_source_sha256=b16012fea11160abb998d29289b8226f940e5dab8803eb92e7fe449b209b20ca files=114" &&
backend/.venv/bin/python .cache/workflow-source-evidence.py &&
backend/.venv/bin/python .cache/frontend-source-evidence.py &&
LC_ALL=en_US.UTF-8 PATH="$PWD/backend/.venv/bin:$PWD/.tools/bin:/opt/homebrew/opt/node@22/bin:$PATH" make check &&
(cd frontend && PATH="/opt/homebrew/opt/node@22/bin:$PATH" npm run test:governance-integration) &&
backend/.venv/bin/python .cache/workflow-source-evidence.py &&
backend/.venv/bin/python .cache/frontend-source-evidence.py
```

## Review units and activation gates

Keep bounded discovery/router work, saved UI/transport, test bridge/SQL journeys and ADR/docs
separately reviewable from existing evidence, session, dependency, policy and recovery changes.
Preserve the dirty tree; no Git staging, commit, PR, self-label or deployment is performed.
Owner-applied security/ADR review labels and revision-bound PR CI remain required.

The synthetic ASGI bridge lives under tests, mounts factories only in a throwaway test app,
uses explicit synthetic sessions and stubs services. It proves actual Pydantic/ASGI serialization
through the frontend HTTP client/parsers/UI without a listener or real identity. Separate
PostgreSQL journeys use real services and test-only verifiers; bridge results do not certify
SQL authorization, credential security, live login or rendered browser behavior.

Zynth remains deferred. Trusted identity/credential/origin/CSRF/TLS/header review, real evidence
scanner/key/retention providers and separate owner authorization still gate activation.
No cloud, monitoring, models, signing, publication, visibility/licensing or deployment changes.
Hack2skill clarification remains pending; the complete Stage 0–9 roadmap is preserved.
