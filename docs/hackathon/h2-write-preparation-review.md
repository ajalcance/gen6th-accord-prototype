# Session-gated write preparation — 2026-10-03

Owner approved the bounded slice and a new two-hour window:
**12:50:44–14:50:44 Asia/Manila, 2026-10-03**. No automatic extension or activation.
Decision: [ADR-0037](../decisions/0037-session-gated-persona-writes.md).
Owner approved the bounded SQL test-fixture correction and renewed a two-hour window:
**18:31:56–20:31:56 Asia/Manila, 2026-10-03**. Other slices and activation remain gated.

## Working result

An explicitly injected saved source with a separate same-workspace write gateway can open
**Read version → Prepare fixture action**: save a version, record independent review, offer a
campaign or record recipient decision/owner revocation. These are structured fixture forms,
not upload, analysis, signing or publishing controls. Default saved connection is unavailable;
the real application mounts no persona route and injects no write gateway.

Four prepared endpoints call existing transactional services. Identity comes from the required
verifier; services check membership/independence/current version and scope. Bodies cannot supply
actors, roles or server time. Faults are sanitized and uncached; invalid response serialization
never becomes a receipt. Existing read transports reject writes; the write transport rejects reads.

Review loads the exact version's current predecessor; decisions discover party-visible offers
and their current decision. Offers require the latest approved review and a supplied version-bound
fixture catalogue. Missing/invalid catalogue stays unavailable; it grants no access or rights.
The backend rechecks selected asset bindings and current roles.

Edits/reopening clear confirmation. Pending/uncertain work blocks new intent; explicit retry
retains request ID/content after edits or navigation. Stop waiting records uncertainty immediately
and ignores late success after another retry or session change. Conflict comparison loads the
head without replacing draft text; new base/confirmation are explicit. Permission loss clears
fetched views/closures and keeps authored fields/intents in studio memory. Other session contexts
cannot expose/retry them. This store contains no fetched snapshots, successful receipts or
credentials, uses no localStorage and does not survive browser reload.
Denied retries and invalid receipts retain earlier uncertainty; restored saved access permits
only an explicit same-intent retry until resolved. Invalid local input is rejected before HTTP.

