# Lessons

Dated, append-only log. **Add an entry after every meaningful change**
(per [`../CLAUDE.md`](../CLAUDE.md) §2). Newest first; link to ADRs for decisions.

Earlier entries are preserved in [lessons history](lessons-foundation-history.md).

---

## 2026-10-17 — A signed display needs record binding and the correct read permissions

- An inspected portrait is not an approved reference. Use the approved reference list and its
  authorized thumbnail; unavailable reads do not establish absence.
- Publication history is owner-only. An unsigned preview must not query it for a reviewer.
- Keep private and public package parsers distinct. Issue time comes from the private package;
  approval time is not issue time. A share receipt does not prove public availability.
- Retain an explicit export only within the current workspace, session, version and offer.
  Navigation must not export, approve or persist the package in browser storage.
- Manual review and static guards are useful but do not establish TypeScript or rendered proof.

## 2026-10-17 — A model feature should reuse an audited read, not add a new action

- The reviewer brief reads one saved version through the existing loader, so membership,
  workspace binding and the observation event are inherited and the coverage guards stayed green
  with a single registry line. A parallel read path would have needed its own audit decision.
- `from __future__ import annotations` in a router module hides a locally defined dependency from
  FastAPI, which then treats it as a query field and answers 422 on the happy path. Sibling
  routers omit the import for this reason.
- Route objects are not stable across FastAPI versions. Read routes from the OpenAPI schema.
- Model output is untrusted input. Validate it against a schema and plain-text limits, reject
  rather than repair, and keep the advisory notice server-authored.

## 2026-10-12 — Oversized pytest IDs can prevent subprocess execution

2026-10-13: Inspect every lock path and edge before declaring dependency removal: tinypool is absent from both complete populations, not just top-level lookups.514/31 tests pass; retain the existing tested Vite8 tree. Owner metadata142 records/87 packages passes; preserve the saved result instead of resolving or rerunning. Focused preview27/31 tests and lint/types/format/DoD pass; owner fresh installs/full gates pass. Temporary tooling symlinks are untracked files: remove only the exact link, preserve its target and completed gates. Candidate28 hashes/population pass; PR67 mergedf466978; exact-main pushCI38336603073 passes applicable app/static gates. Equivalent patch repair preserves approved archives/source/locks; integrated full local checks pass. Owner API reports zero open Dependabot alerts. [Application integration preparation](hackathon/application-integration-2026-10-13.md) passes preview DoD; policy PR77 mergedb2ddb6c with exact-main CI38341957279 green; application full local gate passes (1447 backend,94.15%;514 frontend;31 docs;987 guards/18 skipped); Trust/DoD pass. Three documentation scan matches are reworded; clean unpublished commit preparation preserves controls/locks and completed code checks. PR78 head d67ecd8 passes Linux backend/frontend/static/hygiene and custom SAST; community SAST flags two legacy HTTPSConnection calls. Candidate replaces them with HTTPS-only transport, explicit certificate/hostname verification, no redirects/proxies, timeout and response bounds;54 auth tests, lint/types/Bandit pass. Owner custom/community scans pass at7c70939; full check found test-double typing errors. Candidate uses real parsed HTTPResponse doubles;54 auth tests and full mypy414 sources pass, preserving TLS/redirect/size assertions. Full repaired-head checks and CI remain required; native deployment pending. PR66/main CI accepted; current28 app alerts are owner evidence, not closures. See [review](hackathon/application-dependency-review-2026-10-13.md) and [preserved history](hackathon/dependency-continuation-history-2026-10-13.md).
PR #60 Linux CI failed with E2BIG before the guard ran: a 262145-character case ID enters the inherited pytest environment. Use short IDs and retain the full input/denial assertions; Mac success is not Linux acceptance. See [handoff](hackathon/next-session-2026-10-12.md).

## 2026-10-12 — Bind raw OCI configuration before checking launch settings

A valid launch JSON can describe the wrong image. Hash the raw manifest against the expected
verified image digest, then the raw config against its descriptor; never reserialize first.
The calling pipeline still verifies signatures and reviewed deployment bytes. See [129-test candidate](hackathon/scanner-launch-guardrail-review-2026-10-12.md).

## 2026-10-12 — Candidate checks are not an active release gate

