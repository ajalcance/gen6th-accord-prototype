# Changelog

All notable changes to Gen6th Accord are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/).

## [Unreleased]
- 2026-10-17: prepare the approved paper Persona Passport booklet (ADR-0075). View passport
  opens saved records above the offer list, including empty portrait/no-offer previews. Real
  fields and approved references replace example content. Seal/QR require valid server package
  verification and approved sharing; current permission is separate. No export/approval on open.
  566 frontend tests, types/lint/build pass on Node24; Node22/render/print/cloud/live proof is open.

- 2026-10-17: add an optional advisory reviewer brief (ADR-0074). A saved version's four text
  fields go to Gemini on Vertex AI on an explicit click and return a plain-text summary, gaps and
  questions. Disabled by default through `PERSONA_ASSISTANT_ENABLED`, per-actor rate limited,
  unstored, with a fixed advisory notice. New route, contracts, adapter, frontend gateway and panel.

- 2026-10-13: review prepared app dependency fixes against28 owner alerts; confirm tinypool removal, private braces identity and514/31 tests. PR66/main CI accepted; metadata142 records/87 packages accepted; retain tested Vite8. Focused preview27/31 tests passes; owner fresh installs/full gates pass; temporary tooling link removed,28 hashes/population and frozen source verified. PR67 mergedf466978; exact-main pushCI38336603073 passes applicable app/static gates. Equivalent patch repair preserves approved archives/source/locks; integrated full local checks pass. Owner API reports zero open Dependabot alerts. [Application integration preparation](docs/hackathon/application-integration-2026-10-13.md) passes preview DoD; policy PR77 mergedb2ddb6c with exact-main CI38341957279 green; application full local gate passes (1447 backend,94.15%;514 frontend;31 docs;987 guards/18 skipped); Trust/DoD pass. Three documentation scan matches are reworded; clean unpublished commit preparation preserves controls/locks and completed code checks. PR78 head d67ecd8 passes Linux backend/frontend/static/hygiene and custom SAST; community SAST flags two legacy HTTPSConnection calls. Candidate replaces them with HTTPS-only transport, explicit certificate/hostname verification, no redirects/proxies, timeout and response bounds;54 auth tests, lint/types/Bandit pass. Owner custom/community scans pass at7c70939; full check found test-double typing errors. Candidate uses real parsed HTTPResponse doubles;54 auth tests and full mypy414 sources pass, preserving TLS/redirect/size assertions. Full repaired-head checks and CI remain required; native deployment pending. [Review](docs/hackathon/application-dependency-review-2026-10-13.md).

