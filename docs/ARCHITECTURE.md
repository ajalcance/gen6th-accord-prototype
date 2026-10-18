# Gen6th Accord — Architecture (Target Design)

Separate scanner release assembly preparation is [ADR-0073](decisions/0073-scanner-release-assembly-boundaries.md):
mandatory scanner signatures/reports before publication and promotion, actual layer inspection,
and read-only destination digest verification. Genuine native packaging and new PR/CI remain pending.

Current production preparation and separate scanner guardrail PR status are recorded in the
[October 12 handoff](hackathon/next-session-2026-10-12.md); CI failure and native/release prerequisites
remain unresolved. [ADR-0072](decisions/0072-scanner-artifact-verification-entrypoint.md) preserves the
scanner decision's integration number; the [bounded scope](hackathon/scanner-release-integration-scope-2026-10-12.md)
records the prepared portability fix and pending protected release implementation.

The **design intent** — how the system is meant to work. The **as-built** reality lives in
[`architecture/current-state.md`](architecture/current-state.md); where today diverges from this
blueprint, that page records it.

## 1. Overview

Proposed [ADR-0071](decisions/0071-scanner-explicit-container-health-launch.md) places reviewed scanner
launch parameters in explicit container configuration, keeps Python guards and requires separate
command/topology fault checks. [Input review](hackathon/scanner-build-input-review-2026-10-12.md)
identifies published source hashes and candidate toolchain versions; complete locks remain pending.

Proposed [ADR-0070](decisions/0070-scanner-artifact-release-design.md) defines scanner artifact inputs,
fixture-free final layers and separate mandatory signed assembly/component verification. [Source preparation](hackathon/scanner-packaging-inputs-2026-10-12.md) adds a real production factory and verified-seed config emitter; native listener/build locks and separate guardrail integration remain pending.
No executable server command, workflow or deployment; see [review plan](hackathon/scanner-artifact-design-2026-10-12.md).

[ADR-0068](decisions/0068-scanner-health-supervision-adapter.md) implements an independent required-
runtime scanner health/supervision adapter with synthetic lifecycle tests. No automatic runtime,
implicit process launcher or selected image. ADR-0069 [managed runtime](runbooks/google-scanner-managed-runtime.md) now prepares real-file validation and fixed native exec integration with no fixture fallback; actual image/native acceptance remains pending.

[Scanner packaging review](hackathon/scanner-packaging-review-2026-10-12.md) prepares a candidate
private native freshness adapter, validated definition lifecycle and measured storage/resource plan;
[exact candidate/runtime review](hackathon/scanner-runtime-review-2026-10-12.md) records metadata and proposes fixed configuration, seed/load validation and cancellation-safe process acquisition. No deployable artifact is accepted or launched. Signed scanner release integration is a separate
owner-approved guardrail PR; existing source/contract hashes stay unchanged.

[ADR-0067](decisions/0067-compliance-worker-lifecycle.md) adds a health-only worker-pool entry point
around unchanged compliance passes. Monotonic progress, bounded cancellation and Redis cleanup
do not imply full delivery or whole-pass atomicity. Existing guard/retention logic remains;
native health/TERM, private exposure, credentials and measured allocations are separate gates.

[ADR-0066](decisions/0066-reference-only-runtime.md) separates the reference ASGI factory from API
assembly. Existing machine authentication, SQL-role and job protections remain; exact full config
binding preserves replay. Only wrapping/face/Tasks adapters are assembled. Reference reconcile IAM,
private ingress, credentials and live acceptance remain owner checkpoints; no browser/Redis/scanner.

[ADR-0065](decisions/0065-production-startup-composition.md) records actual service/job/continuous
worker composition and bounded non-development scanner startup before ASGI serving. Failed startup
closes the assembled runtime. Reference assembly and compliance health/signal packaging remain
pending; candidate resources are unmeasured, images unset, private routing and release separate.

[ADR-0064](decisions/0064-distinct-production-sql-roles.md) prepares separate API/reference/compliance
SQL profiles, NOLOGIN role creation and exact-head grants. Forced workspace RLS, immutable metadata
and actor checks remain; lock-column grants confer real head authority and compliance DELETE relies
on existing retention predicates. PUBLIC CREATE/TEMP closes explicitly. SQL/credentials/live proof
and reviewed release are separate owner checkpoints; existing role guards remain intact.