Keep a guard change in its own PR; a dirty source checkout is not that boundary. An isolated
patch can validate structure, but signed-image input binding, CI wiring and real routing need
separate acceptance. See [86-test candidate evidence](hackathon/scanner-launch-guardrail-review-2026-10-12.md).

## 2026-10-12 — Identify the runtime child explicitly

Owner registry metadata identifies index and Linux/amd64 child; unknown/unknown attestations are not runtime images. Preserve both digests and verify real layers separately. See [candidate record](hackathon/scanner-build-input-review-2026-10-12.md); source hashes unchanged.

## 2026-10-12 — Published hashes and tool versions are candidates, not a build lock

The named release archive differs from generated GitHub source archives. Verify actual bytes and
trusted signature; lock every native/Python/Rust dependency in Linux. Bookworm default Rust is too
old for ClamAV 1.4. Explicit deployment launch needs reviewed topology guards, not Python ignores.
See [input review](hackathon/scanner-build-input-review-2026-10-12.md); source unchanged, no full rerun.

## 2026-10-12 — Accept saved phases without inventing the omitted exit

Checkpoint 16 log verifies 1447 backend/94.13% and later phases; current source/ten input hashes
match. Numeric exit and full bindings were omitted from the paste. Preserve that limit and avoid
rerunning unchanged source; native artifact acceptance remains separate. See [evidence](hackathon/scanner-packaging-inputs-2026-10-12.md).

## 2026-10-12 — Stop at intentional exposure guards; bind emitted policy to actual files

A proposed all-interface scanner listener trips S104/B104. Keep the real factory, defer that
executable command to separate owner review, and never compute a spelling to evade the guard.
Build-only config emission requires pinned real hashes, native signatures and unchanged inputs;
exclusive output denies partial reuse. Test bytes never ship. See [source preparation](hackathon/scanner-packaging-inputs-2026-10-12.md).

## 2026-10-12 — An image signature is not complete release acceptance

The current workflow signs images before SBOM scans; accepted signed release evidence must also
pass. Generic components can include scanner but do not require it. Review real seed/build inputs
and every final layer; test-context exclusions do not remove fixtures inherited from a base.
[Artifact design](hackathon/scanner-artifact-design-2026-10-12.md) proposes separate new gates; no build.

## 2026-10-12 — Verify the full log before accepting a truncated checkpoint

Checkpoint 15 saved log verifies 1414 backend/94.10% and all later phases; source/nine contract
hashes match. The paste omits numeric exit and full binding output: record that limit without
rerunning accepted source tests. Source acceptance still does not certify an image or real scanner.
See [checkpoint evidence](hackathon/scanner-runtime-checkpoint-2026-10-12.md); no live mock data.

## 2026-10-12 — Bind load checks to real bytes and own late process acquisition

Hash actual updated definitions before/after engine load and again before launch. A cancelled
spawn can still return a real child later: retain ownership and reap it. Mock processes and seed
bytes belong only in tests; never package a fake manifest or treat fixtures as native evidence.
[ADR-0069](decisions/0069-scanner-fixed-managed-runtime.md) passes 63 new/150 combined tests;
full checkpoint 15, actual image/parser/load/signals and signed release remain pending.

## 2026-10-12 — Registry identifiers are not image provenance

Record index and platform digests separately. Matching source does not prove the image build;
CVD and incremental CLD have distinct trust paths, and unchanged FreshClam success is not a
full seed load test. Review Python/libc packaging before composing an Alpine runtime.
See [candidate/runtime review](hackathon/scanner-runtime-review-2026-10-12.md); no runtime ran.

## 2026-10-12 — Cancellation must not interrupt failure cleanup

Scanner stop can arrive while a failed runner is already reaping children. Shield that cleanup,
TERM every peer, escalate KILL and deny unreaped work; repeated stop must not cancel it again.
33 synthetic tests plus 40 existing scanner/provider tests pass. Typed preparation callbacks do
not prove real bootstrap/configuration validation: the reviewed image/runtime remains pending.
[ADR-0068](decisions/0068-scanner-health-supervision-adapter.md): checkpoint 14 log verifies 1351
backend/93.94% and all later phases; current hashes match, pasted numeric exit omitted.

