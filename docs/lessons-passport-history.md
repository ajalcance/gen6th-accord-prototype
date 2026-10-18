# Passport lessons — retained dated entries

## 2026-10-04 — A driver probe does not persist credential configuration

- Owner's backend session factory/role verifier passes on Mac port 18662. Its URL/password
  lived only in memory; persist private runtime configuration separately before HTTP activation.

## 2026-10-04 — Container login and Mac backend connection are distinct

- Owner password TCP login inside PostgreSQL returns accord_runtime. Verify the Mac's
  published port with the backend driver before treating its connection configuration as ready.

## 2026-10-04 — Role privilege proof does not establish password login

- Owner created accord_runtime and passed the application predicate under SET LOCAL ROLE;
  the 17-table inventory remains empty. Test actual TCP password authentication separately,
  then configure the backend runtime URL; never substitute the migration operator role.
- Owner password command reports no error; actual TCP authentication still needs its own proof.

## 2026-10-04 — A real workspace needs a source boundary and a data inventory

- Removing a sample entry screen is insufficient when shared views import its selectors.
  Extract receipt-only components and move historical scenarios into test-only modules;
  inspect the production import graph and built bundle for sample content.
- A privileged, read-only all-schema count can establish an empty baseline. Tenant RLS can
  hide rows; an ordinary runtime connection cannot certify the whole store. Any populated
  baseline needs provenance review, not automatic deletion or relabelling (ADR-0041).
- Isolated ASGI and form tests are serialization/recovery evidence. Docker-backed SQL,
  live identity and rendered-browser acceptance still require their own evidence.

## 2026-10-04 — Real records need real identity and a distinct runtime role

- Remove sample flags through a migration that refuses populated history; never reclassify
  examples. Zynth ID/access tokens have different issuers and audiences; platform UserInfo
  rechecks current account/session status. Login must resolve established canonical bindings,
  not grant a browser role. Keep operator credentials separate and reject privileged runtime
  roles. Test-only signing/fault data proves boundaries, not live SQL or provider connection.
  See [ADR-0040](../decisions/0040-real-records-and-zynth-session-boundary.md) and the
  [owner runbook](../runbooks/zynth-local-integration.md).

## 2026-10-04 — Removing sample language requires removing sample behavior

- Owner chose an empty workspace gallery rather than relabelled fictional records. The default
  page now loads no examples or historical local drafts; scenario tests inject their state
  explicitly. Keep unavailable creation and footer monitoring factual while consolidating
  controls. Preserve stored drafts without restoring them as real records. DOM behavior/CSS
  values remain separate from rendered acceptance. Owner screenshots exposed redundant title/status
  rows and an input-specificity conflict: use one title/tools row, transparent header actions
  and FAQ outside Records. Owner renamed all visible Gallery terminology to Record/Records;
  keep navigation, titles, return actions and accessibility labels consistent. Existing query
  identifiers remain internal compatibility details. See the [layout review](../hackathon/workspace-layout-review.md).

## 2026-10-03 — An uncertain write belongs to its original intent

- Cancellation stops waiting, not server commitment. Record uncertainty immediately and ignore
  late results, including after retry or source change. Block new intents until the original is
  resolved. Keep authored drafts/failed intents separate from fetched records and successful
  receipts; clear confirmation on edits/reopening. A new session context cannot inherit access.
  A denied retry or malformed response cannot erase earlier uncertainty. Distinguish invalid
  local inputs rejected before transmission from an invalid receipt after possible commitment.
  Test wire/client/forms separately from PostgreSQL transactions and real credentials (ADR-0037).

## 2026-10-03 — Record organizer answers at their stated scope

- Owner-supplied correspondence confirms participant ownership of submitted materials;
  it does not explicitly answer package exclusions, template eligibility or source packaging.
  Preserve exact wording, provenance and unknown reply date without inferring new permission.
  Handoff separates H2–H6 exit conditions, current source-bound gates and expired build scope.

## 2026-10-03 — Discover references before connecting governance panels

- A selected saved record cannot use example campaign/evidence IDs. Discover authorized
  references under an exact version, then bind status/history/audit to those receipts.
  Permission loss in a child panel must clear the selected saved view; draft lifetime is separate.
  ASGI serialization through the typed browser client proves the wire/UI path, while stub
  services do not prove PostgreSQL authorization. Keep that SQL journey as a distinct gate.
  New backend bytes need fresh source-bound evidence; earlier passing totals remain historical.
  The owner renewed the implementation window to 09:16:54–11:16:54 Manila (ADR-0036).

## 2026-10-03 — Governance presence is not current permission or verification