[ADR-0063](decisions/0063-private-sql-proxy-transport.md) selects same-instance loopback Cloud SQL
Auth Proxy sidecars with private-IP authenticated remote TLS and workload identities. Runtime
engines share small bounded pools; Alembic preserves separate operator credentials and NullPool.
Transport validation and a non-deployable container contract are prepared. Proxy supply chain,
SQL users/grants, final worker/job/ingress packaging and live acceptance remain separate gates.

[ADR-0062](decisions/0062-accountable-performer-lifecycle.md) adds an immutable performer lifecycle
ledger: owner-declared operator/authority, time-bounded rights and creation provenance; separate
independent operator/rights/content attestations; member concerns and reviewer responses.
New declarations require fresh assessments. Performer-wide suspension remains effective across
versions and paginated history. Current production permission checks dossier binding, operator,
reviewer roles, rights/assessment expiry and suspension; private trials are capped at 30 days.
Evidence hashes record what was supplied while clean originals are available, without extending
retention or reviewer access. Dossier fields stay out of public/portable passport projections;
signature integrity remains separate from permission. Migration 0018/grants are prepared and
`PERSONA_LIFECYCLE_ENABLED=false`. [L1–L10 register](hackathon/performer-lifecycle.md) preserves
future external credentials, interoperability, consent/appeals and actual-use attestations.

[ADR-0061](decisions/0061-production-first-google-bootstrap.md) records the owner's production-first
Google deployment direction with Zynth sign-in and no separate staging. Initial acceptance runs
on that production environment before inviting users; machine services/data stay private and
enabled capabilities retain their acceptance requirements. The
[bootstrap runbook](runbooks/google-production-bootstrap.md) orders setup and evidence. Cloud
manifests, transport/routing/worker implementation and live deployment remain pending.

[ADR-0060](decisions/0060-attributed-performer-identity-and-credits.md) adds persistent identity
presentation and append-only version annotations for aliases/structured credits. Verified named
human accounts confirm only their own role on an exact declaration; replacement requires fresh
confirmation. Annotations are separate from existing reviews and signed exports. Production
history reads bounded authorized offers, not actual participation. Schema/grants are prepared
and credits remain disabled. [O1–O8 development register](hackathon/performer-identity-and-credits.md)
retains public resolvers, authenticated organizations, claim-level review, granular sharing,
production attestations, delegates, import review and correction/dispute cases as future slices.

[ADR-0055](decisions/0055-google-durable-runtime.md) prepares S7 explicit Cloud Run workload
identity, Google/KMS assembly and append-only approved-reference jobs with verified OIDC delivery,
bounded reconciliation, atomic encrypted completion and creator CAS recovery. Frontend exposes
configuration and job controls. Default activation remains disabled; database/IAM/keys, actual
provider calls, measured recognition, restart and rendered judged rehearsal require owner acceptance.

[ADR-0054](decisions/0054-production-passport-integrity.md) prepares S6 named production roles
on existing exact-version permission offers, submitted consent/claim references and private
passport export/verification. Injected Ed25519/Google KMS adapters bind immutable version, asset
and approved-reference evidence; current permission is recomputed separately from integrity.
Signing keys, migration 0014 and actual Google/rendered acceptance remain owner-gated.

[ADR-0074](decisions/0074-advisory-reviewer-brief.md) adds the first live Google AI path: an
optional, per-click, text-only reviewer brief. The server reads one saved version through the
audited loader and asks Gemini on Vertex AI for a plain-text summary, gaps and neutral questions.
Nothing is stored, no rights or review state changes, and it is off unless the owner enables it.

[ADR-0053](decisions/0053-grounded-investigation-history.md) prepares S5 server-refreshed search
evidence, bounded Vertex Gemini observations and encrypted exact-version findings history.
Records exposes retained analysis, evidence/gaps, saved review requests and independent decisions.
Model output cannot grant rights or clearance; migration/grants, real Google and SQL acceptance
remain pending. Supplied source context is attributed, with no web discovery or URL fetching.