## 2026-10-12 — Inspect the image entrypoint before trusting defaults

The reviewed upstream scanner bootstrap disables database load testing and does not establish
child supervision/native freshness health. Filesystem writes also consume Cloud Run memory.
Review exact pinned artifacts and measure definitions/reload/storage before sizing. Scanner signing
is absent from our release workflow; adding it requires a separate approved guardrail PR.
See [packaging review](hackathon/scanner-packaging-review-2026-10-12.md); no image was run.

## 2026-10-12 — Measure worker progress and preserve stage commits

A successful compliance pass is progress evidence, not delivery completeness. Bound startup,
passes and cooperative cleanup; a stale or failed pass must deny health. Cancellation rolls back
only the active transaction: earlier stage commits remain durable. Synthetic tests cover lifecycle;
Checkpoint 13 verifies both confined SQL tests in 1318 backend passes/93.86% and all later phases;
current hashes match, pasted exit omitted. Native TERM/proxy rehearsal remains pending (ADR-0067).

## 2026-10-12 — Keep the full job binding while narrowing runtime providers

Reference can omit browser/Redis/scanner assembly, but its config hash must retain unused fields
to match API-created jobs. Reconcile also needs Tasks authority that execution alone does not need.
Checkpoint 12 verifies the confined SQL factory/reconcile/replay journey within 1285 backend tests;
all later phases pass, current hashes match. Pasted numeric exit was omitted; preserve saved evidence.

## 2026-10-12 — Trace factories before composing separate workloads

Checkpoint 11's saved log verifies 1263 backend tests/93.79% and all later phases; current hashes
match. Preserve the log rather than rerunning solely for a truncated paste. Numeric exit was omitted.

API/reference share a factory requiring browser/inspection configuration; separate SQL grants do
not isolate assembly. Keep the gap visible instead of copying authority. Scanner startup belongs
before ASGI yield, inside cleanup; a healthy proxy proves neither worker progress nor termination.

## 2026-10-12 — Verify test packages with the repository-wide mypy command

New nested conftest files need a package marker, as the existing auth/personas tests use.
The 32 SQL tests passed; mypy . exposed the collision. Add __init__.py, retain settings; 381 files pass.
Owner full-check-10 now passes: 1249 backend/93.58%, later phases/DoD, matching fingerprints.

## 2026-10-12 — Preserve the underlying SQL error in denial assertions

Full diagnostics exposed a missing hardcoded postgres role, not a permission denial (22023).
Use the disposable server's actual operator; retain exact 42501 denial and full exception diagnostics.

## 2026-10-12 — SQL lock permissions are real mutation permissions

SELECT FOR UPDATE needs a column UPDATE grant; immutable triggers preserve evidence/publication
records, but reference head_revision authority is real. NOINHERIT excludes neither PUBLIC rights
nor future role assumption; close PUBLIC CREATE/TEMP and test session identity, not only SET ROLE.
ADR-0064 prepares separate profiles; 32 disposable tests and full-check-10 pass; live grants pending.

## 2026-10-12 — Source verification remains separate from runtime readiness

Scanner full-check-8 phases pass: 1217 backend (93.58%), later phases/DoD; supplied hashes match. The paste omits the numeric exit/pre-run portion. Keep image/startup/live acceptance pending.

## 2026-10-11 — Collection-time clocks can erase a denial fixture

Relative future timestamps generated in pytest parameters age while the full suite runs.
Build timed receipts in the test body and freeze the validator clock for exact boundaries.
The six-minute-future fixture became valid; fix test timing, not the five-minute/48-hour guards.
Corrected scanner selection passes 40 tests; full-check-8 later verifies 1217 backend (93.58%).

## 2026-10-11 — Scanner freshness is not an open-port or clean-file claim

Readiness needs exact PONG and a fresh validated VERSION within one deadline; close sockets
without extending cancellation. Keep per-scan receipt/verdict checks after startup succeeds.
Probe source is not native platform startup wiring or real malware inspection. Review daemon
limit-exceeded behavior, idle updates and reload capacity separately; scanner source phases pass.

## 2026-10-11 — Job shutdown is part of migration failure handling