- Keep immutable history separate from current eligibility, audit presence separate from
  chain/signature verification, and inspection separate from rights or permanent retention.
  A disconnected preview needs its own fictional record and clock. Recovery compares a
  snapshot without merging, and uncertain retries keep the original request/content.
  Compare canonical serialized audit times exactly: JavaScript Date rounds away fractional
  precision, so a mismatched reference can otherwise appear to match.
  Unchanged backend fingerprints preserve prior SQL proof; new frontend code needs fresh
  relevant gates even when dependency manifests are unchanged (ADR-0035).

## 2026-10-03 — Owner-run gates resolve sandbox audit limits

- Owner source-bound `make check` passes, including Python/npm audits and 454 backend
  tests with PostgreSQL cases at 96.55% coverage. Matching fingerprints were independently checked.
  Record sandbox DNS/bootstrap failures as historical, without weakening a guard. Synthetic
  session proof still does not activate trusted identity or establish a connected browser journey.

## 2026-10-03 — Saved records need their own lifetime and source

- Separate browser fixtures from stored versions. Clear page/version results on access loss,
  source changes and loading; discard late requests even when cancellation is ignored.
  Observed reads use explicit POST queries to preserve GET semantics. Typed verifier output
  still needs validation; a synthetic verifier is not proof of login or identity activation.

## 2026-10-02 — Bind owner validation to the changed source

- Read-side owner validation passes 421 tests with 96.42% coverage. Its trailing fingerprint
  matches the current independent rehash; the pasted excerpt omits the leading fingerprint.
  Record that distinction and keep passing service tests separate from live UI connectivity.

## 2026-10-02 — Read pages need identity and cursor contracts

- A bounded page must bind every item to the requested workspace/record, reject duplicate
  ordering and validate its next cursor. Empty reads still need observation; never log search
  text. Private evidence status does not need decryption or prove retained audit verification.

## 2026-10-02 — Prepare connections without inventing authority

- Encrypted intake needs real key/inspection/retention providers, not successful test doubles.
  Keep immutable provenance separate from expiring payloads. Transport casts need runtime
  validation; cancellation can leave a committed write, so preserve the exact retry intent.
  Owner package installation resolved sandbox registry DNS without bypassing confinement.
  Owner-approved exact action-set assertions caught registry drift explicitly; the corrected
  source passed 397 database tests with matching fingerprints and 96.35% application coverage.

## 2026-10-02 — Interaction affordances must describe real behavior

- Fourth-pass console (ADR-0030): drag handles need pointer behavior; disclosures need focus handling; command empty states must derive from actual results. State colors cannot imply connected security. Rendered acceptance remains separate from DOM tests.

## 2026-10-02 — Transition prompts must name the current checkpoint

- Refreshed next-session handoff with 73-test UI evidence, unchanged backend fingerprint,
  final visual-review priority and explicit gate/activation holds; removed stale next-task claims.

## 2026-10-02 — Console credibility needs evidence and measured layout

- Owner approved second/third-pass UI (ADRs 0028/0029). Independent fixture state and
  draft-only restoration remain distinct from server authority. Compact density needs its
  own tokens; gallery columns follow workspace width. Status lights cannot claim monitoring
  without live sources. Hover disclosure needs keyboard/touch equivalents. DOM tests prove
  behavior, not spacing; screenshot/mobile/zoom review remains separate.

## 2026-10-02 — Coverage configuration depends on invocation location

- Owner repeat round passed 31 frontend and 349 backend tests. Root-level bare coverage
  included tests/migrations in its 98% figure; explicit backend configuration and source
  reporting gives 96% application coverage and passes the 70% floor. Updated repeat commands
  bind coverage explicitly. Test success still does not establish UI/API connectivity.

## 2026-10-02 — Screen navigation is not backend integration

- Audited browser state and mounted routers: H1 sends no persona requests. Note edits now
  invalidate stale demo decisions; comparison gating and source-family wording are corrected.
  Backend receipts cannot be inferred from UI clicks. See the frontend/backend alignment review.
  The repeat round expands to all 349 backend tests with coverage, beyond the 301-test target.

## 2026-10-02 — Verify detection against its expanded database target

- The owner passed all 301 persona/migration tests in 50.58s with matching fingerprints,
  independently confirmed against current source. Recovery, concurrency and retention proof
  now belongs to this slice; the earlier workflow-only result could not establish it.
  Dependency audits and revision-bound CI still require completion.

## 2026-10-02 — Detection needs a durable checkpoint

- Direct PostgreSQL persona events bypass Redis ingestion. Atomic receipts enable
  restart/retry discovery. Retention preserves pending/supporting persona windows while
  old-window uncertainty stays explicit. See ADR-0027; new SQL proof pending.