[ADR-0052](decisions/0052-private-calibrated-similarity.md) prepares S4 studio-scoped exact
cosine over approved references, persona grouping, calibration/abstention and an encrypted
Redis query lifecycle. Records exposes preparation, confirmed selection/scope, method/results,
fresh candidate comparison and clearing. Default runtime/model calibration remain unavailable;
held-out accuracy, Google/SQL/retention and rendered acceptance are separate gates.

[ADR-0051](decisions/0051-explicit-face-representation.md) prepares exact-version face detection,
explicit stored-face selection, provisional Linux crop/quality and encrypted dual representations.
Studio controls and injected Google candidate adapters exist; permitted held-out evaluation,
model selection, schema/grants/providers and runtime acceptance remain pending.

[ADR-0050](decisions/0050-analysis-capture-and-reference-approval.md) prepares dedicated encrypted
analysis capture/provenance and explicit ordered references bound to new immutable versions.
Capture metadata and reference editing/thumbnail inspection are exposed in the studio;
S3 face and S4 serving source follow; actual Google execution remains an activation/evaluation task.

[ADR-0049](decisions/0049-exact-portrait-search-foundation.md) implements the first
[capture/search slice](hackathon/capture-search-slices.md): transient, studio-authorized
exact-file portrait search and frontend inspection of matching historical versions.
S4 prepares calibrated serving; measured facial accuracy and Google execution remain pending.

[ADR-0048](decisions/0048-synthetic-performer-identity-and-search.md) extends the target toward
infrastructure for the emerging synthetic-performer industry: persistent identity, approved
visual reference profiles, measured face-based candidate search, evidence/rights claims and
production-use clearance. The hackathon demonstrates a bounded working journey. Broader
web discovery, voice/video support and monitoring are future stages; recognition, derived
indexing and expanded studio workflows remain planned; capture source exists with activation pending.
See [approved direction](hackathon/synthetic-performer-industry.md). Present legal acceptance
does not set the product's ambition; assurance claims and applicable obligations stay honest.

[ADR-0047](decisions/0047-required-registration-portrait.md) requires an inspected portrait for
new System Capture registrations in the UI and HTTP boundary. Confirmed image-free historical
versions are incomplete; unavailable photo services do not imply a missing image.

[ADR-0046](decisions/0046-system-capture-terminology.md) names the persona entry workflow
System Capture throughout navigation, actions, guidance and completion. Persona contracts remain.

[ADR-0045](decisions/0045-portrait-focused-creation-layout.md) pairs compact Creation details
with an uncropped portrait preview; narrow workspaces stack the portrait above the fields.
Local preview remains distinct from checked upload and immutable saved attachment.

[ADR-0043](decisions/0043-creation-completion-screen.md) replaces a confirmed creation form
with a focused completion screen and fresh authorized navigation to the saved record.

[ADR-0042](decisions/0042-records-presentation-and-editing.md) places creation beside Records
tools, integrates search, aligns controls and adds compact saved metadata plus direct prefilled
editing. Optional version-bound photos are authorized work with separate inspection, encryption
and retention prerequisites; their absence is not a completed upload capability.

[ADR-0041](decisions/0041-real-creation-and-data-inventory.md) connects real creation to the
existing version API with explicit confirmation and session-bound in-memory retry intent.
Production contains no historical sample workspace imports. An operator-only read-only
inventory checks all application schemas before integration; populated stores require review.

[ADR-0040](decisions/0040-real-records-and-zynth-session-boundary.md) supersedes fixture-only
runtime contracts and the HMAC scaffold: confidential Zynth OIDC, canonical bindings, confined
DB role and same-origin saved reads/writes are implemented locally, disabled until owner
configuration and live validation. Historical preparation below is not activation evidence.

The default Records workspace UI is now defined by [ADR-0039](decisions/0039-workspace-gallery-without-sample-flows.md): empty until a saved-record source is supplied, consolidated controls and no sample workflows. Earlier fixture UI decisions below remain historical/test preparation; no identity or provider activation is implied.