Always attempt proxy shutdown after configuration, startup or migration failure; retain the
primary phase and report shutdown failure separately. A shutdown HTTP acknowledgment is not
container-exit proof. Keep exact-head grant sequencing separate from upgrade-to-head and review
effective evidence privileges rather than trusting grant comments. Owner runner full gate passes:
1185 backend (93.45%), all later phases/DoD, matching source/contract before/after; live proof pending.

## 2026-10-11 — Share transport bounds across every runtime engine

HTTP and compliance need the same reviewed SQL transport and capacity limits. Proxy IAM is
separate from database login/RLS; keep operator credentials out of runtime engines. A proxy
startup probe proves process readiness, not SQL authorization. Migration sidecars need explicit
shutdown on success/failure. [ADR-0063](decisions/0063-private-sql-proxy-transport.md); owner full
gate passes: 1147 backend (93.40%), matching source/contract before/after; live acceptance pending.

## 2026-10-11 — Diagnose DDL before repairing cascades

A shared trigger-function syntax fault blocked both model schemas and migrations. Parenthesize
CASE inside PL/pgSQL IF conditions; test actual SQL, not only rendered strings. Rollback expires
ORM objects: retain IDs/sequence before fallible work. Optional JSON needs explicit SQL-null binding;
Keep constraints intact. Patched JS pins/owner locks and shared Redis CA wiring pass the full gate: 1122 backend (93.26%). Reject URL overrides; live certificates and SQL transport remain separate acceptance/design review. [Repair](hackathon/backend-test-repair-2026-10-11.md), [CA preparation](hackathon/redis-ca-preparation-2026-10-11.md).

## 2026-10-11 — Record provisioning and failed execution separately

Owner resource/IAM output establishes configuration, not live TLS, roles, keys or deployment.
The later backend run reached SQL tests: 795 passed, 2 failed, 307 errors, 81.25% coverage.
Keep coverage success separate from gate failure; a truncated ProgrammingError summary cannot
identify the underlying SQL fault. Preserve exact test IDs and full-trace follow-up, not the old
pip-audit failure as the current diagnosis. See [inventory](runbooks/google-production-inventory-2026-10-11.md).

## 2026-10-11 — Separate declarations, attestations and current permission

An operator login does not prove authority, a clean attachment does not prove rights, and a signed
passport does not prove current permission. Bind independent assessments to the exact declaration,
capture evidence hashes while originals are available, and keep existing original-retention rules.
Evaluate performer-wide suspension across all cases and versions, not the visible history page.
Record each future adaptation with its own acceptance criteria. See [ADR-0062](decisions/0062-accountable-performer-lifecycle.md).

## 2026-10-11 — Production-first changes the environment, not the evidence

The owner selected production without staging and will create Google resources with guided
checkpoints. Record that choice instead of continuing to prescribe staging. Keep reviewed signed
releases and capability acceptance explicit: no users does not prove SQL isolation, trusted TLS,
scanner freshness or model accuracy. Google bootstrap requires Tasks/KMS even without calibration;
both Redis clients need verified service CA wiring. Source configuration is not resource setup.
See [ADR-0061](decisions/0061-production-first-google-bootstrap.md) and the G0–G8 runbook.

## 2026-10-07 — Inspect the cascade as well as the shared component

The picker reused a visually hidden label whose CSS only covered System Capture, and its search
inherited Records' narrow toolbar width. DOM-only interaction checks missed both visual defects.
Share the accessibility utility globally, explicitly size the picker search in its workspace
context and give each destination a purpose and action. Retain deliberate selection and loaded
version continuity; do not infer activation from entry guidance. This refines ADR-0059.
Owner screenshots remain necessary for rendered width, zoom and narrow-layout acceptance.

## 2026-10-06 — Bind contributor acknowledgment to its declaration

Persistent performer identity differs from account identity, a face representation and a signing
key. Typed credits remain declarations until the named account explicitly confirms them. Keep
annotation receipts outside an already-reviewed version/passport projection; replacement requires
fresh confirmations and optimistic concurrency. A production permission is not evidence of actual
participation. Retain every inspiration-table item with a stable backlog ID and exit criteria,
not only a chat mention. See [ADR-0060](decisions/0060-attributed-performer-identity-and-credits.md)
and [O1–O8 register](hackathon/performer-identity-and-credits.md).

