# Gen6th Accord — Current State (As-Built)

Prepared booklet (ADR-0075): `frontend/app/passport/` adds `passport-booklet.tsx`,
`booklet-read.ts`, `booklet-identity.tsx`, `booklet-records.tsx`, `booklet-ornaments.tsx` and
`booklet-paper.css`/`booklet-records.css`/`booklet-responsive.css`; `frontend/lib/passport-booklet.ts` maps exact-bound record fields.
`frontend/public/passport-booklet/` holds the original Accord logo and native security-pattern SVG.
No fixture portrait ships. SavedPassports retains only an explicitly exported private package in
memory, cleared across session/version/offer changes. Existing capture/status/verification and
publication-history gateways supply the display; previews never read owner-only publication
history. Permission is timestamped separately, not inferred from the signed seal. Issued display
also needs a nonwithdrawn approved share link and local QR encoding. Public link availability,
566 frontend tests/types/lint/build pass on Node24; Node22/browser/print/cloud proof remains open.

_What exists today; target intent lives in [`../ARCHITECTURE.md`](../ARCHITECTURE.md)._

> **Kept current every change (CLAUDE.md §2).** `scripts/dod-check.py` (`doc-guards`) requires
> every backend module and top-level directory to be named here; missing coverage blocks the PR.

_Synced: 2026-10-13; [application dependency review](../hackathon/application-dependency-review-2026-10-13.md): existing locks use Next16.3.8/Sharp0.35.5/source-map-js1.2.2/Vitest4.1.11 and approved private braces; tinypool absent throughout.514/31 tests and lint/types pass. Main2c7d972 CI accepted with application jobs skipped;28 app alerts remain open in owner inventory. Metadata142 records/87 packages accepted; retain tested Vite8; focused preview27/31 tests passes. Owner fresh installs/full gates pass; temporary tooling link removed,28 hashes/population and frozen source pass. PR67 mergedf466978; exact-main pushCI38336603073 passes applicable app/static gates. Equivalent patch repair preserves approved archives/source/locks; integrated full local checks pass. Owner API reports zero open Dependabot alerts. [Application integration preparation](../hackathon/application-integration-2026-10-13.md) passes preview DoD; policy PR77 mergedb2ddb6c with exact-main CI38341957279 green; application full local gate passes (1447 backend,94.15%;514 frontend;31 docs;987 guards/18 skipped); Trust/DoD pass. Three documentation scan matches are reworded; clean unpublished commit preparation preserves controls/locks and completed code checks. PR78 head d67ecd8 passes Linux backend/frontend/static/hygiene and custom SAST; community SAST flags two legacy HTTPSConnection calls. Candidate replaces them with HTTPS-only transport, explicit certificate/hostname verification, no redirects/proxies, timeout and response bounds;54 auth tests, lint/types/Bandit pass. Owner custom/community scans pass at7c70939; full check found test-double typing errors. Candidate uses real parsed HTTPResponse doubles;54 auth tests and full mypy414 sources pass, preserving TLS/redirect/size assertions. Full repaired-head checks and CI remain required; native deployment pending; no runtime change._
ADR-0061 production-first setup: [owner foundations/IAM inventory](../runbooks/google-production-inventory-2026-10-11.md), [G0–G8](../runbooks/google-production-bootstrap.md); no Google manifests/deployment yet.
[Approved SQL preparation](../hackathon/sql-transport-proposal-2026-10-11.md), ADR-0063, implements transport/pool bounds alongside Redis CA support; full gate passes: 1147 backend (93.40%), 514 frontend, 31 docs-site, Trust/builds/audits/DoD, matching source/contract before/after. Zynth/CI/rendered/recognition/runtime proof pending.
Approved migration_job runner/finally disposal and grant matrix pass full gate: 1185 backend (93.45%), all later phases/DoD, matching fingerprints before/after. Owner reports setup/bindings/sign-in/first save; persistent enablement false, process enabled; reviewer proof pending.
ADR-0064 [SQL role preparation](../runbooks/google-sql-role-preparation.md): distinct API/reference/compliance NOLOGIN contracts and exact-head SQL; evidence INSERT, narrow lock-column grants and PUBLIC CREATE/TEMP closure; 32 disposable tests pass, full gate passes. No production SQL/credential activation. Owner reports local sign-in restored after process-flag correction. Package collision repaired; full-check-10 exits 0: 1249 backend/93.58%, Trust, 514 frontend, 31 docs-site, builds/audits/DoD; hashes match before/after. CI/signed release and live grants pending.

Records tools/cards, prefilled editing, Record IDs and `creation-completion.tsx` exist. Confirmed System Capture focuses success/fresh reads. Session markers prevent duplicates; receipts are not restored.
Progressive details/compact portrait pair; new registrations require inspected portraits/explicit Scan. Confirmed missing historical portraits are incomplete; unavailable providers do not prove absence.
ADR-0059 adds toolbar image modes, retained page/query/display, performer/revision journey context, record sections/version picker, scoped production-reference selection and split passport actions.
`capture-helper.tsx` guides missing inputs on demand; sidebar Settings exposes capabilities, local recognition reports and tab-only display preferences. No new route, schema or activation.
Capture uses single field labels/placeholder hints and explicit first-reference confirmation beside Register persona; connected drafts no longer show the repeated footer instruction paragraph.
`workspace-pages.ts` provides journey-specific entry purpose/actions; `performer-picker.css` sizes the full-width search and compact selector. Global CSS shares hidden labels; `workspace-polish.css` compacts feedback/forms/settings/public layout. Analysis history stays in Independent review.