## 2026-10-02 — Bind owner database evidence to the tested source

- The corrected workflow target passed all 279 tests in the owner's terminal in 48.86s.
  Matching before/after fingerprints and an independent local comparison bind that result to
  the current backend source. This establishes target coverage, not a completed full gate.

## 2026-10-02 — Freeze the scope in expiry boundary tests

- Owner validation stopped at 48 passes because separately generated offers expired at
  different instants. Both now share an explicit scope, testing rejection at the exact expiry
  boundary. The matching source fingerprint identifies the failed run; revalidation is pending.

## 2026-10-03 — Preserve referenced identity when testing write-role loss

- Immutable records reference workspace members. Deleting an already referenced member
  fails at the foreign key before authorization is exercised. Owner approved correcting the
  four write-retry fixtures to downgrade the role to `viewer`, assert that downgrade, and
  retain 403/no-new-record assertions. Name this write-role loss, not membership removal;
  full membership revocation needs its own lifecycle design. SQL execution remains owner/CI.

## 2026-10-03 — A successful SQL correction can expose a new dependency blocker

- Owner's corrected source passes 553 backend tests and Trust, then stops at the frontend
  braces advisory. Both apps contain the chain; the advisory lists no patched release.
  Record the passing phases separately. A forced lint downgrade, untested fork or renamed
  dependency does not establish a safe fix. Preserve the audit gate and prepare a separately
  approved dependency proposal with exact sources and compatibility evidence before installs.

## 2026-10-03 — Freeze the whole dependency distribution before adoption

- The fetched fork's hashes/MIT license match, but its fractional depth handling and extra
  parser changes remain. A direct glob-engine alias changes matched roots too. The published-
  source backport passes all 764 released cases through a Node runner adapter and both app
  consumer reviews. Freeze its actual tar bytes and preview manifest/lock changes; adopting a
  private derivative adds maintenance and advisory-lineage duties requiring an owner decision.

## 2026-10-03 — A tested backport is separate from an audited dependency

- Preserve published behavior when backporting a security patch: PR 72 also changes stringify
  parent handling. An isolated correction passes 9 tests per npm tree on Node 22, including
  10,632 comparisons and 243 depth assertions each. Original 3.0.3 metadata still leaves the
  advisory open. A visible fork commit is insufficient to certify its complete distribution;
  acquire source, inspect scripts/license and pin the actual artifact before installation.

## 2026-10-03 — Verify npm's generated tree and preserve Docker build contexts

- Owner approved the exact private backport and maintenance. A direct local development
  dependency plus scoped exact-version override resolves consistently; the existing npm 11 resolver
  changes only root/braces lock records. Reject npm 10's unrelated platform metadata drift.
  Mirror the frozen archive inside each app's build context and verify its hash in normal tests.
  A frontend frozen reinstall exposed missing cached tarballs and sandbox registry DNS failure;
  finish through the owner's existing network access, without changing policy or claiming green.

## 2026-10-03 — Close the owner-run gate against the exact implementation inputs

- Owner validation exits 0 after restoration/full gates and the conditional 14-test ASGI
  bridge; three trailing fingerprints independently match current inputs. Both installed
  dependency chains and 20 regressions per app are independently verified. Record the
  preceding detailed output as omitted, and preserve sandbox failures as historical evidence.
  A complete local run does not establish revision-bound CI or authorize activation.

## 2026-10-03 — Reconcile evidence before packaging review units

- Owner full-local proof supersedes an earlier gate failure, but does not validate a different
  PR head. ADR/current status must reflect that distinction. Include untracked implementation
  in scoped source scans; the existing rules scan 211 Python/TypeScript targets with zero
  findings. Mixed dependency and integration-script hunks require explicit review-unit selection.
  A renewed time window permits the stated work, not provider or route activation.

## 2026-10-04 — Empty data does not establish schema readiness

- Owner inventory reports three scaffold tables and zero domain rows, with empty Redis.
  This is a clean local baseline, not proof that persona migrations or runtime permissions
  exist. Validate the current gate, apply migrations, then repeat inventory before provisioning.

## 2026-10-04 — Full-gate success and application migration are separate proof

- Owner validation exits 0 with matching source fingerprints and 15 ASGI tests. Disposable
  SQL test success does not upgrade the application volume. Rebuild the migration image,
  apply its head to the empty local store, then repeat inventory before provisioning users.

## 2026-10-04 — A migrated empty store still needs a confined role

- Owner confirms migration 0009identity, 17-table empty inventory and empty Redis. Frozen
  migration descriptions are history, not inserted sample data. Probe the actual runtime
  role with the application predicate before separately verifying password login.