## 2026-10-06 — Audit shared layouts and failure states across destinations

A shared picker inherited label margins that displaced its search action. Selected workflows also
repeated headings, stretched feedback and loaded review requests in the Analysis tab. Audit shared
composition and loading/empty/error states across all destinations, with resource-specific feedback
and cursor-aware pagination. Source/DOM coverage cannot substitute for rendered geometry checks;
record that limit explicitly. Build an isolated source copy while the owner's preview is running.
See [layout audit](hackathon/workspace-layout-audit-2026-10-06.md), ADR-0059.

## 2026-10-06 — Preserve the process override in local restart commands

The owner's working local sign-in used process-only `PERSONA_API_ENABLED=true`, keeping the saved
configuration disabled. Repeating a plain Uvicorn command silently loses that flag: startup succeeds,
but no verifier is built and login returns `Zynth connection is not configured`. Preserve the
override in the [startup instructions](runbooks/zynth-local-integration.md); do not recreate
credentials or change saved configuration for this symptom. Owner restart/sign-in proof is separate.

## 2026-10-06 — Keep capability entry points above results and assistance on demand

Image search belongs beside name search, with explicit method labels and bounded pagination.
Cross-page workflow context must pin the loaded version and clear on session changes; an authored
draft has a different lifetime from fetched evidence. Collapse secondary required fields without
hiding completion state; a compact helper can open and focus the missing input instead of adding
another permanent panel. A disclosure summary can provide the single accessible field label;
short hints belong in placeholders, while approval text and validation remain visible.
Register persona should state first-reference approval explicitly. Source/DOM tests prove these transitions, not rendered layout or live
recognition. See [ADR-0059](decisions/0059-performer-workspace-navigation.md).

## 2026-10-06 — Carry the frontend checkpoint into the handoff (historical checkpoint)

The owner paused new tasks to inspect the frontend. Preserve that decision explicitly in the
[next-chat prompt](hackathon/next-session-2026-10-06.md): read-only warm-up, current dirty-source
fingerprint, listener evidence without freshness claims, then wait for feedback before resuming.

## 2026-10-06 — Failed observations do not prove safe rejection

Report absent-query failures separately from scored false-match denominators; missing cost must
stay unknown. Bind normalized inputs and check actual corpus bytes explicitly, but keep supplied
observations, byte checks, provider execution, permission provenance and runtime authorization
distinct. A perfect calibration impostor needs universal abstention, not a silently deployable
threshold. Local report import cannot certify a benchmark. See [ADR-0058](decisions/0058-offline-recognition-evidence.md).

## 2026-10-05 — Inspection, enrollment and public approval are separate actions

A clean upload establishes bounded inspection, not production rights or publication authority.
Enrollment records the creator's permission basis against exact-version server-digested evidence.
Persist private issuance per acceptance and reuse committed packages before signing again;
precommit provider cost can still repeat. Public disclosure uses a separate signed allowlist,
trusted keys, explicit approval and withdrawal. Downloaded copies cannot be recalled.
Source tests do not establish scanner, SQL/RLS, live keys, rendered QR or infrastructure acceptance.

## 2026-10-05 — Durable delivery is separate from completion and cost

S7 commits intent before task creation and atomically binds encrypted result, success and events.
Task-name tombstones observe dispatch, not completion. Reserve state-ledger space for final work,
retain exact unknown-outcome intent and expose explicit CAS recovery. Precommit crash can repeat
provider cost even when committed replay is idempotent. Use stored human attribution, separately
verified workload identity, fresh access checks and explicit retained keys. Configuration status
cannot certify live IAM, recognition accuracy or a judged rehearsal. Older dated entries moved
unchanged to linked lessons history. See [ADR-0055](decisions/0055-google-durable-runtime.md).

## 2026-10-05 — Integrity must survive withdrawal without restoring permission

S6 signs immutable production evidence and recomputes current permission during verification.
A valid signature can coexist with expiry/revocation; uploaded keys or creator claims cannot
become authority. Preserve absent-production serialization to keep legacy replay fingerprints.
Consent references require exact-version ownership and retained clean evidence, whose seven-day
lifecycle can block a longer campaign. Keep evidence gaps visible and plan durable attestations.
See [ADR-0054](decisions/0054-production-passport-integrity.md) and [S6 evidence](hackathon/production-passport-slice.md).