- Prepare ADR-0069 fixed scanner managed runtime: real release-bound seeds/config validation,
  signature/update/load commands, loaded-byte binding and cancellation-owned process acquisition.
  63 new tests and 150 combined tests pass; mypy 410 sources. Checkpoint 15 verifies 1414 backend/94.10% and all later phases;
  current hashes match, pasted exit omitted. ADR-0070 proposes real artifact/release evidence design;
  Prepare real production factory, verified-seed/config emitter and explicit proposed source inventory: 33 new/183 combined tests pass; checkpoint 16 saved log verifies 1447 backend/94.13% and all later phases; current hashes match, pasted numeric exit omitted. ADR-0071 preparation approved: isolated four-file guardrail review patch has 129 passing tests, manifest/config digest binding and lint/format/strict typing; separate PR and CI/release wiring pending; upstream source hashes/toolchain candidates and owner index/Linux-amd64 metadata identified, actual verification/locks open. No mock data/native execution/build/cloud action. Owner published draft [PR #60](https://github.com/ajalcance/gen6th-accord/pull/60), head `116fa14d9d82a9e12dbae4a268db89086d549a4a`: Linux guard tests fail with E2BIG before oversized-input CLI execution (864 passed, 1 failed, 18 skipped). Short IDs are now prepared in the separate checkout, preserving the full payload/denial checks; published at 36cc85addeb8; exact-head Linux guards pass (865 passed/18 skipped), policy/harness pass; owner applied guardrail-change and fresh CI run 38241515740 passes including meta-guard/ci-complete; owner merged PR #60 as 524dbbb18d9c2065af29ab1c017ce453ae93f9cf; exact main push CI run 38244164224 passes, including 865 guards/18 skipped, policy/harness and ci-complete; application/native acceptance remains pending. Owner authenticated API confirms all 21 alerts (3 critical/7 high/11 medium); [triage](docs/hackathon/dependabot-owner-triage-2026-10-12.md) reconciles 13 PyJWT CI-lock alerts and eight app-lock alerts. Existing app fixes remain unmerged; Owner approved separate CI-lock repair preparation: Semgrep1.179.0 / PyJWT2.15.0 meet the cooldown; scratch resolver freezes78 other packages and rejects unrelated hashes/markers. Owner resolver path-space failure fixed using relative paths; twelve checkpoint tests/lint/typing pass; October13 owner candidate lock hash verified: only two packages changed, 78 unchanged; tracked dependencies unchanged. New isolated package/scanner checkpoint passes four offline faults and lint/typing; Actual ten PyJWT regressions pass; CLI1.176.0 versus installed1.179.0 blocks scanner acceptance. Separate installed-bin-first checkpoint requires CLI/core1.179.0; bound CLI/core both1.179.0 confirmed. Core labeled-output parser fixed; 15 offline faults pass. Hash-bound resume skips completed versions; Bound scan acceptance confirmed:16/16 rule faults,121 targets/0 findings. Canonical lock regenerated offline with identical80 package/marker/hash blocks. Seven review files prepared; local985 guards/18 skipped, policy and harness commands pass. Owner local branch/commit/declaration checkpoint prepared; no push/PR/CI yet. No Actions triggered. [Integration scope](docs/hackathon/scanner-release-integration-scope-2026-10-12.md) maps isolated scanner ADR-0021 to application ADR-0072; separate release integration is owner-approved and staged (ADR-0073): scanner assembly/signature/layer checks and read-only destination verification; genuine producers and new PR/CI remain pending. Owner review/label, exact-head CI and mandatory release wiring remain pending; Dependabot alert identities are owner-verified; remediation remains open. See [October 12 handoff](docs/hackathon/next-session-2026-10-12.md).

- Complete scanner candidate/runtime metadata review: record platform/index identifiers, matching
  source defaults, seed/update trust and Python packaging gaps. Propose fixed configuration and
  cancellation-safe process launch; source/contracts unchanged, no image/runtime/cloud execution.

- Prepare approved scanner health/supervision adapter (ADR-0068): required internal managed runtime,
  prepare-before-start, exact two live children, unchanged fixed freshness probe and health-only
  HTTP. Bound startup/TERM/KILL/reaping, shield failure cleanup from stop cancellation and deny
  uncertain completion. 33 new synthetic tests and 40 existing scanner/provider tests pass;
  mypy checks 404 sources. Checkpoint 14 log verifies 1351 backend/93.94%, Trust, 514 frontend,
  31 docs-site, audits and builds; current hashes match, pasted exit omitted. No activation.

- Complete scanner packaging review: identify upstream bootstrap validation and child-supervision
  gaps, native freshness health, idle CPU/writable-storage requirements and missing signed scanner
  release integration. Record bounded follow-up source/release/rehearsal scopes and measurement
  criteria; no images, runtime configuration, guards or cloud resources changed.

- Prepare approved compliance worker-pool lifecycle `accord.compliance:app` (ADR-0067) with strict
  configuration, existing role verification and unchanged worker passes. Add monotonic progress
  health, bounded startup/cancellation/Redis cleanup and generic errors. Preserve separate stage
  commits and active-transaction rollback; healthy passes do not claim Redis/delivery completeness.
  Checkpoint 13 log verifies 1318 backend/93.86%, Trust, 514 frontend, 31 docs-site, audits and
  builds; both SQL lifecycle tests pass, current fingerprints match, pasted numeric exit omitted.
  Existing processing/guard implementations and accepted artifacts unchanged; no cloud activation.

- Prepare approved reference-only ASGI process `accord.reference:app` (ADR-0066), strict independent
  configuration and existing authenticated task routes/role guard. Retain full queued-job config
  binding; exclude browser, Redis, scanner, signing and investigation providers. Add synthetic
  config/signed-OIDC/factory tests and disposable SQL completion/replay test. Checkpoint 12 log
  verifies 1285 backend/93.81%, Trust, 514 frontend, 31 docs-site and builds; current hashes match,
  pasted numeric exit omitted.
  Reference reconciliation IAM and credentials remain pending; no grants/deployment or queue resume.

- Prepare approved production composition inventory/contract (ADR-0065). Non-development inspected
  startup requires the fixed bounded scanner receipt after role verification; startup failures and
  cancellation close the assembled runtime. Preserve development behavior and existing scan/role
  guards. Checkpoint 11 log verifies 1263 backend/93.79% and all later phases; current hashes match.
  The pasted numeric exit is omitted; verified log evidence is recorded separately.
  Reference-only assembly subsequently passes source acceptance; worker health/signals, scanner
  packaging/sizing and routing remain pending.
  No images, credentials, deployment or cloud mutation; Tasks paused and Zynth later.

- Prepare approved distinct production SQL role profiles (ADR-0064), exact-head operator SQL,
  non-deployable contract and source-bound privilege inventory. Roles remain NOLOGIN; evidence
  INSERT matches intake, original deletion stays excluded, existing guards/revisions unchanged.
  Add 32 collected disposable permission/precondition and API/reference/compliance journey tests;
  PostgreSQL/full gate pending. No production SQL, credentials or cloud mutation.
  Correct the denial test's nonexistent hardcoded postgres target to the actual disposable operator;
  retain SQLSTATE 42501 and full diagnostics. SQL/grants unchanged; owner rerun pending.
  Owner disposable SQL acceptance passes all 32 tests (24.04s). Full gate stops at duplicate
  conftest module; add the new test package marker. Exact mypy . passes 381 files; full rerun pending.
  Full-check-10 subsequently exits 0: 1249 backend (93.58%), Trust, 514 frontend, 31 docs-site,
  builds/audits and DoD; source/SQL/contract fingerprints match before/after. Production remains pending.

- Prepare approved scanner readiness callable/CLI with exact loopback PONG/fresh VERSION checks,
  a five-second deadline and generic outcomes. Bound scanner stream cleanup; preserve scan guards.
  Add framing/failure tests and a non-deployable image/resource/update contract; full phases verified.
  No scanner image/install/start, capability activation or cloud mutation.
  Repair the future-definition test's collection-time timestamp; add fixed-clock freshness-boundary
  checks. Production thresholds unchanged; corrected full-check-8 verifies 1217 backend (93.58%),
  all later phases and DoD on October 12; numeric exit line omitted from the supplied paste.

- Prepare approved operator migration runner with bounded loopback startup/shutdown, fixed
  revision targets, generic failure reporting and finally disposal of the Alembic NullPool engine.
  Add failure/deadline regressions and a grant-sequencing matrix; full gate passes: 1185 backend
  (93.45%), all later phases/DoD, matching fingerprints before/after; live acceptance pending.
  Frozen migration revisions, role/grant guards, release workflows and cloud resources are unchanged.

- Fix job-trigger SQL parsing in migration and model schemas; retain job IDs/worker sequence
  across rollback so queue/provider outages preserve durable recovery receipts. Extend the
  explicit detection test for registered asset/passport/publication actions and SQL recovery
  regression coverage. Store absent production metadata as SQL NULL, fit investigation-review
  telemetry to its existing bound, and test preserved/removed search references per ADR-0050.
  Owner full repair gate passes: 1108 backend (93.12%), 514 frontend, 31 docs-site tests,
  Trust/builds/audits/DoD. Both JS manifests/locks resolve sharp 0.35.5/source-map-js 1.2.2.
  [Repair evidence](docs/hackathon/backend-test-repair-2026-10-11.md).
  Subsequent [Redis CA preparation](docs/hackathon/redis-ca-preparation-2026-10-11.md) shares
  verified TLS/mounted CA wiring across both clients; rejects verification URL overrides.
  Full gate passes: 1122 backend (93.26%), all later phases/DoD green; live mounts/TLS pending.
  Owner-approved SQL proxy transport now validates loopback/credentials and rejects URL overrides
  and known admin runtime logins. HTTP/compliance share bounded pools and connect waits;
  migration NullPool is retained. ADR-0063 and a non-deployable proxy contract record pending
  image/lifecycle/role/live acceptance. Full gate passes: 1147 backend (93.40%), all later phases
  and DoD, with matching source/contract fingerprints before/after. No cloud changes.

- Record owner Google provisioning/IAM checkpoints, paused Tasks queue and empty deployment
  inventory. Update G0–G8 status and preserve minimum-sizing/Zynth-deferral choices. Add the
  [October 11 transition](docs/hackathon/next-session-2026-10-11.md) with source fingerprint and
  backend gate failures (795 passed, 2 failed, 307 errors; 81.25% coverage). Fixes remain for
  the next chat; no application, production schema or capability was deployed/activated here.

- Prepare accountable performer lifecycle (ADR-0062): operator/authority, time-bounded rights and
  creator-declared provenance, separate independent assessments, private trials, reassessment and
  concerns with performer-wide suspension. Add Rights & operator forms/history and fresh production
  permission checks. Prepare migration 0018 and confined grants; activation defaults disabled.
  Retain all L1–L10 adaptations and future acceptance criteria in the
  [development register](docs/hackathon/performer-lifecycle.md). No cloud/schema activation.

- Record owner-approved production-first Google deployment with Zynth sign-in and no separate
  staging (ADR-0061). Add the G0–G8 step-by-step bootstrap/evidence runbook covering project/billing,
  reviewed release, networking/data, keys/scanner, login, workers, recognition and live acceptance.
  Deployment configuration was pending at that preparation; later owner provisioning is recorded
  in the [cloud inventory](docs/runbooks/google-production-inventory-2026-10-11.md). Release gates remain.

- Give Analysis, Production & use and Passports distinct entry guidance and selection actions.
  Fix the exposed performer label and narrow search field; compact the shared picker and wrap
  actions at narrow widths. Preserve performer/version selection across workflow pages.
  Refines ADR-0059; updated layout awaits owner rendered review.

- Add persistent performer identity/provenance, optional aliases and structured contributor
  credits with authenticated self-confirmation of exact declarations. Add bounded version-scoped
  production history without inferring actual appearances. Existing passport/review projections
  exclude credit annotations. Prepare migration 0017/append-only grants; credits default disabled.
  Record every ORCID-inspired future item O1–O8 and acceptance criteria in the
  [development register](docs/hackathon/performer-identity-and-credits.md), ADR-0060.

- Audit workspace layouts across all destinations after owner screenshot feedback: compact aligned
  performer picker, scoped feedback, contextual headings, consistent workflow/forms/Settings/public
  passport spacing and cursor-aware pagination. Review-request history lives in Independent review.
  See [layout audit](docs/hackathon/workspace-layout-audit-2026-10-06.md); rendered acceptance remains open.

- Correct local sign-in startup instructions to preserve the previously used process-only
  `PERSONA_API_ENABLED=true` override. Saved private configuration and activation boundaries remain.

- Redesign the performer workspace: toolbar image search, retained catalogue pagination/display,
  version-scoped analysis/production/passport pages, progressive System Capture and compact
  interactive Capture helper. Add Settings, an evidence-reference picker, public-recipient preview
  and separate private issuance/verification controls. Existing save/scan/permission gates remain.
  Compact forms use single visible labels and placeholder hints; Register persona makes
  first-reference approval explicit, with helper guidance replacing repeated footer instructions.
  See [review checkpoint](docs/hackathon/workspace-redesign-2026-10-06.md), ADR-0059.

- Add October 6 next-chat handoff preserving the owner frontend-review checkpoint, current
  source fingerprint, validation limits and remaining recognition/runtime acceptance tasks.

- Extend offline recognition evaluation with optional corpus-byte validation, input fingerprints,
  per-case failure/scored counts, latency percentiles and unknown cost. Add bounded local report
  inspection in Connection & readiness. Real recognition accuracy and Google rehearsal remain
  pending. See [workflow](docs/hackathon/recognition-evaluation-workflow.md), ADR-0058.

- Add private PNG/JPEG/text evidence upload, inspection, exact-byte download and capability status,
  with encrypted quarantine and separate explicit production asset registration in the frontend.
- Persist private passport issuance per campaign acceptance, reuse committed export retries and
  add owner-approved public field previews, signed public packages, share links/local QR codes,
  public verification, approval history and withdrawal. Public serving is disabled by default.
- Prepare migration 0016 and confined append-only runtime grants. Live SQL, scanner, keys,
  retention authority, ingress limits, Google infrastructure and rendered acceptance remain pending.
  See [S8–S10 evidence](docs/hackathon/evidence-assets-public-passport-slices.md).

- Prepare S7 opt-in Google runtime and recoverable face jobs (ADR-0055): explicit Cloud Run
  workload access, KMS context/CRC wrapping and retained-key routing, Cloud Tasks OIDC delivery,
  durable intent/transition ledger, bounded reconciliation and atomic encrypted completion.
  Expose studio configuration, queued detection/selection, recent jobs, exact retry, CAS recovery,
  cancellation and completed-result reload. Prepare migration 0015/SELECT-INSERT grants;
  cloud/key/schema activation and measured/rendered rehearsal remain pending.

- Prepare S6 production clearance and passport integrity (ADR-0054): named production/episode/
  role/adaptation and submitted evidence references on exact-version campaign offers, owner asset
  discovery and current permission. Expose studio fields, status/history and signed export/file
  verification controls, including altered-package rejection. Add injected Ed25519 trust and
  Google KMS adapter plus migration 0014, without live key/cloud/schema activation.

- Prepare S5 grounded investigation (ADR-0053): fresh server-authorized search evidence,
  structured Vertex Gemini comparison/abstention, mandatory evidence gaps and encrypted immutable
  exact-version findings history. Expose explicit retained analysis, retry/cancel/receipt/history
  and saved independent review requests in Records. Prepare migration 0013 and confined grants;
  no live model, SQL, signing or web-discovery activation.

- Prepare S4 private calibrated similarity serving (ADR-0052): exact cosine across compatible
  approved references, persona grouping, threshold/margin abstention and fresh scope checks.
  Expose manual query preparation, numbered face confirmation, current/history scope, method
  evidence, candidate comparison and expiry/clearing in Records. Inject encrypted Redis storage
  with ten-minute absolute expiry; ship no production calibration or live provider activation.

- Prepare S3 explicit face detection/selection, provisional quality and normalized square crop,
  encrypted face/whole-image representations and Google REST candidate adapters (ADR-0051).
  Expose numbered boxes, confirmation, availability, quality, provenance and exact retry in
  Records. Add offline permitted-manifest held-out evaluator and migration 0012faces/grants.
  Actual corpus/model evaluation, SQL/Linux/Google/browser acceptance and activation remain pending.

- Prepare S2 dedicated 1024px analysis derivatives, immutable context-bound encrypted capture
  provenance and ordered reference sets (ADR-0050). Scan all three image parts before atomic
  intake; expose capture metadata and explicit reference approval/remove/reorder in Records.
  Version saves preserve history and exact retries; exact-file search includes approved references.
  Add migration 0011captures and confined runtime grants for owner review, without activation.

- Create seven capture/search implementation slices with backend-to-frontend coverage. Add S1
  studio-authorized exact-file portrait search (ADR-0049), visible in Records with manual query,
  validated evidence, empty/error/retry/cancel states and fresh matching-version inspection.
  Queries are not enrolled or stored; facial similarity and actual Google execution remain future
  slices. Runtime/photo schema activation and SQL/live acceptance remain pending.

- Record the owner-approved future-industry direction for AI Persona Passport (ADR-0048):
  persistent synthetic-performer identity, visual reference enrollment, measured face-based
  catalogue search, studio evidence/use investigation and production clearance. Stage future
  web discovery and voice/video monitoring. Update plans and acceptance; documentation only,
  with no recognition implementation, runtime activation or new rights/accuracy certificate.

- Require an inspected portrait for new System Capture registrations in the UI and HTTP API
  (ADR-0047), with explicit Scan before saving. Mark confirmed image-free historical versions
  Incomplete — portrait required; separate loading/unavailable photo states from missing images.
  Provider activation remains pending, so new registrations cannot complete until scanning works.

- Make Scan the explicit photo ingestion action below the portrait picker in System Capture
  and editing. Selection only previews; show scan progress/completion and preserve exact retries.
  Photo services remain unactivated; unchecked selected photos still block saving.

- Rename the persona entry workflow to System Capture across the sidebar, Quick Actions,
  Records, page/forms, guide, save/completion actions and accessibility labels (ADR-0046).
  Preserve existing records, session drafts and persona API contracts.

- Record the owner's successful full `make check` for the corrected portrait schema/detection
  source. Frontend and docs builds/audits pass; browser and live photo activation remain pending.

- Align encrypted photo payloads with `persona_` schema enumeration and shared immutable
  protection. Preserve migration checks; apply the owner-approved exact detection inventory
  extension and add tenant/server-only portrait detection regression tests.

- Redesign Creation with compact details on the left and a prominent uncropped portrait panel
  on the right, stacked above details in narrow workspaces (ADR-0045). Add accessible photo
  selection, filename and local preview without a connected photo service. An unchecked
  selection must be checked or discarded before saving; photo runtime activation remains pending.

- Prepare optional creation/editing photo selection, checked upload, exact retry/cancellation,
  private saved thumbnails and immutable add/keep/replace/remove version binding (ADR-0044).
  Separate encrypted portrait storage, scanner/key adapters, migration and narrow grants exist
  for review. Pillow 12.3.0 is confirmed installed; Mac worker memory limits are unavailable.
  Linux runtime, durable services, SQL/full-gate validation, live acceptance and trusted retention
  cleanup remain pending. The running connected backend and populated records were not changed.

- Replace successful persona creation with a focused completion screen, collapsed storage
  receipt and Open saved record / Create another persona actions (ADR-0043). Preserve uncertain
  drafts/retries and block duplicate submission on re-entry; reopening uses a fresh authorized
  read. Owner has since confirmed Pillow 12.3.0 installation. Photo runtime activation remains pending.

- Refine Records with one integrated search action, aligned Refresh/Grid/List controls,
  inline singular-aware counts and a contextual Create persona action. Compact cards show
  the actual biography, revision, saved date and unsigned state with a visible Open record.
- Add direct Edit persona with saved text prefilled, preserve session-scoped authored drafts
  and show Record ID in the storage receipt. Record authorized photo work separately;
  upload, image inspection, encryption providers and retention are not active yet (ADR-0042).
  Current validation: 273 frontend unit / 15 isolated ASGI tests, static/build/budget/docs pass;
  the full gate stops at pip-audit bootstrap. Rendered and photo acceptance remain pending.

- Record owner backend Python connection success as `accord_runtime` through Mac port 18662.
  Save the real-data continuation handoff: persistent runtime configuration, Zynth approval,
  real authenticated record acceptance and evidence/provider work remain pending.

- Record successful password TCP authentication as `accord_runtime` inside PostgreSQL.
  Prepare a Mac port-18662 probe through the real backend Python session factory and privilege
  verifier; persistent runtime configuration and authenticated application acceptance remain open.

- Record owner creation of `accord_runtime`, successful application privilege preflight and
  unchanged empty application inventory. Owner password setup reports no error; TCP/backend
  login and live identity remain unconfirmed. Prepare the explicit password-authentication check.

- Record successful owner local migration to `0009identity`, 17-table inventory with zero
  application rows and empty Redis. Prepare restricted-role privilege verification using the
  application's exact preflight query; runtime role, password/login and Zynth remain pending.

- Record owner full validation exit 0 with matching current backend/frontend fingerprints and
  15 ASGI tests. Prepare the exact local migration/re-inventory command; actual application
  migration, runtime-role preparation and authenticated browser acceptance remain pending.

- Record the owner-run local storage baseline: PostgreSQL has only scaffold tables and zero
  application rows; Redis keyspace is empty. Persona schema migration, confined runtime-role
  preparation and current full/live acceptance remain pending.

- Add real persona creation with bounded authored fields, explicit confirmation, verified-session
  saves and exact-intent recovery. Validate saved receipts, retain private drafts in tab memory
  and require explicit new-form preparation after success (ADR-0041). Move historical sample
  modules into regression tests; no application sample workflows or imports remain.
  Prepare an operator-only read-only database inventory across application schemas, with seven
  SQL regressions. Populated stores require provenance review; no rows are deleted or relabelled.
  Frontend: 271 unit / 15 isolated ASGI tests pass. Live inventory/SQL/browser proof remains open.

- Remove runtime sample flags and the scaffold example/HMAC identity path. Prepare real
  record migrations, canonical workspace provisioning and confidential Zynth OIDC sessions
  with PKCE, per-request UserInfo, encrypted Redis and confined DB-role checks (ADR-0040).
  Connect the frontend through same-origin verified sessions; defaults remain disabled.
  Exact owner setup and pending SQL/live acceptance are in the Zynth integration runbook.

- Replace the default sample persona journey with an empty workspace gallery (ADR-0039).
  Consolidate actions in the header, place passport guidance in the guide FAQ, shrink
  search/Grid/List controls and retain readiness only in the footer. Remove repeated gallery
  titles, subtitles, source labels and the large informational summary panel.
  Header actions use minimalist transparent controls with visible keyboard focus. Rename
  all visible Gallery terminology to Record/Records, including navigation and accessibility labels.
  No sample-source toggle, scripted workflows or demo banner remain in the default view;
  real sessions, creation, analysis, uploads and signing remain unavailable pending integration.
- Reconcile write-validation status with the successful owner local gate. Prepare separate
  PR review units, scoped security-review evidence and a proposed evidence-provider fault matrix;
  revision-bound CI and browser acceptance remain open. Renew the bounded review/preparation
  window to 21:07:44–23:07:44 Manila on October 3; no provider or route is activated.
- Record the corrected owner's 553-test backend/Trust pass and the remaining braces audit
  blocker in both npm trees. Owner approved remediation preparation; an isolated Node 22 patch
  experiment passes in both trees. Fetched fork inspection is complete; an exact private artifact
  also passes 764 released cases. Owner approved installation/maintenance; both app manifests
  and locks pin the artifact with ordinary regression tests and Docker-context archive copies.
  Owner restored both locked trees and reports full validation exit 0 with 14 ASGI tests and
  matching source/artifact fingerprints; agent verifies both installed chains and 20 regressions per app.
- Correct the owner-approved PostgreSQL write-retry fixtures to downgrade write roles instead
  of deleting referenced members. Preserve 403/no-new-record assertions and database constraints;
  complete membership revocation is separate work. Corrected SQL and owner full local gates pass;
  revision-bound PR/CI and activation review remain separate.
- Prepare session-gated persona writes (ADR-0037): unmounted version/review/campaign operations,
  explicit write-only transport and structured fixture forms. Confirmation clears after edits;
  cancellation, navigation and permission loss preserve authored drafts/exact retry intent in
  memory while discarding fetched views. Catalogue absence denies offer preparation. Identity,
  providers, real application connection and deployment remain gated; current proof is in
  `docs/hackathon/h2-write-preparation-review.md`.
- Record the owner-supplied organizer clarification that submitted solution/material rights
  remain with participants. Explicit boundary/eligibility/source-packaging questions stay open;
  rights notice and MVP transition order are reconciled without licensing or visibility changes.
- Prepare record-bound saved governance (ADR-0036): bounded authorized version, campaign and
  private evidence discovery; exact-version review/decision/status/audit panels; shared permission
  loss clears saved data while preserving drafts. A separate unmounted read router and inactive
  read-only transport are tested through isolated ASGI serialization. Real-service PostgreSQL
  journeys are prepared for owner/CI validation. Default connection and providers remain inactive.
Earlier prototype preparation continues unchanged in
[the prototype changelog](docs/changelog-prototype-history.md).

Foundation Added/Changed/Security entries continue unchanged in
[the foundation changelog](docs/changelog-foundation-history.md).