The second-pass console, semantic tokens and explicit fixture operations are proposed in
[ADR-0028](decisions/0028-persona-console-design-system.md). Backend identity integration
and commercial shipment remain separately gated.
The compact third-pass shell, five-column gallery and honest security status are recorded in
[ADR-0029](decisions/0029-compact-persona-console.md).
The fourth-pass task hierarchy, actionable fixture metrics, comparison controls and explicit
decision/export states are recorded in [ADR-0030](decisions/0030-task-focused-persona-console.md).
Internal encrypted quarantine is defined in [ADR-0031](decisions/0031-private-evidence-quarantine.md).
[ADR-0032](decisions/0032-persona-connection-contracts.md) prepares validated transport/recovery;
neither activates persona HTTP, identity, scanner, key provider or cloud services.
[ADR-0033](decisions/0033-bounded-persona-read-contracts.md) extends this with authorized
current-version listing and bounded, validated history/evidence reads.
[ADR-0034](decisions/0034-session-gated-persona-read-surface.md) prepares a trusted-verifier
boundary, unregistered read queries and a separate saved-record UI with an unavailable default.
[ADR-0035](decisions/0035-visible-governance-and-draft-recovery.md) exposes versions, independent
review, campaign decisions, evidence/audit status and draft recovery through separate, labelled
local contract examples. No service/provider activation or server-backed governance UI is implied.
The subsequent [ADR-0036](decisions/0036-record-bound-governance-reads.md) prepares record-bound
saved governance, bounded discovery and isolated ASGI integration tests. Default connection,
trusted identity and all persona routes remain inactive.

[ADR-0037](decisions/0037-session-gated-persona-writes.md) prepares a separate unmounted write
router/transport and structured saved-fixture actions. Server services retain authority;
authored drafts/uncertain intents have a separate in-memory lifetime from fetched records.
Default writes remain unavailable; real identity, credential/security review and activation are gated.

[ADR-0038](decisions/0038-private-braces-depth-backport.md) records the owner-approved private
braces depth backport, exact artifact identity, app-local Docker packaging, normal regression
tests and temporary maintenance duties. Audit and full-gate evidence remain separate requirements.

Internal persona detection delivery is proposed in
[ADR-0027](decisions/0027-durable-persona-detection.md): atomic receipts, tenant windows
and retention interlocks, without notification or enforcement activation.

Accountability infrastructure for work made by people, institutions and AI agents: governed collaboration, structured claims and independently verifiable trust.

**The Accord target design is [`architecture/README.md`](architecture/README.md).** It summarises the approved architecture v1.0 and Addenda 01–03 (ADR-0013 to ADR-0016). This page keeps the template's structure and points there. Where this page and the Accord design differ, the Accord design wins.

## 2. Principles

- **Fail closed** — deny on missing config / ambiguous auth; never degrade to insecure.
- **Secrets never in git** — only `.env.example` placeholders are committed.
- **Thin routers, logic in services** — one router per resource; business logic in `services/`.
- **Type everything; test every behaviour.**

## 3. High-level components

- **Backend** (`backend/accord/`) — FastAPI app: config, logging, routers, services, DB layer.
- **Frontend** (`frontend/`) — Next.js UI.
- **Docs site** (`docs-site/`) — published documentation.
- **Deploy** (`deploy/`) — Docker Compose + Caddy. Production moves to Cloud Run and
  Terraform (`infra/`) in Stage 0 (ADR-0016); local Compose remains the isolated development
  stack with production-style app builds (ADR-0022).
- **Spine** — telemetry → detection → hash-chained audit → compliance coverage-guards. Transport moves to the Pub/Sub outbox in Stage 1.
- **Planned:**
  - Trust services in Go (`trust/`)
  - mobile apps (`mobile/`)
  - shared schemas (`contracts/`)
  - Accord services inside `backend/accord/` (control, core, MCP server, Intelligence)

  See [`architecture/README.md`](architecture/README.md).


## 4. Data model