## 2026-10-05 — Grounding and retained findings have different lifecycles

S5 refreshes search evidence server-side instead of trusting a browser receipt. Exact candidate
generation, membership, calibration, query openness and catalogue binding survive long model/key
work only if rechecked before commit. Allowlisted observations and citations constrain unsupported
claims; they do not prove visual correctness. Explicitly retained digests/boxes/findings outlive
query pixels. Human review, model findings, source statements and production permission stay distinct.
See [ADR-0053](decisions/0053-grounded-investigation-history.md) and [S5 evidence](hackathon/grounded-investigation-slice.md).

## 2026-10-05 — Similarity abstention and ephemeral cleanup need explicit evidence

S4 ranks compatible approved references, groups by persona and rechecks membership/catalogue
after long work. Missing calibration, incompatible vectors and a bounded-pool overflow cannot
become confident results. Query expiry never renews on retry; clear tombstones block late work.
Distinguish local clearing, acknowledged live Redis deletion and external retention/backups.
See [ADR-0052](decisions/0052-private-calibrated-similarity.md) and [S4 evidence](hackathon/similarity-serving-slice.md).

## 2026-10-05 — Representation readiness is not measured recognition

S3 requires explicit selection from stored detection and keeps both vectors encrypted.
Provisional quality and unresolved provider aliases remain visible; benchmark tests exercise
arithmetic, not face accuracy. Hold out entire performer families and retain failed queries in
denominators. Committed replay avoids calls; precommit outages can still repeat provider cost.
See [ADR-0051](decisions/0051-explicit-face-representation.md) and [S3 evidence](hackathon/face-representation-slice.md).

## 2026-10-05 — Analysis preparation and reference approval are separate evidence

- Keep a dedicated analysis derivative, source/recipe provenance and independent safety scan;
  a display thumbnail is not a face-analysis readiness verdict (ADR-0050).
- Approval is explicit and version-bound. Scan alone cannot approve a new reference; replacement
  of the display portrait cannot silently replace the studio's ordered reference set.
- Exercise complete add/cleanup clicks: two draft updates in one batch can overwrite an authored
  selection. Verify exact retry, conflict, blob cleanup and old-version evidence alongside pixels.

## 2026-10-05 — A search slice must reach the studio UI with precise evidence

- S1 joins enrolled immutable history after authorization; hash queries never enroll themselves.
- Distinguish exact-file evidence from facial similarity. Show its method and the matching version,
  then authorize that version afresh; session/known permission loss clears earlier candidates.
- Slice acceptance includes frontend states and tests alongside the backend. Keep SQL, model,
  Google runtime and real-store proof separate from synthetic transport/UI checks (ADR-0049).

## 2026-10-05 — Build the infrastructure for an emerging industry

- Owner clarified AI Persona Passport anticipates synthetic actors' continuing identity and use.
  Present legal acceptance is not a prerequisite for the product experiment (ADR-0048).
- Document approved vision separately from activation. Technology, measured face retrieval and
  meaningful Google integration must prove the hackathon story; an ID/concept is insufficient.
- References, representations, permissions and issued integrity have distinct evidence. Preserve
  the ambition while measuring reliability; never turn a future target into current acceptance.

## 2026-10-05 — A required image needs a server boundary and an honest status

- Initial registration must require an inspected attachment in UI and HTTP; selection is no scan.
- Confirm missing portraits through authorized reads; unavailable providers do not prove absence.
- Preserve legacy history, explicit Scan and exact retries; provider activation is separate proof.

## 2026-10-05 — Make the start of ingestion explicit

- Photo selection only previews; Scan starts upload and safety checks, then Save attaches it.
- Verify no upload before the click; retries preserve intent and unchecked photos block saving.

## 2026-10-05 — A workflow rename must follow every entry point

- System Capture replaces the persona entry label in navigation, Quick Actions, Records,
  guide, forms, completion and accessible names. Align action verbs and legacy fixture copy.
- Preserve stored draft keys and server contracts so a display rename cannot lose authored work.

October 4 entries continue unchanged in [portrait history](lessons-portrait-history.md).