ADR-0062 adds `lifecycle_contracts`, `lifecycle_models`, `lifecycle_repository`, `lifecycle_evidence`, `lifecycle_service`, `lifecycle_reads`, `lifecycle_http`, `lifecycle_policy`:
forced-RLS immutable declarations, independent assessments, concerns/responses; three private session-gated lifecycle routes.
UI `persona-lifecycle.ts`/contracts/reads, performer-lifecycle, lifecycle dossier/assessments/concerns/form/fields/state/use expose Rights & operator, bounded history and production binding.
Current offer/acceptance/status/export/verification enforce operator, dossier, assessment/rights expiry and performer-wide suspension when enabled; trials are private and at most 30 days.
Migration 0018lifecycle/SELECT-INSERT grants are prepared; `PERSONA_LIFECYCLE_ENABLED=false`. Evidence hashes persist without extending private-original retention. Private dossiers are excluded from passport projections.
[L1–L10 register](../hackathon/performer-lifecycle.md) records checks, live acceptance and future contracts; no cloud/schema/flag activation.

ADR-0060 adds `credit_contracts`, `credit_models`, `credit_repository`, `credit_service`, `credit_intent`, `credit_http`:
optional immutable version annotations/self-confirmations and three session-gated `/credits/` actions.
UI `persona-credits.ts`, performer identity/credits, credit editor/fields/evidence picker/state and production history exist.
Migration 0017credits/append-only grants are prepared; `PERSONA_CREDITS_ENABLED=false`. No live schema/activation.
Metadata is workspace-visible; linked evidence stays private. Existing review/passport projections exclude credits.
[O1–O8 register](../hackathon/performer-identity-and-credits.md) retains all future comparison items; offers are not appearances.

ADR-0048 [industry intent](../hackathon/synthetic-performer-industry.md) targets measured retrieval and governed use.
ADRs 0049/0050 add `portrait_search`, `portrait_search_http`, `capture_contracts`, `capture_models`, `capture_storage`, `capture_reads`, `capture_http`, `reference_binding`: exact-file search, encrypted analysis and version references; UI `persona-portrait-search.ts`/`persona-captures.ts`.
ADR-0051 adds `face_contracts`, `face_providers`, `face_google`, `face_crop`, `face_models`,
`face_repository`, `face_storage`, `face_processing`, `face_service`, `face_http`, `face_benchmark`,
`face_benchmark_runner`: explicit selection, provisional quality, encrypted dual vectors/candidate Google adapters; UI `persona-faces.ts`, inspection/preview/state.
ADR-0058 adds `benchmark_report`, `benchmark_corpus`: offline typed reports/fingerprints,
explicit byte preflight, per-case denominators/latency/unknown cost. UI `persona-benchmark.ts`,
`benchmark-report.tsx`/`use-benchmark-report.ts` inspects local untrusted reports in Settings → Recognition evidence.
No HTTP action, storage or policy activation; actual corpus/provider acceptance remains pending.
ADR-0052 adds `face_vectors`, `similarity_contracts`, `similarity_policy`, `similarity_cache`,
`similarity_query`, `similarity_repository`, `similarity_ranking`, `similarity_service`, `similarity_http`:
private calibrated cosine, persona grouping, encrypted expiring queries; UI `persona-similarity.ts`/contracts and controls/results.
ADR-0053 adds `investigation_contracts`, `investigation_provider`, `investigation_models`,
`investigation_storage`, `investigation_repository`, `investigation_evidence`, `investigation_service`,
`investigation_google`, `investigation_http`, `investigation_review_contracts`, `investigation_review_models`,
`investigation_reviews`, `investigation_review_http`: fresh grounded findings/encrypted history and saved review requests; UI `persona-investigations.ts`/contracts/history.
ADR-0054 adds `production_contracts`, `production_evidence`, `passport_contracts`, `passport_signing`,
`passport_google`, `passport_repository`, `passport_service`, `passport_http`: exact-version scope,
asset discovery and injected private Ed25519/KMS export/verification; optional production stores SQL NULL, bounded review telemetry uses `persona_investigation_review`; UI `persona-production.ts`, `persona-passports.ts`/contracts and saved actions.
ADR-0055 adds `google_access`, `google_keys`, `runtime_contracts`, `runtime_bootstrap`, `runtime_http`,
`task_google`, `task_identity`, `job_contracts`, `job_models`, `job_policy`, `job_repository`,
`job_runtime`, `job_service`, `job_worker`, `job_http`: opt-in workload/KMS/Google assembly,
immutable jobs and OIDC delivery, bounded reconciliation, atomic completion and CAS recovery; corrected SQL CASE parsing and retained IDs/sequence across rollback expiration.
UI `persona-runtime.ts`/`persona-job-contracts.ts`, runtime-readiness, durable-face-jobs, job-state/create/history/controls exposes all human capabilities.
S2–S7 migrations 0011–0015 and confined grants are prepared only; inline persistent processing is disabled in assembled Google runtime.
Default Google activation/signing/trust remain unavailable; corpus/calibration, SQL/Linux/scanner/Redis/IAM/Google/key and rendered acceptance pending. [S7 evidence](../hackathon/google-runtime-slice.md).