The internal H2 fixture service proposes transactional persona versions, workspace
membership, replay receipts and cold-store server events in ADR-0024
([decision](decisions/0024-persona-transactional-persistence.md)). No persona routes
are mounted. Audit sealing is asynchronous; reliable detection delivery, private-data
encryption and verified Zynth sessions remain prerequisites for a real journey.
Internal workspace observations expose pending audit counts and receipt references; no
automatic monitoring or public verification is activated by those inspection functions.
Internal fixture reviews now append exact-version decisions with monotonic ordering, stored
reviewer permissions, self-review denial and atomic server events; see proposed
[ADR-0025](decisions/0025-version-bound-human-review.md). Human fixture context is not identity
verification. Historical retries acknowledge receipts; campaign eligibility must recheck
the current version and latest review. No review HTTP route is mounted.
Internal campaigns bind exact review/version, fixture asset fingerprints, recipient and
temporal scope. Creator permission, recipient acceptance/change requests and final revocation
have separate immutable records; see proposed [ADR-0026](decisions/0026-scoped-campaign-permission.md).
Scoped evidence inspection reports matching event/audit-entry presence separately from
current fixture eligibility. It does not verify a signature or the whole audit chain.

The core objects and state machines are in architecture v1.0 Appendix B, extended by Addendum 01 §9 and Addendum 03. The PostgreSQL schemas and their split between the `control` and `cell` databases are in Addendum 01 §9 and Addendum 02 §8.

## 5. Security model

Optional portraits use separate encrypted intake and immutable version bindings
([ADR-0044](decisions/0044-inspected-version-bound-portraits.md)). Current sessions/membership
gate upload and thumbnail reads; originals have no browser route. Pillow, clamd and persistent
Vault Transit are fail-closed providers. Migration/runtime activation remains pending;
staging expiry does not authorize deletion.

See [`SECURITY.md`](SECURITY.md). Summary: fail-closed config, non-root containers, secret
scanning + SAST in CI, dependency auditing. Local agent clients keep separate
owner-managed policies under a shared repository contract (ADR-0021).

## 6. Decisions

Architectural decisions are recorded as ADRs in [`decisions/`](decisions/).

The private paper passport booklet ([ADR-0075](decisions/0075-record-bound-passport-booklet.md))
is a display of existing records. It reuses approved-reference thumbnails, scoped permission,
server package verification and owner-only approved share history. Opening never issues or
approves; the issued seal and QR require both valid private verification and approved sharing.
Unsigned previews remain accessible without an offer or portrait. No backend route, stored shape
or cloud activation is added. 566 frontend tests/types/lint/build pass on Node24; Node22/render/print/live acceptance is open.

## 7. Immediate prototype boundary

[ADR-0023](decisions/0023-ai-persona-passport-prototype.md) selects the AI Persona Passport
as a focused implementation through Collab, Claims and Trust. The
[prototype plan](hackathon/prototype-plan.md) defines the subset and UI direction. It brings
forward a bounded similarity experiment, and demonstrates platform signing without claiming
the full passkey, transparency-log or timestamp assurance of product launch. The full target
architecture remains applicable; these capabilities are not implemented by documenting them.

### Bounded evidence and public passport continuation (ADRs 0056/0057)

The as-built prototype adds owner-only encrypted inspected evidence, explicitly claimed production
assets, persisted issuance and separately signed approved public fields with withdrawal/history.
Public serving stays disabled; signature integrity, fresh scoped use and legal claims are distinct.
See [source/acceptance](hackathon/evidence-assets-public-passport-slices.md) and current-state.

[ADR-0058](decisions/0058-offline-recognition-evidence.md) extends offline matching evaluation
and local frontend report inspection with byte preflight, fingerprints and explicit failure/cost
denominators. Supplied observations cannot become runtime calibration or server audit authority.
Actual permitted corpus/provider execution and independently reviewed acceptance remain required.

[ADR-0059](decisions/0059-performer-workspace-navigation.md) organizes existing capabilities around
selected performers and saved revisions, toolbar image search, progressive capture with an on-demand
helper, scoped evidence selection and separate private/public/verification passport flows. Settings
hosts connection/capability information and local recognition reports. It reuses existing contracts
without adding authority or runtime activation; global queues require future bounded APIs.
The [later layout audit](hackathon/workspace-layout-audit-2026-10-06.md) normalizes shared picker,
feedback, forms and capability surfaces. Saved review-request history lives in Independent review.