Default [source preview](http://127.0.0.1:18664/) remains the labelled browser journey; 18660
is the separate older Docker image. Prepared forms use explicit test-source injection only.
No test identity/provider is installed in the preview. Tests do not certify rendered
mobile/zoom/touch/keyboard/reduced-motion geometry or real credentials.

## Current validation

- **233 standard frontend tests / 23 files pass on unchanged frontend source**: all forms, confirmation, predecessor/assets,
  malformed receipts, context isolation, conflict, cancellation, denied and exact retry navigation.
- **14 additional ASGI-to-UI cases pass again after the correction**: eight reads plus six write cases. Actual
  FastAPI/Pydantic responses pass through HTTP client/parsers/forms. Services and verification
  are explicitly synthetic; this is not SQL, login or deployed credential proof.
- **38 new backend ASGI boundary cases pass**: verifier failures before database access,
  false attribution, command/actor mapping, sanitized faults and real-app route absence.
  Together with existing wire/session/read boundaries, **127 isolated backend cases pass again**.
- **10 real-service PostgreSQL write cases pass within the owner's 553-test suite**: creator/reviewer/recipient/revocation journey,
  retry cardinality, server attribution, write-role loss, foreign tenant, changed retry intent,
  self-review, wrong recipient and stale version. The corrected four role-loss cases now pass.
  Owner reports **553 tests / 80.55s / 96.96% coverage**; Trust checks also pass.
- Frontend lint, Prettier, TypeScript, production build and bundle budget pass:
  **166.4 kB shared gzip / 250 kB limit**. Function/file caps were reviewed.
- The earlier agent full `make check` reaches backend static/security checks, then stops at pip-audit's
  **Failed to upgrade pip** bootstrap. `make frontend` stops at npm audit's registry DNS
  **ENOTFOUND registry.npmjs.org** on the earlier unchanged frontend. No gate is skipped or weakened.
  The post-correction agent source run passes
  **776 guards / 18 skips**, policy, harness, doc consistency, backend Ruff/Black,
  strict mypy (**146 source files**) and Bandit. SQL, trust and later full-chain gates were not reached.
- Browser automation cannot initialize its sandbox (`TIOCSTI` unbound variable). No rendered
  browser acceptance or unsandboxed retry is claimed. Subsequent live GitHub read refresh
  and scoped SAST are recorded in the [readiness review](h2-pr-readiness-review.md).
- Backend fingerprint (**159 inputs**):
  `375e3d8a776d68b7d77ef01477ef46eef4ada0335bffdfc1179bc89f35e1c5b2`.
- Frontend fingerprint at the corrected-owner checkpoint (**130 inputs; now historical**):
  `f1d7598b8971ccbba183707e30d717af2db3a85c8698aff67841080bab25c9b0`.
  Both fingerprints match before/after the post-correction agent checks. Corrected SQL has
  not run in the agent sandbox; the previous owner's audit pass does not certify new SQL results.
  Supplied trailing fingerprints matched that checkpoint; leading output was omitted.
  Subsequent approved dependency remediation supersedes the frontend digest only;
  current source/restoration commands are in the [dependency checkpoint](braces-installation-proposal.md).
  The intermediate owner run stopped at frontend's **braces high-severity audit**, not SQL. Git metadata, dependencies, constraints,
  guard definitions and pre-existing work were preserved by this correction.

## Owner SQL failure and approved correction

Owner supplied the full run on October 3: **549 backend tests passed / 4 failed in 83.40s**,
**96.96% application coverage**, **776 guards / 18 skips**, and backend audit found no known
vulnerabilities. Leading/trailing fingerprints matched the prior backend
`f3df858e53e615302bae0b68db9030800ebcc87f1daa62ed3090c19afe3e4a98` and the frontend above.
The run stopped at SQL tests with `validation_exit_status=2`; trust/frontend/docs-site and
the separate ASGI command were not reached. This is a failed checkpoint, not full-gate proof.

All four failures occurred before the replay request: deletion of a referenced member violated
owner/reviewer/recipient foreign keys. The corrected test downgrades that member to `viewer`,
asserts the role changed, then retains the **403 and unchanged-record-count assertions** for
the exact replay. No service, foreign key, trigger, schema or authorization rule changes.
The owner's corrected SQL run proves the write-role-loss cases. Complete membership revocation
is a separate lifecycle decision; a viewer retains read membership.

The subsequent owner's run passes all **553 backend tests** and Trust checks, then fails the
frontend audit on GHSA-vfj7-8cjw-p6xm (`validation_exit_status=2`). Both frontend and docs-site
lock the affected braces 3.0.3 chain. No patched release is listed in the advisory; no forced
lint downgrade or exemption was applied. See [audit review](braces-audit-review.md).
Owner approved dependency-remediation preparation for both apps. Source acquisition and fork review
are complete; the [exact private-backport proposal](braces-installation-proposal.md) passes its
released-case/consumer checks. Owner then approved exact adoption/installation/maintenance
(ADR-0038). Both manifests/locks pin it; docs-site installs with 31 tests/static/build passing.
Frontend's initial frozen reinstall failed at cache/registry DNS. The owner subsequently restores
both locked trees and reports full validation exit **0** with **14 ASGI tests / 17.31s** and
matching three trailing input hashes. Agent verifies restored chains and 20 regressions per app.
The supplied closeout excerpt omits preceding detailed gate output; local owner proof remains
separate from agent full-gate and PR/CI evidence. Earlier failures are historical.

## Owner current-source validation

The write-only command's frontend precondition is superseded by approved ADR-0038 remediation.
The [dependency restoration and complete validation block](braces-installation-proposal.md) has
completed successfully in the owner run; no repeat is needed without changed source or an
unresolved failure. The reproducible command runs
in **Mac Terminal**, with Docker running. It checks branch, backend/frontend source and exact
archive/provenance, restores both locked trees using the already installed npm 11.16.0 resolver,
then runs the unchanged full gate and conditional ASGI bridge. No additional install approval
is needed for this owner-approved artifact; no provider, route or deployment is activated.
The closeout result records matching trailing fingerprints and final exit status 0.

## Review and activation gates

Preserve dirty work and separate review units. No staging, commit, PR, self-label, guard/policy,
cloud/model/signing/publication/visibility/licensing or deployment change. Owner security/ADR
review labels and revision-bound PR CI remain required. The extra integration command is not
part of existing CI; changing that gate is separate work.

Trusted Zynth identity, credential/origin/CSRF/TLS/header/nonce and bounded-ingress review still
gate live reads/writes. Scanner/key/retention providers gate uploads. The 454-test owner result
and ADR-0036 fingerprints do not certify these bytes. H2 secure-core completion remains pending;
H3–H6 and the full Stage 0–9 roadmap remain intact.
