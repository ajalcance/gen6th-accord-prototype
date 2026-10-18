# Security (posture & practices)
2026-10-13: PR #66 merged at2c7d972; exact-main pushCI38326263023 succeeds (application jobs skipped). Owner inventory now28 open app alerts (6 critical/8 high/12 medium/2 low), no PyJWT entries; closure reasons unknown. [App review](hackathon/application-dependency-review-2026-10-13.md) verifies full locks, zero tinypool entries/edges, approved braces bytes,514/31 Node22 tests, lint/types and DoD. Unmerged fixes remain separate; Owner metadata142 records/87 packages accepted; retain tested Vite8. Focused preview27/31 tests/lint/types/format/DoD pass; owner fresh installs/full gates pass. Temporary tooling link removed;28 hashes/population and frozen source pass. PR67 mergedf466978; exact-main pushCI38336603073 passes applicable app/static gates. Equivalent patch repair preserves approved archives/source/locks; integrated full local checks pass. Owner API reports zero open Dependabot alerts. [Application integration preparation](hackathon/application-integration-2026-10-13.md) passes preview DoD; policy PR77 mergedb2ddb6c with exact-main CI38341957279 green; application full local gate passes (1447 backend,94.15%;514 frontend;31 docs;987 guards/18 skipped); Trust/DoD pass. Three documentation scan matches are reworded; clean unpublished commit preparation preserves controls/locks and completed code checks. PR78 head d67ecd8 passes Linux backend/frontend/static/hygiene and custom SAST; community SAST flags two legacy HTTPSConnection calls. Candidate replaces them with HTTPS-only transport, explicit certificate/hostname verification, no redirects/proxies, timeout and response bounds;54 auth tests, lint/types/Bandit pass. Owner custom/community scans pass at7c70939; full check found test-double typing errors. Candidate uses real parsed HTTPResponse doubles;54 auth tests and full mypy414 sources pass, preserving TLS/redirect/size assertions. Full repaired-head checks and CI remain required; native deployment pending. [Earlier snapshots](hackathon/dependency-continuation-history-2026-10-13.md) are retained; no guard or policy changes.
Scanner release integration PR61 is accepted; genuine packaging/native evidence remains pending. Preserve ADR0072/0073 mapping, paused Tasks, owner-only cloud/Git checkpoints and signed digest-bound releases.
ADR-0062 prepares forced-RLS, append-only lifecycle declarations/assessments/concerns with server attribution, performer locking, CAS and replay. Owner/operator cannot self-review; reporters cannot decide their own concerns.
Production permission rechecks exact dossier/operator binding, membership, independent assessment/rights dates and performer-wide suspension across all versions/cases. Trials are private and at most 30 days.
Server-inspected evidence hashes preserve attestation basis; no private-original access or retention rule changes. Originals remain owner-only; private dossiers stay outside passport projections.
`PERSONA_LIFECYCLE_ENABLED=false`; disabled bound requests deny. Migration/grants, SQL/concurrency, real sessions and rendered/cloud acceptance remain pending. [Lifecycle register](hackathon/performer-lifecycle.md).
ADR-0061: [inventory](runbooks/google-production-inventory-2026-10-11.md) is configuration evidence; queue paused. [Redis CA](hackathon/redis-ca-preparation-2026-10-11.md) live mounts/TLS pending. Approved [SQL transport](hackathon/sql-transport-proposal-2026-10-11.md), ADR-0063, denies non-proxy production URLs, URL overrides and known admin runtime logins. ADR-0064 [SQL roles](runbooks/google-sql-role-preparation.md) prepares distinct NOLOGIN profiles and evidence INSERT, closes PUBLIC CREATE/TEMP; guards unchanged. Reference head UPDATE and compliance event DELETE are real authority, governed by existing application checks; spine reads lack RLS. Immutable lock-column UPDATE still triggers denial. Full-check-10 exits 0: 1249 backend/93.58%, Trust, 514 frontend, 31 docs-site, builds/audits/DoD; hashes match. ADR-0065 [composition](runbooks/google-container-composition.md) adds pre-serve scanner readiness and startup-failure cleanup; Checkpoint 11 log verifies 1263 backend/93.79% and all later phases; current hashes match, pasted numeric exit omitted. ADR-0066 [reference assembly](runbooks/google-reference-runtime.md) preserves machine/job/SQL guards with independent config and full job hash; Checkpoint 12 log verifies 1285 backend/93.81% and all later phases; SQL factory/replay acceptance passes, current hashes match, pasted numeric exit omitted. ADR-0067 [compliance lifecycle](runbooks/google-compliance-lifecycle.md) prepares confined startup, progress-only health and bounded cooperative cleanup; Checkpoint 13 log verifies 1318 backend/93.86% and all later phases; confined SQL tests pass, current hashes match, pasted exit omitted. Earlier stage commits survive cancellation; existing worker guards stay unchanged. Reference reconcile IAM/credentials, native TERM/rollback, [scanner packaging review](hackathon/scanner-packaging-review-2026-10-12.md) identifies unsafe upstream defaults and missing signed scanner release integration; ADR-0068 [scanner adapter](runbooks/google-scanner-health-adapter.md) denies missing/dead children, failed/stale probes and uncertain cleanup; required runtime has no default launcher. Checkpoint 14 log verifies 1351 backend/93.94% and all later phases; current hashes match, pasted exit omitted. [Candidate/runtime review](hackathon/scanner-runtime-review-2026-10-12.md) records index/platform identifiers without claiming provenance or signature verification; ADR-0069 [managed runtime](runbooks/google-scanner-managed-runtime.md) validates real release-bound CVDs/configuration, signatures, trusted updates and unchanged loaded bytes before fixed process launch. Test data stays outside production imports/context; no placeholder seed manifest. 63 new tests and 150 combined tests pass; checkpoint 15 log verifies 1414 backend/94.10% and all later phases; current hashes match, pasted exit omitted. Actual image/signature/load behavior remains pending. Proposed ADR-0070 [artifact/release design](hackathon/scanner-artifact-design-2026-10-12.md) requires genuine seeds, explicit context/layer exclusion of fixtures, verified build inputs and matching signed component/assembly evidence. These new enforcement checks are pending a separate guardrail PR; no active gate or build is claimed. [Source preparation](hackathon/scanner-packaging-inputs-2026-10-12.md) adds real factory and root-only seed/config emitter with pinned verifier/seed hashes, native checks, unchanged-byte binding and exclusive output; 33 new/183 combined tests pass, mypy 414 sources, checkpoint 16 saved log verifies 1447 backend/94.13% and all later phases; current hashes match, pasted numeric exit omitted. Proposed source inventory excludes emitter/tests. Non-loopback executable listener is deferred by S104/B104; no suppression or computed spelling, review separately. Exact native/Python packaging remains unresolved. Real validation/native packaging and routing remain pending; no identity/role/retention bypass. CI/signed release and live acceptance required; cloud changes owner-run. [Build-input review](hackathon/scanner-build-input-review-2026-10-12.md) identifies published ClamAV archive/signature hashes and candidate Trixie toolchain; actual verification/complete locks remain open. Approved ADR-0071 prepares explicit container launch without Python guard exceptions. Owner published draft [PR #60](https://github.com/ajalcance/gen6th-accord/pull/60), head `116fa14d9d82a9e12dbae4a268db89086d549a4a`: Linux guard tests fail with E2BIG before oversized-input CLI execution (864 passed, 1 failed, 18 skipped). Short case IDs must preserve the oversized payload and denial checks. Owner review/label, exact-head CI and mandatory release wiring remain pending; Dependabot alerts are unverified. See [October 12 handoff](hackathon/next-session-2026-10-12.md).

ADR-0060 credits use immutable forced-RLS annotations with verified-session actors, current-owner declarations, declaration CAS, named-human self-confirmation and exact retries. Workspace-visible
metadata grants no private evidence access, ownership, organization attestation or publication. Existing reviews/passports exclude credits. Default disabled; schema/grants/live acceptance pending.
See [boundaries and O1–O8 acceptance criteria](hackathon/performer-identity-and-credits.md).

ADR-0058 adds offline corpus byte checks and bounded local benchmark report inspection.
Reports remain untrusted supplied observations; no HTTP upload, storage, runtime policy or server
audit authority is added. Resolved corpus paths/bytes are bounded; roots must be owner-controlled
during runs. Permission validity, image inspection and provider execution require separate evidence.

**S8–S10 source boundaries (2026-10-05, ADRs 0056/0057):** owner-only private evidence
is quarantined, encrypted, bounded and inspected before access; expiry denies reads but is not
physical deletion. Explicit asset enrollment records a claim, not an independent rights finding.
Public routes disclose only separately approved signed fields and an optional approved inspected
thumbnail. No private package, party identifiers, evidence bytes or original/analysis images are
publicly served. Withdrawals are append-only and prevent further public reads; copies persist.
Committed issuance retries reuse retained trusted packages. Signature integrity and fresh scoped
permission remain distinct; public access grants no reuse rights. Both new activation flags are
false by default. SQL/RLS, scanner/KMS/trusted-key acceptance, retention authority and anonymous
rate/cost controls remain owner/CI gates. [Acceptance record](hackathon/evidence-assets-public-passport-slices.md).

S7 (ADR-0055) prepares opt-in workload metadata access, explicit KMS wrapping/signing trust and
OIDC-authenticated reference-only Cloud Tasks. Browser sessions never authorize the worker;
fixed Google JWKS, audience/email/subject/time/signature checks precede bounded task input.
Immutable SQL intents/transition protocol, SELECT/INSERT grants and fresh creator/reference checks
bind completion atomically to encrypted face generations and observations. Ledger recovery reserves
completion space; three attempts bound repeated precommit cost. Unknown KMS aliases never fall
back to Vault; retained versions are explicit. No credentials/pixels/actor/model in task bodies.
Default activation is disabled. Configuration flags are not live probes; queue tombstones are not
completion. SQL/RLS, actual IAM/Google/key rotation, benchmark and rendered acceptance remain open.

Production passports (ADR-0054) reuse exact-version review/asset/recipient/expiry/revocation.
Consent/claim references require owner/studio/version-bound clean unexpired retained evidence;
scanning is not a rights verdict. Migration 0014 adds bounded immutable offer metadata only.
Owner-only asset reads never substitute private evidence. Default signing/trust runtime is unset.
Export requires eligible accepted production and approved references, rechecks membership and
permission after signing, and excludes private evidence/keys/vectors/reviewer comments. Injected
Ed25519 keys bind domain-separated canonical JSON; packages cannot supply keys or URLs. Prepared
Google KMS signing uses immutable resource/workload access and CRC32C plus local signature checks.
Private verification authorizes before bounded input, rejects duplicate keys, verifies before
interpreting claims and binds saved records/acceptance before returning fresh permission. Valid
historical signatures cannot restore expired/revoked use. Server observations contain no uploaded
claims. Real migration/KMS/SQL/key lifecycle/rendered acceptance remain separate owner gates.

Reviewer brief (ADR-0074) is disabled by default and fails startup if enabled without a valid
project, region and model. It authorizes through the audited saved-version loader before any model
call, then sends only the four creator-written text fields to Gemini on Vertex AI with workload
identity. That is data egress to Google, disclosed in the interface before each click. No images,
tools, URL fetching or API key are used. Output must match a schema and plain-text limits or it is
rejected, never repaired. Limits are ten requests per actor per ten minutes, four concurrent calls
and a 45 second ceiling, held per instance. Failures return an opaque 503 and log no record
content. The brief is advisory, unstored and decides nothing. Prompt injection from the fields is
mitigated, not eliminated; the human reviewer remains the control.

Investigation (ADR-0053) authorizes before metadata/decryption/provider work, refreshes search
server-side and binds selected version/reference/latest generation. Membership, query openness,
calibration and catalogue are rechecked after model/key work. An allowlisted schema accepts only
neutral visual labels citing both inspected images or abstention; mandatory evidence gaps remain.
No model tools, source-note instructions, external URLs, browser scores or rights verdicts enter
processing. Encrypted 64 KiB immutable packets retain query provenance/digests/boxes, not pixels
or vectors, under explicit retention confirmation. Migration 0013/SELECT-INSERT grants are source
only. Committed replay and bounded history freshly authorize. Atomic server observations describe
processing, not source truth. Real Gemini/SQL/retention/key/browser acceptance remains pending.
Saved review requests bind studio/version/analysis via composite FK and immutable RLS-protected
rows. New requests require the current version; replay cannot change evidence or actor. They grant
no decision/permission and send no notification; existing independent review remains authoritative.

Similarity serving (ADR-0052) authorizes human membership before input/decryption/cost and
reauthorizes after long work. Approved references/latest generations remain studio/version bound;
catalogue/head changes reject disclosure. Finite unit vectors and exact policy compatibility
precede ranking; missing/expired calibration and pool overflow fail closed. Query original bytes
are discarded; safe pixels/representations use actor/studio/part-bound AES-GCM in injected Redis
with absolute ten-minute expiry. Clear tombstones block late preparation and delete live children;
in-flight orphan children stay inaccessible until original expiry. Browser access loss/expiry/clear
removes query views and revokes blobs; failed server clearing is visible. Default runtime is unset,
no production policy ships and no query enrolls in SQL. Redis/backups/provider retention, bounded
connections, real keys/Google, permissions and corpus acceptance remain owner activation gates.

Face processing (ADR-0051) authorizes membership and approved-reference binding before decrypt;
only the version creator can process. Server generation/index selection excludes browser
coordinates/actor/vectors. Boxes/dual vectors are encrypted with exact-version/request context;
private responses expose bounded metadata only. Forced RLS/immutable migration 0012 and
SELECT/INSERT-only grants are prepared, not applied. Committed intents replay after current
authorization; precommit failures can repeat external cost. Provider injection is disabled by
default; Google adapters read no personal credentials and reject redirects/errors/oversize data.
Linux crop limits and actual permission/corpus/provider acceptance remain pending; quality is
provisional and no production similarity model is selected. No new purge/deletion path exists.

Analysis capture/reference approval (ADR-0050) scans original/thumbnail/analysis before atomic
encryption. Dedicated analysis pixels bind source/processing/scan provenance into wrapping context.
Owner-approved unique references are version-bound; staged metadata is owner-only and reference
thumbnails require current membership/exact binding. No original/analysis bytes or wrapping
material leave the server. Forced RLS/immutable migration 0011 and SELECT/INSERT-only grants are
prepared, not applied; no deletion, key/provider activation or model recognition occurs.

Exact portrait search (ADR-0049) authorizes human session/membership before bounded body consumption,
recomputes the file digest and scopes every joined table to the studio. Only immutable enrolled
bindings can return; staging and other studios are excluded. Queries are not decoded or persisted,
and originals are never read. Private no-store responses bind method/workspace/request/digest;
server observations carry only operation/method/counts. Fresh historical inspection reauthorizes;
known access loss and session changes clear candidates. SQL and live acceptance remain pending.

New HTTP registrations require an inspected portrait attachment (ADR-0047); omission, keep,
remove or a client scan assertion cannot satisfy the initial intent. Transactional binding
checks ownership, staged expiry and stored payloads. UI confirmation/local previews cannot
replace that check; unavailable providers block registration. Existing version/history contracts
stay readable, and missing-portrait labels require an authorized confirmed absence, not an outage.

Portrait preparation (ADR-0044) adds authenticated bounded intake, original/derivative scanning,
Linux resource-limited decoding and context-bound AES-GCM/Vault key wrapping. Version bindings
are append-only; thumbnails require current membership and no-store responses. No original
route, deletion grant, purge worker, default key or clean-scan fallback exists. Pillow 12.3.0
is installed; unsupported Mac workers deny processing. Migration/grants, persistent providers,
recovery and real photo acceptance remain pending.
Encrypted payloads now use `persona_portrait_payloads` and the shared immutable trigger so the
unchanged migration check includes them in tenant RLS/immutability coverage. Owner approved
the four-action exact detection test extension; new SQL cases cover tenant/server-only detection.

## Creation completion and photo dependency preparation (ADRs 0042/0043)

Confirmed creation replaces the editor; Open saved record performs a fresh session-authorized read. Re-entry retains only the authored completion marker, not a cached receipt or grant.
Source/session changes hide earlier receipts/navigation; uncertain saves remain unresolved until the same intent is confirmed. Owner confirmed Pillow 12.3.0 installation; durable photo preparation supersedes the ignored draft.
Synthetic pixel/provider/ASGI probes pass; owner reports full SQL/code gate passes. Linux/live-provider acceptance and trusted cleanup remain pending. No credentials or real source photo were read; passing tests do not activate services.

## Real creation and database inventory (ADR-0041)

Creation sends only bounded authored content, a fresh request ID and initial revision intent;
server identity/membership authorizes the write. Confirmation clears on edits and navigation.
Drafts and uncertain intents stay in tab memory under workspace/session keys; no fetched receipt
is persisted. Access loss blocks saves, and another session cannot see the previous draft.
Historical sample modules are test-only; production imports none. The database inventory runs
read-only under an all-tenant operator, reports counts/legacy flags and refuses a populated
baseline. It never deletes or relabels rows. The owner initially verified 17 empty local tables;
that snapshot precedes real identity provisioning/creation. Owner reports private mode-600
backend configuration, database/Redis checks, distinct creator/reviewer bindings, real Zynth
sign-in and first save. Restricted runtime confinement/login/driver checks passed; independent
reviewer proof and revision-bound security/PR/CI acceptance remain pending. ADR-0042 prefill
uses only the current authorized snapshot when no authored draft exists; it never persists
fetched content merely by opening Edit. Photo inspection/key/retention providers remain absent.

## October 4 real integration boundary (ADR-0040)

Runtime HMAC issuance and the example endpoint are removed. Zynth signatures, distinct ID/access
profiles, per-request UserInfo, exact-tenant canonical bindings and stored membership gate real
routes. Confidential PKCE login binds state/nonce/at_hash; encrypted Redis and HttpOnly opaque
cookies keep tokens server-side. Exact Origin/JSON checks protect cookie writes. Missing config,
provider/cache failure and privileged runtime roles deny access. Auth responses are private.
Migration refuses populated sample history; no silent relabel/deletion. Operator provisioning
commits a system-attributed grant observation; login grants nothing. No refresh/global logout,
back-channel logout or membership reassignment lifecycle is claimed. The owner migrated the
local database and verified its restricted role. No real identity/provider connection is active;
changed source still requires appropriate gates, security review and live acceptance.
See [runbook](runbooks/zynth-local-integration.md). Earlier checkpoint text below is historical.


_This is the engineering security posture. For **reporting a vulnerability**, see
[`../.github/SECURITY.md`](../.github/SECURITY.md)._

## Secrets & keys

ADR-0039 replaces the default seeded browser UI with an empty workspace gallery. No initial
scenario state, role simulation, scripted findings, example governance, legacy storage restore
or sample export is available from `app/page.tsx`. Saved reads retain explicit source injection
and existing validation/access-loss behavior. ADR-0041 now supplies creation; saving requires trusted
sessions, routes, uploads, analysis, monitoring and signing are not activated. Historical tests
explicitly inject scenario state. See the [layout review](hackathon/workspace-layout-review.md).

ADR-0031 adds internal private quarantine: bounded streams, exact digest/size checks, fresh
AES-GCM envelope encryption bound to tenant/version/object, immutable metadata/inspection,
forced tenant RLS and owner-only clean/unexpired reads. No key provider, content/malware
inspector or legal-hold/retention provider is configured; none has a default-allow fallback.
Purge requires expiry and affirmative retention authorization. Cleanup is not scheduled.
Fixtures never become real campaign assets. Production promotion/retention remains gated.
ADR-0032 prepares strict transport receipts and explicit retry/conflict/cancellation recovery;
the default transport rejects and the UI remains disconnected. Owner source-bound database
validation now passes 454 tests / 96.55% coverage and full local `make check`, including
dependency audits. Provider activation and revision-bound CI/security review remain incomplete.
ADR-0033 adds bounded gallery reads under the existing workspace membership boundary and
owner-only evidence metadata reads without decryption. Queries use bound, escaped literal
search; events omit search text and identify metadata-only evidence access. Prepared history
adapters validate tenant/record/cursor binding. No routes or membership grants are activated.
ADR-0034 prepares an unregistered read router and a mandatory injected session verifier;
missing/expired/failed verification denies before database access. Scaffold tokens are not
accepted through fallback. Membership remains a per-request service check, query bodies
reject authority fields, and responses are uncached/sanitized. The separate saved-record UI
clears data on request/context/access changes and persists no server content. Real credentials,
identity mapping, revocation, origin/CSRF/TLS/headers and provider observations need review.
ADR-0035 exposes those governance concepts through a separately labelled local example, not
stored server data or the selected browser persona. It uses runtime parsers, exact review/audit
binding and cleared read state. Evidence metadata has no payload/download; inspection and
expiry do not establish rights, promotion or deletion. Audit presence remains unsigned and
unverified. Recovery captures retry intent and never changes draft records, permissions or
visibility. Backend source retains its owner checkpoint; the changed frontend still needs its
current audit/CI gate. No history/write/evidence route or provider is activated.
ADR-0036 prepares authorized version/campaign/evidence discovery and an unmounted governance
read factory. Campaign discovery filters named parties; private metadata remains owner-only,
even on empty pages. Existing authorization and observed transactions are reused. Frontend
parsers bind tenant/resource/cursor; any denied governance read clears the complete saved view
and ignores late responses without altering drafts. No synthetic verifier ships as a provider:
ASGI bridging and test identities live only under tests. New backend bytes need fresh owner/CI
SQL/full-gate evidence; the 454-test checkpoint above is historical for this changed tree.

ADR-0037 prepares an unmounted write factory using the same required session verifier before
database access. Existing services reauthorize retries, bind independent review/campaign intent
to exact versions/assets and atomically emit their registered server actions. Extra authority
fields and invalid initial revisions reject; sanitized errors/receipts stay uncached. A separate
same-origin write transport has no automatic retries, redirects or credential fallback.
Explicitly injected fixture forms require confirmation and version-bound catalogue references.
Their studio store contains only authored fields/failed or uncertain intents, not fetched data,
successful receipts, credentials or persistent localStorage. Access loss clears saved views;
different session contexts cannot display or retry prior drafts. Cancellation blocks new intent
until outcome resolution and ignores late responses. Denied retries and malformed receipts
retain uncertainty; invalid local intents are rejected before transmission. Identity/provider/CSRF/origin/TLS/header/
nonce/ingress review still gates any live connection; synthetic sessions exist only in tests.
Owner current-source SQL/full local gates pass; revision-bound CI/security review and rendered acceptance remain required;
see the [write checkpoint](hackathon/h2-write-preparation-review.md).
Owner-approved write-retry SQL fixture correction downgrades roles to `viewer`, preserving
member references, constraints and 403/no-new-record assertions. It does not implement full
membership revocation: viewers retain read membership. Owner's corrected 553-test suite passes.
The intermediate full gate blocked on braces 3.0.3 through Next's lint plugin in both npm trees;
that failure is historical. See the [audit history](hackathon/braces-audit-review.md).
Owner approved the exact private artifact's adoption, installation and temporary maintenance
(ADR-0038). Both manifests/locks pin it; docs-site installs and 20 normal regressions pass.
Owner restored both frozen trees and reports full validation exit 0 with 14 ASGI tests and
matching source/artifact hashes. Agent verifies both installed chains and 20 regressions per app.
The [dependency checkpoint](hackathon/braces-installation-proposal.md) separates local proof from pending PR/CI/security review;
no dependency/audit exemption, forced downgrade or gate change is applied.
The [PR/security readiness review](hackathon/h2-pr-readiness-review.md) records scoped SAST
with 11 applicable rules/211 Python and TypeScript targets/zero findings, approximately 99.9%
parsed lines and exit 0. This is not full SAST/credential/CI certification. Policy PR #50's
observed startup failure does not validate the uncommitted persona work. Provider integration
scope is proposed for review only; no real provider, key, upload or live connection is enabled.

ADRs 0028/0029 add local console state and honest security readiness. Storage restores only
bounded draft fields and selected record; notes, approval, roles and history are not persisted.
Public export allowlists committed fields and remains unsigned. Scripted assistance cannot
approve; creator/reviewer/recipient selectors are fixture controls, not auth. Footer presence
means local UI only. Monitoring/identity/signing remain disconnected or unavailable; no breach
assessment or live server health check is claimed. Required security decisions stay visible.

Frontend alignment review confirms no persona API calls or mounted persona routes. Note
edits invalidate demo approvals; changing drafts clears notes anchored to earlier content.
The public/private toggle remains presentation only. No real evidence, identity substitute
or browser role grant was introduced; see the frontend/backend alignment review.

- **Never in git.** Only `.env.example` (placeholders) is committed. Real values live in a local
  `.env` (gitignored) or the deployment's secret store. `*.pem` / `*.key` are gitignored.
- **Defence in depth:**
  1. `.gitignore`.
  2. The gitleaks pre-commit hook, which scans the **staged** change at commit time on a laptop.
  3. The **CI secret scan** (`scripts/secret_scan.py`), which scans the **commits** of every PR and every push to `main`. It is pinned by version and SHA-256, and proven on every run by a canary: fresh fake tokens planted in every tracked directory must all be found, or the run refuses.
  4. The `detect-private-key` hook.
- **The pre-commit gitleaks hook does not run in CI.** It scans staged files, and a CI checkout has none, so in CI it read nothing and passed every run until 2026-09-24 (ADR-0018). The CI scan above replaces it there.
- **No ignore list and no path allowlist.** Inline `gitleaks:allow` comments and `.gitleaksignore` are disabled in the CI scan. `.gitleaks.toml` may exempt only placeholder *values*, never paths; the canary refuses to run if any directory is exempt. History was triaged in full on 2026-09-24 and was clean. A secret that ever reaches the repo is **rotated**, not exempted (SEC-003).
- **GitHub secret scanning and push protection are not enabled** on this private repository. The CI scan is the server-side control.

## Fail closed

H2 exposes no persona route. The internal fixture service checks stored membership and
ownership before each write and stored membership before reads or retries. Content cannot
supply actor, workspace, roles or approval. Versions, events and replay receipts commit
atomically; triggers and tenant RLS are defined in migration 0003. Database enforcement
tests passed in the owner-reported 92-test persona/migration run (2026-10-02, 20.31s);
the agent cannot independently run Docker here. Future runtime credentials
must not bypass RLS; existing local administrator credentials are not isolation evidence.
The HMAC principal remains development scaffolding. Zynth work is deferred, with no
identity fallback. Content and credentials are excluded from events. Audit sealing and
detection delivery are distinct; unsealed auditable events survive expiry until sealing.
Receipt inspection rechecks membership and record references and logs the version read;
audit-entry presence is not a verified chain. Redis outage does not stop durable sealing.
Transaction advisory locking prevents simultaneous sealers from reading the same chain head;
its PostgreSQL concurrency test is included in the owner-reported passing suite.
Workspace backlog inspection rechecks membership, filters server events by tenant/category,
and returns counts/timestamps without content or actor lists. It records the observation;
no automatic monitoring, detection engine or public health endpoint is introduced.
Internal review persistence adds forced tenant RLS and immutable decision rows in migration
0004. Trusted human fixture context and stored reviewer roles are required; no browser grant
or real identity claim is introduced. Self-review and stale versions fail closed. Persona
head locking serializes edits/reviews; expected previous IDs prevent lost decisions.
Exact retries reauthorize and return historical receipts, never current-use permission.
Statements stay out of server events. PostgreSQL behavior tests passed in the owner-run target.
Detection scopes registered server persona observations by tenant. Internal receipts omit
actors/statements and use the command-table boundary without RLS; no route exposes them.
Authorized backlog reads record access. Retention preserves supporting persona windows
without prolonging client data. ADR-0027 documents the boundary. The owner passed the
301-test target in 50.58s with matching source fingerprints; full gates remain incomplete.
Migration 0005 adds immutable fixture assets, scoped offers/bindings/decisions and forced RLS.
Composite references refuse other tenants/versions; creator permission and named-recipient
decisions remain distinct. Change requests withdraw use; revocation cannot be undone by an
old acceptance retry. Current eligibility separately checks version/review, roles and time.
Only campaign parties may inspect scope, history or decision evidence. Evidence inspection
matches committed server references and fails on missing/mismatched rows; audit presence is
not chain verification or signing. No private upload, real identity or HTTP grant path exists.
The owner reported 279 target tests passing in 48.86s with matching source fingerprints;
the workflow review records provenance. Full gates and revision-bound CI remain incomplete.
Receipt reads refresh cold-store/audit references after retention. H1 fixture decisions also
reset on change requests and re-analysis; these browser checks remain demonstration logic,
not authorization or an alternative to trusted sessions.
Worker failure logs include an exception class, never raw exception text. Failure to store
a denial logs only its bounded request UUID and propagates the error; it cannot fabricate
a durable audit record while PostgreSQL is unavailable.
See [H2 readiness](hackathon/h2-core-readiness.md) and ADR-0024.

Outside `development` the config validator **requires** real secrets and raises if any are
missing (`accord/config.py`). Missing config / ambiguous auth → deny.

## CI configuration is attack surface (ADR-0018)

- Workflows are audited by **zizmor** at its strictest persona. No `${{ }}` expression is ever expanded inside a `run:` script; values reach the shell through `env:`.
- Each job holds only the permissions it names, each with a comment saying why.
- The Scorecard PAT (`repo` scope) lives in the `scorecard` **environment**, readable by that one job only.
- The two credentialed checkouts are reviewed exceptions, recorded inline and in `docs/runbooks/ci-integrity-checklist.md`.
- **A release needs a green default-branch run for its own commit** (REL-035). Ancestry of `main` proves only that the pull request passed. The release preflight also requires the commit's latest CI push run on `main` to have completed green. A missing push run fails: GitHub delivered none for the merge of #31.

## The AI agent's boundary (ADR-0019)

The unchanged controls and their evidence limits are retained in
[agent boundary security](security-agent-boundary.md).

## Supply chain

Existing controls and remediation evidence are preserved in [supply chain security](security-supply-chain.md).

## Runtime hardening

- **Local delivery boundary (ADR-0022):** the owner-run local stack publishes only loopback
  ports 18660/18662/18663; foreground public docs use 18661. Startup refuses conflicts,
  validates resolved Compose isolation and never stops another project. Local-only secrets
  live in ignored `.cache/local-stack/runtime.env` (600, directory 700); root `.env` is
  not used. Project-specific networks, image tags and persistent volumes isolate checkouts.
  Shutdown preserves data. Production TLS, signatures and both agent policies remain separate.
  Fault tests cover these controls; owner evidence confirms successful Docker startup,
  migrations and HTTP readiness. All four observed host listeners bind only to 127.0.0.1.

- Containers run as a **non-root** user.
- Least privilege for the app's DB role; back up before destructive migrations.

## Published documentation

The docs site (`docs-site/`) publishes **only** `docs/public/`. This is an allowlist, set in
`docs-site/lib/docs.ts`. Everything else under `docs/` is internal and must never be published:
the architecture, ADRs, requirements to other teams and the standards. Put a file in
`docs/public/` only when it is safe for anyone to read.

The rule is enforced in CI, not only by review. `docs-site/tests/` runs the real loader in the
`docs` job and in `make docs-site`, and fails if:
- a published document resolves outside `docs/public/`;
- a Markdown file in `docs/public/` is not published;
- any other file under `docs/` is published;
- nothing is published at all.

A fixture tree proves the loader never follows a symlink, and never serves a `..` or path slug.
It was doing both before the harness existed (2026-09-25). Put no symlink in `docs/public/`:
the loader ignores it rather than publishing its target.

## Any security-relevant change

Note it here and tag the commit `security:`.

## Persona prototype requirements (planned, ADR-0023)

The [prototype plan](hackathon/prototype-plan.md) requires server-enforced creator/reviewer
permissions, private evidence by default, controlled publication, tenant-scoped encryption
with KMS wrapping, separate encryption/signing keys and no personal data in signed manifests.
Model access is limited to authorized evidence; image embeddings are protected derived data
and cross-workspace search requires an explicit public projection or permission grant.
Uploads need type/size validation, quarantine and scanning before model or public use.
Approval and issuance bind the exact reviewed version; all new server actions retain spine
coverage and attribution. UI animation and browser telemetry are not evidence of completion.
Public verification checks a trusted platform key, not an arbitrary key supplied by an export.
These requirements are not active product controls yet. No policy, guard or licence changes
are made here. Source publication follows the [publication record](hackathon/publication-record.md)
and requires owner approval; the docs-site allowlist does not protect a public Git repository.

## Private passport booklet (ADR-0075)

The display reads existing authorized gateways only. No new route, stored shape or telemetry
claim is added. It never exports or approves on open. Only approved references supply portraits.
Private package bindings and server verification precede owner-only publication history; unsigned
reviewer previews never invoke that history. Session/version/offer changes clear retained packages;
abort checks reject late completions. No package or portrait is stored in browser storage.
Seal/QR need valid package verification and a nonwithdrawn approved public projection. The QR
contains only the approved same-origin public URL. Public availability is not inferred from the
private receipt, and a signature does not prove identity, rights or continuing use permission.
No backend/security setting, scanner freshness, public flag or cloud runtime is changed. 566 frontend tests, types/lint and optimized build pass on Node24. Production Node22,
rendered/accessibility/print and live signing/sharing acceptance remain unverified.