Portrait preparation includes `photo_contracts`, `photo_models`, `photo_policy`, `photo_binding`,
`photo_storage`, `photo_intake`, `photo_reads`, `photo_http`, `photo_bootstrap`, `photo_decoder`,
`photo_scanner`, `scanner_probe` (fixed loopback readiness/CLI), `runtime_startup` (non-development photos require fresh bounded probe before ASGI serving; lifespan closes runtime after startup failure/cancellation), `photo_inspector`, `photo_vault`; UI uses `persona-photos.ts`, photo editor/state and `use-saved-portrait`. ADR-0065 [composition inventory](../runbooks/google-container-composition.md): checkpoint 11 log verifies 1263 backend/93.79% and all later phases; current hashes match, pasted numeric exit omitted; ADR-0066 `reference_bootstrap`, `reference_app` and `accord.reference` now prepare independent machine-only assembly without browser/Redis/scanner/signing/investigation; Checkpoint 12 log verifies 1285 backend/93.81% and all later phases, including SQL factory/replay; current hashes match, pasted numeric exit omitted. ADR-0067 [compliance lifecycle](../runbooks/google-compliance-lifecycle.md) prepares confined startup, progress health and cooperative cleanup; Checkpoint 13 log verifies 1318 backend/93.86% and all later phases; confined SQL tests pass, current hashes match, pasted exit omitted. Reference reconcile IAM/credentials, native TERM/rollback, [scanner packaging review](../hackathon/scanner-packaging-review-2026-10-12.md) completed; ADR-0068 `scanner/` adds `processes`, `supervisor`, `app` and required-runtime health/supervision without launch/config/Settings assembly; Checkpoint 14 log verifies 1351 backend/93.94%, Trust, 514 frontend, 31 docs-site, audits and builds; current hashes match, pasted exit omitted. [Candidate/runtime review](../hackathon/scanner-runtime-review-2026-10-12.md) completed; ADR-0069 [managed runtime](../runbooks/google-scanner-managed-runtime.md) adds `policy`, `filesystem`, `launcher`, `runtime` within `scanner/`: real file/config/seed checks, fixed signature/update/load commands, loaded-byte binding and cancellation-owned acquisition. 63 new tests and 150 combined tests pass, mypy 410 sources; checkpoint 15 log verifies 1414 backend/94.10% and all later phases; current hashes match, pasted exit omitted. No native executable/image or fixture data is activated. Proposed ADR-0070 [artifact/release design](../hackathon/scanner-artifact-design-2026-10-12.md) records preferred source-build/ABI route, real immutable CVD inputs and separate required-component/assembly checks; [source preparation](../hackathon/scanner-packaging-inputs-2026-10-12.md) now adds `production` real ASGI factory and build-only `seed_policy` verified-config emitter, plus explicit proposed source inventory. 33 new/183 combined tests pass; mypy 414 sources, checkpoint 16 saved log verifies 1447 backend/94.13% and all later phases; current hashes match, pasted numeric exit omitted. Listener deferred by S104/B104; exact build locks and guardrail integration open. Candidate registry metadata is not artifact acceptance. Image/config/runtime implementation, separate release integration, routing and live proof pending. [Build-input review](../hackathon/scanner-build-input-review-2026-10-12.md) identifies published ClamAV archive/signature hashes and candidate Trixie toolchain; actual verification/complete locks remain open. Approved ADR-0071 prepares explicit container launch without Python guard exceptions. Owner published draft [PR #60](https://github.com/ajalcance/gen6th-accord/pull/60), head `116fa14d9d82a9e12dbae4a268db89086d549a4a`: Linux guard tests fail with E2BIG before oversized-input CLI execution (864 passed, 1 failed, 18 skipped). Short IDs are now prepared in the separate checkout, preserving the full payload/denial checks; published at 36cc85addeb8; exact-head Linux guards pass (865 passed/18 skipped), policy/harness pass; owner applied guardrail-change and fresh CI run 38241515740 passes including meta-guard/ci-complete; owner merged PR #60 as 524dbbb18d9c2065af29ab1c017ce453ae93f9cf; exact main push CI run 38244164224 passes, including 865 guards/18 skipped, policy/harness and ci-complete; application/native acceptance remains pending. Owner authenticated API confirms all 21 alerts (3 critical/7 high/11 medium); [triage](../hackathon/dependabot-owner-triage-2026-10-12.md) reconciles 13 PyJWT CI-lock alerts and eight app-lock alerts. Existing app fixes remain unmerged; Owner approved separate CI-lock repair preparation: Semgrep1.179.0 / PyJWT2.15.0 meet the cooldown; scratch resolver freezes78 other packages and rejects unrelated hashes/markers. Owner resolver path-space failure fixed using relative paths; twelve checkpoint tests/lint/typing pass; October13 owner candidate lock hash verified: only two packages changed, 78 unchanged; tracked dependencies unchanged. New isolated package/scanner checkpoint passes four offline faults and lint/typing; Actual ten PyJWT regressions pass; CLI1.176.0 versus installed1.179.0 blocks scanner acceptance. Separate installed-bin-first checkpoint requires CLI/core1.179.0; bound CLI/core both1.179.0 confirmed. Core labeled-output parser fixed; 15 offline faults pass. Hash-bound resume skips completed versions; Bound scan acceptance confirmed:16/16 rule faults,121 targets/0 findings. Canonical lock regenerated offline with identical80 package/marker/hash blocks. Seven review files prepared; local985 guards/18 skipped, policy and harness commands pass. Owner local branch/commit/declaration checkpoint prepared; no push/PR/CI yet. No Actions triggered. [Integration scope](../hackathon/scanner-release-integration-scope-2026-10-12.md) maps isolated scanner ADR-0021 to application ADR-0072; separate release integration is owner-approved and staged (ADR-0073), with mandatory scanner assembly/signature/layer checks and a read-only destination verifier; genuine producers and new PR/CI remain pending. Owner review/label, exact-head CI and mandatory release wiring remain pending; Dependabot alert identities are owner-verified; remediation remains open. See [October 12 handoff](../hackathon/next-session-2026-10-12.md).
Migration 0010portraits adds encrypted original/thumbnail storage and immutable version binding;
`accord-portrait-runtime-grants.sql` and `accord-portrait-vault-policy.hcl` are owner-only preparation.
Pillow 12.3.0 is installed; synthetic pixels pass; Mac workers deny unavailable memory limits.
Linux, clamd/Vault, schema/grants/live proof remain pending; no original/analysis read route
or deletion/purge exists. Staging expires after 24h; bytes await trusted retention/hold policy.

ADRs 0056/0057 add `evidence_inspector`, `evidence_http`, `asset_contracts`, `asset_models`,
`enrollment_policy`, `asset_service`, `asset_http`, `issuance_models`, `issuance_policy`,
`issuance_repository`, `publication_contracts`, `publication_service`, `publication_history`,
`publication_reads`, `publication_http`: private inspected intake, explicit asset provenance,
committed issuance replay and signed allowlisted publication, history, withdrawal and verification.
Frontend `persona-evidence.ts`, `persona-assets.ts`, `persona-publications.ts`, `passport-qr.ts`
and evidence intake/library, asset enrollment, publication/history/share/public pages expose them.
`frontend/app/p/`, `frontend/app/p/[workspace]/`, `frontend/app/p/[workspace]/[publication]/`
contain the public route. Migration 0016passports and runtime grants are prepared, not executed.
New evidence/public flags remain false; deletion requires an injected retention gate (none by default).
[Source/acceptance record](../hackathon/evidence-assets-public-passport-slices.md) separates tests
from pending real SQL, providers, ingress, QR/browser and independent-review proof.
Current checks: 85 focused backend, 459 frontend, 17 isolated integrations; 10 SQL cases
collected only. Static/build/doc checks pass. Full gate stops at pip-audit; npm audit DNS fails.

## Actual repository layout

```
backend/                    FastAPI backend (Python 3.12)
  accord/
    main.py                 app factory; /health + / (system endpoints)
    config.py               Pydantic settings, fail-closed outside dev
    logger.py               structured JSON logging
    db/                     SQLAlchemy base/models; runtime.py validated proxy/bounded engines; connection.py sessions; migration_job.py operator runner
    api/                    authenticated client-reported telemetry; example endpoint removed
    auth/                   request principal (signed bearer token) → event actor
    cache/                  shared verified TLS/CA Redis factory (fakeredis in tests; live TLS pending)
    telemetry/              event envelope, fail-open emitter, coverage registry
    command/                cold store, audit/detection/control catalogs; compliance_config, compliance_supervisor, compliance_app and accord.compliance prepare bounded progress health and cleanup (ADR-0067; checkpoint 13 phases verified)
    personas/               contracts, models, database_policy, repository, services, transactions, observability, health; session-gated routers
  migrations/               Alembic (async env)
  tests/                    pytest on PostgreSQL 17 (Testcontainers; a database per test) — health, spine, migration fidelity
  tests/postgres/           Dockerfile pinning the test PostgreSQL by digest (read, never built; Dependabot-refreshed)
frontend/                   Next.js app (security headers, error boundaries, bundle budget)
  frontend/app/             App Router routes + layout + error.tsx / global-error.tsx boundaries
  frontend/app/passport/    real record-creation, workspace-console/panel, gallery-display/workspace-layout styles, saved queries; no sample workspace imports
  frontend/lib/             typed API client (retry/error contract)
  frontend/scripts/         check-bundle-size.mjs (client JS budget)
  frontend/tests/           vitest + Testing Library
  frontend/tests/fixtures/  fictional wire examples shared with backend contract tests
  frontend/tests/legacy-passport/ historical scenario modules confined to regression tests, never application imports
trust/                      Go module for the trust services (Trust Signer, Log, Anchor, Verifier arrive in Stage 5)
  trust/internal/digest/    the one canonical content digest: sha256:<64 lowercase hex>
docs-site/                  documentation site (publishes only docs/public/)
  docs-site/lib/docs.ts     the loader: docs/public/ only; refuses symlinks and any slug that is not plain names
  docs-site/tests/          vitest (Node): the public-only rule on the real repo and on a fixture tree
deploy/                     Compose + Caddyfile (Postgres, migrate, Redis, worker); prod pulls cosign-signed images (verify.sh)
  compose.local.yml         local stack: app 18660, PostgreSQL 18662, Redis 18663 on loopback
  Caddyfile.local            local HTTP proxy; production TLS configuration stays separate
  accord-data-inventory.sql owner-only read-only all-schema counts; populated stores require provenance review, no cleanup
scripts/local/              private development runtime and merged-model/port isolation validation
scripts/local_stack.py      owner-run local lifecycle guard; docs on loopback 18661
scripts/codex/              proposed managed Codex policy, hook, offline tests and live probe (ADR-0021; owner installation pending)
scripts/                    check_guard_coverage.py (every guard has a fault test + a surface) · check_unicode_hazards.py · dod-check.py (doc guards) · meta_guard.py · check_pins.py · scorecard_gate.py · prod_readiness.py · standards_check.py · release_preflight.py · release_evidence.py · preflight.py · context.py · pr_declaration.py · risk_context.py · secret_scan.py (canary-proven CI secret scan) · check_agent_local_settings.py (local agent settings may only restrict) · sandbox_probe.py (live sandbox probe from a launched program) · wall_off_siblings.py (owner-run: deny sibling projects to the file tools) · bootstrap-repo.sh
tests/guards/               negative tests proving each guard in scripts/ CAN fail
experience/                 registry.toml — lessons normalized onto the enforcement ladder
docs/                       OVERVIEW / GLOSSARY / ENGINEERING_PROCESS / ARCHITECTURE / PLAN / LESSONS / decisions
docs/standards/             the full rule suite — stable ids, honest enforcement markers
.devcontainer/              sandboxed dev image + default-deny egress firewall
.claude/hooks/              local Claude Code hooks: auto-format · footgun + secret blockers · confine_to_project.py (no change leaves the project) · approved_scope.py (approval per unit of work) · ask_on_install.py (every package install asks)
.claude/approved-scope.json  owner-approved scopes; ships empty, so every core path prompts
.claude/settings.json       the agent policy (ADR-0007, ADR-0019, ADR-0020): permissions, shell sandbox, tool-cache env, GitHub identity, hooks
.claude/settings.local.json  gitignored; may only restrict (make policy checks)
vendor/braces/              immutable approved archive, readable third-party source, patch and maintenance record; frontend/vendor/ and docs-site/vendor/ contain identical build-context archives
.tools/                     gitignored: checksum-verified scanner binaries and the local Python interpreter
```

## What's implemented

- **Real integration preparation (ADR-0040):** `auth/zynth_http.py`, `zynth_tokens.py`,
  `zynth_session.py`, `zynth_bootstrap.py`, `browser_store.py`, `browser_oidc.py`,
  `browser_routes.py` provide bounded RS256/UserInfo verification, confidential PKCE login,
  encrypted Redis sessions, Origin checks and local logout. `principal.py` has no local issuer.
  `personas/identity_models.py`, `identity_policy.py`, `identity_repository.py`, `provision.py`
  establish canonical owner-provisioned bindings; `runtime_role.py` denies privileged runtime roles.
  A scoped security-definer membership read retains row locks without runtime grant mutations.
  `0008_real_record_versions.py` refuses prior populated history; `0009_zynth_identity_bindings.py`
  preserves binding immutability/RLS. `connected-workspace.tsx` validates same-origin sessions
  and supplies existing read/write gateways; `next.config.ts` supports a loopback API proxy.
  Defaults remain disconnected. No owner migration, live login or real record has been performed.
  `deploy/accord-runtime-role.sql` is owner-only setup; the [runbook](../runbooks/zynth-local-integration.md)
  records setup, incomplete gates and remaining creation/upload/AI/signing work.

- **Private quarantine preparation (ADR-0031):** `personas/evidence_contracts.py`,
  `evidence_crypto.py`, `evidence_models.py`, `evidence_policy.py`, `evidence_repository.py`
  and `evidence_service.py` implement bounded intake, AES-GCM with injected wrapping,
  immutable metadata/inspection, expiring encrypted payloads, authorized reads and gated purge.
  Migration `0007_private_evidence.py` is prepared; no owner database was migrated.
  `cryptography==50.0.2` was owner-approved/installed and independently import-verified.
  S8 now wires existing scanner/key adapters and session-gated HTTP/UI intake; live activation,
  trusted retention authority and automatic cleanup remain absent. Clean inspection alone
  is not asset enrollment; S9 adds a separate explicit owner action.
- **Prepared frontend adapters (ADR-0032):** `frontend/lib/persona-contracts.ts`,
  `persona-validation.ts`, `persona-receipts.ts`, `persona-campaign-receipts.ts`,
  `persona-commands.ts`, `persona-gateway.ts`, `persona-mutation.ts` validate wire shapes and
  preserve retry intent/conflict state. Default transport rejects; the default console is empty (ADR-0039).
  `api-client.ts` now respects caller cancellation. Shared fictional wire tests are not HTTP E2E.
  Read additions (ADR-0033): `personas/gallery.py`, `evidence_status.py` and frontend
  `persona-read-contracts.ts`, `persona-pages.ts`, `persona-evidence-receipts.ts`, `persona-reads.ts`.
  They add bounded current-head listing and private metadata/history contracts; SQL proof
  is recorded in the [read-side review](../hackathon/h2-read-side-review.md).
  ADR-0074 adds the advisory reviewer brief: `personas/assistant_contracts.py` (bounded plain-text
  contracts and the fixed notice), `assistant_google.py` (text-only Vertex Gemini adapter and
  fail-closed `build_provider`) and `assistant_http.py` (one session-gated read-class route with a
  per-actor limiter). It reuses `persona.version_read`, stores nothing and is off unless
  `PERSONA_ASSISTANT_ENABLED` is true. Frontend: `lib/persona-assistant.ts` and
  `app/passport/record-brief.tsx`, shown on a saved version and sent only on click.
  ADR-0034 adds `personas/session_boundary.py` and `read_http.py`: injected verifier and
  session-gated gallery/version query router. `persona-read-transport.ts`, `persona-query.ts`
  and `app/passport/saved-source.tsx`, `use-persona-query.ts`, `saved-gallery.tsx`,
  `saved-record.tsx`, `saved-records.css` prepare a separate unavailable-by-default saved view.
  ADR-0035 adds `governance-workspace.tsx`, `governance-versions.tsx`, `governance-reviews.tsx`,
  `governance-campaign.tsx`, `governance-evidence.tsx`, `governance-audit.tsx`, `governance-common.tsx`,
  `governance-recovery.tsx`, `governance-recovery-state.ts`, `governance-save-preview.ts`,
  `governance-fixtures.ts`, `governance-preview-transport.ts` and `governance.css`. Separate local
  examples use actual parsers/controllers; drafts stay intact. No real writes, uploads or HTTP.
  ADR-0036 adds `personas/governance_contracts.py`, `version_history.py`, `governance_index.py`
  and `governance_http.py`: bounded discovery and eight session-gated governance POST queries.
  `persona-governance-pages.ts`, `persona-governance-reads.ts`, `persona-prepared-read-transport.ts`
  and `saved-governance*.tsx` bind authorized saved history/status to selected versions, with
  context/permission cleanup. Test-only ASGI bridging proves serialization/client/UI; owner SQL/local-gate proof passes, revision-bound CI remains separate.
  ADR-0037 adds `personas/write_http.py`: four verifier-gated real record write operations
  reusing existing services/actions. `persona-prepared-write-transport.ts` and `prepared-write-*`,
  `prepared-version-*`, `prepared-review-write.tsx`, `prepared-campaign-*` prepare structured
  actions, explicit confirmation and cancellation/conflict/retry recovery. Studio memory retains
  authored drafts/failed intents across navigation/access loss, not fetched records or receipts;
  new session contexts cannot expose them. Default source/writes stay unavailable. Catalogue
  references are injected/version-bound and reauthorized by the service, not private uploads.

- **H2 transactional record persistence, owner-reported PostgreSQL validation:** `personas/contracts.py`
  rejects client attribution/approval; `models.py` defines membership, head, versions and replay
  receipts. `repository.py` checks membership/ownership and locks rows; `service.py` commits
  head/version/server-event/receipt together. `transactions.py` rolls back failed work before
  storing bounded denials/conflicts. `database_policy.py` protects metadata-created test
  schemas; migration `0003_persona_persistence.py` freezes tenant RLS and immutable triggers.
  Owner reports migration through 0009identity and real save/sign-in; routes still deny absent configuration.
  HMAC authentication is removed; Zynth verification is implemented but disabled. Existing local admin
  credentials do not prove RLS application isolation. Future runtime grants must not bypass it.
  Saves, reads, denials, conflicts and workspace observations have complete action registration.
  Direct cold-store writes avoid Redis loss; sealing is asynchronous. Expiry retains unsealed
  auditable server events. Direct events do not yet reach live detection.
  Retention uses a delete/count CTE so concurrent writes do not distort deletion counts;
  receipt reads refresh cold-store/audit references instead of trusting the ORM cache.
  `observability.py` returns scoped receipt references and event/audit-entry presence;
  it records the read and makes no chain verification claim. Redis outage no longer blocks
  sealing already durable records; transaction advisory locking serializes audit sealers.
  `health.py` authorizes a workspace backlog observation and records counts without content.
  Migration 0003 adds a tenant/category/source/time index for this scoped query.
  Sixty-three non-database contract, migration, reference, worker and coverage tests pass.
  Rejection-record failure logs only a bounded request UUID; worker errors omit raw exception
  details. These signals do not imply a durable rejection record when PostgreSQL is unavailable.
  Historical Docker denial, owner 92-test run, early gate/bootstrap and clean Semgrep proof are
  retained in [H2 readiness](../hackathon/h2-core-readiness.md). October 3 owner proof supersedes
  that source; no guard/policy was changed. Seeded migration negatives remain included (ADR-0024).

- **Internal review persistence (2026-10-02):** `personas/workflow_contracts.py` separates
  bounded review intents from trusted internal human fixture context; `review_models.py`
  stores immutable decisions/retry receipts, with `review_policy.py` test-schema protection.
  `workflow_repository.py` shares scoped role/head queries; `workflow_events.py` emits
  minimal server observations. `reviews.py` implements role/self-review checks, version
  freshness, compare-and-swap decision ordering, retries and bounded history pagination.
  Migration 0004 freezes the review table, forced RLS and immutable trigger independently.
  No review route or verified-human adapter exists. Thirty-two targeted non-database checks
  pass; 22 new PostgreSQL behavior/migration cases are collected, not executed in the agent sandbox.

- **Matching experiment preparation (2026-10-02):** the controlled protocol is in
  `docs/hackathon/matching-benchmark-plan.md`; S3/S4 now prepare matching source, while live
  model calls/evaluation remain pending. H1 palette variants count as one source family.

- **Internal campaign persistence (2026-10-02):** `personas/campaign_contracts.py` defines
  bounded fixture scope, receipt, history and status schemas; `campaign_models.py` stores
  version-bound assets, immutable offers, exact version/asset bindings and decision ordinals.
  `campaign_policy.py` installs test-schema RLS/triggers; migration 0005 freezes equivalent
  DDL and composite foreign keys. `campaign_repository.py` scopes storage reads;
  `campaigns.py` records owner offers; `campaign_decisions.py` records named-recipient
  acceptance/change requests and creator revocation. `campaign_status.py` recomputes current
  campaign eligibility from version/review/roles/time; `campaign_history.py` provides private
  bounded cursor history. Edits, replacement reviews, withdrawal, revocation and expiry
  block use without rewriting historical records. Later slices add campaign HTTP/UI.
  S8/S9 now prepare the private inspected intake and explicit asset enrollment pipeline.
  `workflow_evidence_contracts.py`, `workflow_evidence_repository.py` and `workflow_evidence.py`
  inspect matching review/offer/decision events or retained audit references. Source, actor,
  action, tenant, time, request and resource mismatches fail closed; observation is recorded.
  An audit entry being present does not establish chain integrity or a platform signature.
  Owner-run SQL coverage includes 45 campaign, 21 combined migration and six evidence cases.
  Current non-database selection passes 156 tests; lint/types and source-size review pass.
  Owner workflow execution stopped at 48 passes on a test using two different expiry instants.
  Both offers now share one scope. Corrected owner run: 279 passed in 48.86s with matching
  before/after source fingerprints, independently confirmed here; see the workflow review record.
  At that checkpoint `make check` passed 776 guards (18 skipped), policy, harness and backend static checks,
  then stopped at pip-audit bootstrap. Semgrep scanned 36 explicit source targets with nine
  applicable rules and zero findings. No dependency, guard or policy was changed.

- **Durable detection (ADR-0027, migration 0006):** `command/detection.py` evaluates server
  persona events in batches of 100. `command/detection_models.py` registers
  `detection_receipts`: event/workspace, time, catalogue digest, retention flag and findings.
  Atomic receipts enable restart/retry; a shared lock serializes evaluation/retention.
  Counts are tenant-scoped; client events cannot contribute. Late events do not rewrite
  old receipts. `personas/detection_health.py` records authorized backlog reads.
  No route, notification or enforcement. Receipts use the internal command-table boundary,
  without RLS or tamper-evidence. Owner validation passed 301 tests in 50.58s with matching
  before/after source fingerprints, independently confirmed here; see detection review.
  `command/detection_events.py` emits atomic workspace batch observations with count/digest;
  the new action has detection, audit and compliance decisions and cannot recurse.
  Expanded target: 301 collected tests (147 non-database, 154 PostgreSQL); 164 selected
  non-database tests including spine coverage pass. Semgrep: 38 targets, nine rules, zero
  findings; targeted command/test secret scans pass. October 3 owner local gate now passes.

- **Dependency remediation verified locally (2026-10-01):** frontend and docs-site
  manifests, locks and installed copies agree on Next/eslint-config-next 16.3.8 and
  Vitest/@vitest/mocker 4.1.11. The owner used scoped npm 11.16.0 under `.cache/npm-resolver`
  after bundled npm 10.9.8 crashed. The submitted output reached app startup after the
  full gate in the supplied fail-fast sequence. CI review and merge remain pending.

- **Local-first delivery tooling (ADR-0022):** owner commands initialize private local
  credentials, validate resolved Compose isolation and port availability, build/start/stop
  the current services, report status and probe app/health. Public docs run separately.
  Fault tests enforce service parity with the production definitions. `make check` now
  includes Go trust. Owner evidence confirms successful migrations, service readiness,
  app/health HTTP probes and docs startup. Live listener inventory confirms all four ports
  bound only to 127.0.0.1. Manual product journeys remain unverified.

- **Codex companion policy source:** `scripts/codex/` is versioned with guard tests. The
  Mac-wide requirements and hook are not active until owner installation and a passing
  live probe (ADR-0021). The managed default is sealed; the owner selects this project's
  profile in Codex after installation. Claude files remain. The copyable parameters
  for other projects are documented in `docs/runbooks/codex-sandbox-template.md`;
  no other project profile is active yet.
- **Backend skeleton:** FastAPI app factory, fail-closed config, JSON logging, `/health` + `/`.
- **Database layer:** SQLAlchemy 2.0 declarative base + async engine/session (`db/`); Alembic ready.
- **Gates:** ruff / black / mypy --strict / bandit / pip-audit / pytest, pre-commit (gitleaks on
  the staged change at commit time, private-key detection, shellcheck; every hook pinned to a
  commit SHA), actionlint and zizmor (strictest `auditor` persona) on the workflows, hadolint
  (failure threshold `info`) on the Dockerfiles, Semgrep dangerous-ops (blocking) and community
  rules (blocking on new findings since the base commit, SARIF kept as an artifact), with an
  explicit `.semgrepignore` so tests and guards are scanned, and the doc-consistency guards. The
  `ci-complete` aggregator counts the gates it checked and refuses an empty set. The scanners
  themselves come from a hash-locked `requirements-ci.txt` (generated from `requirements-ci.in`),
  installed with `--require-hashes` behind a tampered-lock canary. The quarterly CI-integrity checklist
  is `docs/runbooks/ci-integrity-checklist.md`.
- **Drift tests** (`tests/guards/`) fail when any of these happen:
  - Python differs between CI, the backend image and the devcontainer;
  - Node differs between CI, the frontend image and `.nvmrc`;
  - the commit-time gitleaks version differs from CI's;
  - a pre-commit hook is pinned to anything but a commit;
  - Dependabot coverage is missing or stale against the tracked manifests;
  - the docs path filter misses what the docs site publishes.
- **Secret scan in CI** (`scripts/secret_scan.py`, `make secret-scan`, CI `hygiene` job): gitleaks
  over the COMMITS in the PR or push range, pinned by version and SHA-256. Every run first plants
  fresh canary tokens in every tracked directory and refuses to report clean unless all are found.
  Empty or unresolvable ranges are refused. Inline allow comments and `.gitleaksignore` are
  disabled. The pre-commit gitleaks hook is skipped in CI because it scans staged files, and a CI
  checkout has none (ADR-0018).
- **Guard fault tests** (`tests/guards/`): negative tests proving every guard can still fail, so a
  guard that silently stops working becomes a test failure rather than a green tick. Run by
  `make check` and the CI `static` job.
- **Migration fidelity** (`backend/tests/test_migrations.py`): the backend suite creates tables
  from the models, but production only ever runs `alembic upgrade head` — so the suite applies
  the real migrations to an empty database, proves every revision reverses and re-applies, and
  fails if the migrated schema differs from the models, column types included. A model change
  without a migration is caught at PR time instead of at deploy time.
- **Tests on PostgreSQL** (`backend/tests/postgres_server.py`, ADR-0016, TA-015):
  - one throwaway PostgreSQL 17 per test session, from the image pinned by digest in
    `backend/tests/postgres/Dockerfile`, or `ACCORD_TEST_DATABASE_URL` where Docker is unreachable;
  - a fresh database per test, cloned from a schema template;
  - no silent skip: the suite fails if it cannot reach PostgreSQL, and fails if it runs on any
    other major version;
  - Testcontainers' Ryuk reaper is off, so no privileged image is pulled by a movable tag.
- **Experience-to-control loop** (`experience/`): recurring lessons normalized onto a five-rung
  ladder (reference → context → checklist → guard → production blocker). `make risk-context`
  matches the current diff to the entries that apply; CI **fails** if an entry claims `guard`
  enforcement without naming a mechanism that exists. See ADR-0008.
- **Release evidence chain:** `make release-preflight TAG=vX.Y.Z` is fail-closed — an open
  `release-blocker` issue, an open production blocker, a dirty or unmerged tree, a re-pointed tag,
  missing release notes, or a commit whose own CI run on the default branch is missing or not
  green all stop a release, and a check that *cannot run* fails rather than
  passing. On a `v*` tag the release workflow builds each image **once**, signs it,
  generates an SBOM, and publishes a signed `release-evidence.json` naming every image by digest;
  promotion is a separate manual step with a typed confirmation that verifies the evidence and
  retags the same digests, and is asserted to contain no build step. See ADR-0010.
- **Standards suite** (`docs/standards/`): every engineering rule stated once with a stable id
  (`BE`/`API`/`FE`/`TA`/`SEC`/`OBS`/`REL`) and a marker saying how it is *actually* enforced.
  `scripts/standards_check.py` fails CI if a rule claims a `[CI]` gate that does not exist, or if
  a document cites a rule id the suite does not define. See ADR-0009.
- **Memory governance:** `make context` derives a session snapshot from the repository (prints,
  never persists a second copy of the truth); every PR carries a **Memory impact** declaration that
  `scripts/pr_declaration.py` checks against the diff in both directions; `dod-check` additionally
  enforces ADR numbering/indexing and newest-first `LESSONS.md` ordering.
- **Docs site publishes only `docs/public/`** (`docs-site/lib/docs.ts`), enforced in CI by
  `docs-site/tests/` through `make docs-site` and the CI `docs` job:
  - on the repository: at least one document is published, every published document resolves
    inside `docs/public/`, every Markdown file there is published, and none of the rest of `docs/`
    is, directly or through a `..` slug;
  - on a fixture tree: a symlinked file or directory, a `..` or path slug, an in-tree alias and a
    missing `docs/public/` each publish nothing, while the real files still publish.
- **Frontend chassis:** baseline security headers (CSP, COOP, CORP, HSTS, Permissions-Policy) in
  `next.config.ts`; route + root error boundaries for fault isolation; a typed API client that
  retries only idempotent methods; and a client bundle-size budget enforced in CI.

- **Agent boundary:** existing authority, project confinement, owner-only policy and historical
  probes remain documented in [agent boundary state](agent-boundary-state.md); ADRs 0019/0020 govern.

- **Compliance/observability spine:** fail-open telemetry (`telemetry/`) → Redis stream → cold
  store (`command/` `events`) → hash-chained tamper-evident `audit_log`, plus detection-rule and
  compliance-control catalogs. **Four CI coverage-guards** enforce that every emitted action is
  registered for emit + detection + audit + compliance. Auth session observations and operator membership provisioning are registered;
  the example endpoint is removed; the worker (`command/worker.py`) ingests + seals.
  Client-reported events (`POST /api/v1/client-events`) are authenticated, server-attributed,
  allowlisted, rate-capped and stamped `source=client` — they are queryable data but can never
  enter the audit chain or the compliance map (ADR-0012).
  A signed bearer token (`auth/`) resolves the request **principal**, recorded as the event actor
  (anonymous → `system`; a forged token is rejected 401).
## Historical planning

Earlier scenario planning and the baseline ADR map are retained in
[historical prototype state](historical-prototype-state.md). Current source preparation does not
establish runtime acceptance; the release and live evidence gates remain open.
