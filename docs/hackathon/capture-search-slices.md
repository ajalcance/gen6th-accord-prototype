# Synthetic-performer capture and search — implementation slices

Owner authorized slicing and implementation on October 5, 2026, including frontend exposure
of every new backend capability. Implements [ADR-0048](../decisions/0048-synthetic-performer-identity-and-search.md)
and the [Google capture/search architecture](google-capture-search-architecture.md).
The [industry objective](synthetic-performer-industry.md) remains persistent synthetic-performer
identity, trustworthy reference enrollment, measured facial search and production-use evidence.

## Delivery order and frontend coverage

Each slice includes its backend contracts, privacy boundaries, frontend states, negative tests,
documentation and source-bound acceptance. Background operations surface status and recovery
in the studio; they do not expose internal worker credentials or operator controls.

| Slice | Backend delivery | Frontend delivery | Exit evidence | Current status |
|---|---|---|---|---|
| S1 — exact-file search | Transient bounded image query, server-verified SHA-256, enrolled portrait history, studio isolation, audited observation | Records → Search by portrait; manual query, exact-file evidence, empty/error/retry/cancel/clear states, freshly authorized version inspection | Contract/HTTP/UI tests; PostgreSQL isolation, grouping and retention tests; real-store acceptance separately | Source implemented; validation below; runtime pending |
| S2 — analysis capture and references | Dedicated metadata-free analysis image, source dimensions/orientation, immutable analysis generation/provenance, explicitly approved multiple references | System Capture/reference manager; thumbnail versus analysis readiness; approve/remove/reorder reference; pending/failed/retry states | Bounded Linux decode, three-part scan, key outage/recovery, tenant/version/reference boundaries | Source prepared; [S2 record](analysis-capture-reference-slice.md); migration/provider/SQL acceptance pending |
| S3 — face selection and measured representation | Detector/quality adapter, explicit multi-face selection, versioned normalized crop, face and whole-image embedding providers; encrypted representations | Face boxes/selection, quality feedback, approved reference set, model/generation and analysis readiness | Permitted synthetic-performer benchmark; held-out family split, regenerated appearances, lookalikes and absent performers | Source prepared; [S3 record](face-representation-slice.md); corpus/model selection and runtime acceptance pending |
| S4 — similarity serving | Authorized exact vector baseline, grouping across references, calibrated ranking/abstention, reauthorization before disclosure; bounded query lifecycle | Image query with face selection, scope selector, candidate comparison, evidence method/quality, no confident match and unavailable states | Recall@1/3/5, strong false matches, latency/cost, isolation, failures and retry/recovery; no invented identity probability | Source prepared; [S4 record](similarity-serving-slice.md); permitted calibration/runtime acceptance pending |
| S5 — grounded investigation | Structured Gemini findings from authorized stored evidence and search receipts; supplied appearance evidence; exact-version human review | Analysis & review: compare appearances, evidence/gaps, grounded findings, request independent review and inspect history | Source-bound findings, unsupported-claim refusal, provider failures and human decision boundaries | Source prepared; [S5 record](grounded-investigation-slice.md); saved review requests/existing decisions; SQL/Gemini acceptance pending |
| S6 — production clearance and passport integrity | Performer-versus-role metadata, named production/episode/asset use, consent/claim references, permission status, signed export/verification adapters | Studio production-use form/status/history; passport export and verification with altered-package result | Exact-version clearance, recipient/expiry/revocation, signature verification and tamper rejection | Source prepared; [production/passport evidence](production-passport-slice.md); migration/KMS/SQL/rendered acceptance pending |
| S7 — Google runtime and judged rehearsal | Opt-in Cloud Run/Tasks delivery, durable intent/reconciliation, Google model/KMS assembly, encrypted persistence/observability | Configured capabilities, queued detection/selection, job history/recovery/cancel, existing full journey | Actual bounded Google calls, restart/replay recovery, measured demo and failure/isolation cases | Source prepared; [runtime/rehearsal record](google-runtime-slice.md); actual SQL/cloud/benchmark/rendered acceptance pending |

S7 is an integration lane, not an excuse to defer Google until the end: implement the reviewed
Google adapters while S2–S5 establish their contracts. A hackathon completion requires the actual
Google processing and measured retrieval proof; S1 alone does not satisfy that technical goal.
Cloud resources, installs, costs, database/grant changes, signing and publication retain their
separate owner activation gates. No activation or security-policy change occurs in S1.

Future web/platform discovery, continuous appearance monitoring, voice/video representations
and large public/shared indexes remain after the bounded prototype. S4 initially serves only
the authorized private studio; new shared/discoverable scopes require explicit consent, policy
and isolation tests before the scope selector enables them.

## S1 — reviewable implementation

[ADR-0049](../decisions/0049-exact-portrait-search-foundation.md) records the first evidence path.
One route is added under the existing session-gated persona photo router:

`POST /api/workspaces/{workspace_id}/personas/photos/search`

- Reuse the bounded `PhotoUpload` byte envelope, with no browser actor or scan verdict.
  Validate declared length/base64 and recompute SHA-256 from the transmitted bytes.
- Verify the current human session/workspace and stored membership before consuming the body.
  Readers may search; search grants no enrollment or mutation permission.
- Join workspace-bound portraits → immutable bindings → immutable persona versions. Ignore
  staged/unbound portraits and all other studios. Select the newest **matching** historical
  version per persona, ordered deterministically by persona ID, capped at 20 plus an overflow flag.
  A later changed/removed portrait does not erase prior version evidence.
- This path hashes bytes without decoding or displaying the query. It does not claim a new
  safety inspection, identify a face, compare regenerated images or certify production permission.
  Malformed image bytes cannot match a successfully inspected enrolled original unless identical.
- Store no query image, new portrait, vector, reference, filename or durable query digest.
  The existing portrait SHA-256 remains private metadata, searchable only after studio authorization.
- Commit a server-attributed `persona.workspace_observed` event with operation
  `portrait_exact_search`, method and bounded result count/overflow. Its existing audit, detection
  and compliance decisions apply. Exclude bytes/digest/candidate identifiers from event metadata.
- Return only authorized candidate versions plus query digest/request/workspace/method binding.
  Private no-store error/success contracts sanitize exceptions. A failed schema/provider path is
  unavailable, never an empty catalogue or an unauthorized fallback.
- The same-origin frontend verifies response shape, method, unique ordered candidates, workspace,
  request and digest. Selecting a file does not run the query. Results/file remain in tab memory;
  session changes clear them, cancelled late results are ignored, retry is explicit.
- Candidate inspection freshly reads its exact historical version and verifies the returned
  version ID, then requests the existing authorized thumbnail. Version permission loss clears
  the search candidates. The historical view is read-only.

Implementation: `backend/accord/personas/portrait_search.py`, `portrait_search_http.py`,
existing photo router/telemetry registry; `frontend/lib/persona-portrait-search.ts`,
`frontend/app/passport/portrait-search.tsx`/styles, saved gallery and connected session source.
No dependency, stored schema, database extension or cloud call is added.

## Validation record

Final source checks on October 5:

- 36 backend focused contract/HTTP/intake and unchanged spine coverage tests pass. No SQL
  fixture or live identity/provider is exercised by that focused run.
- 305 frontend unit tests across 32 files pass, including 18 new transport/UI cases. Existing
  15 isolated HTTP-to-UI integration cases pass separately; their sessions/receipts are synthetic.
- Frontend ESLint/Prettier, strict TypeScript/production build and bundle budget pass.
  Client bundle is 166.4 kB gzip against a 250 kB budget. Rendered browser acceptance remains pending.
- Full `make check`: 776 guards pass, 18 skip; policy/harness and backend Ruff/Black/mypy/Bandit
  pass (192 typed source files), then pip-audit stops at its temporary pip-upgrade bootstrap.
  Full backend SQL/coverage and later full-gate stages do not run; no full-green claim.
- `make frontend` passes lint/formatting/TypeScript then stops because npm audit cannot resolve
  `registry.npmjs.org`. Unit/build/bundle checks above were run independently, retaining both audits.
- Doc consistency, local links, file/function caps and whitespace checks pass. No install,
  runtime restart, migration/grant, cloud call, model activation, signing or publication occurs.

Four new PostgreSQL cases cover historical deduplication/unbound exclusion/no query enrollment,
foreign-studio isolation/authorization-before-consumption, bounded overflow across personas and
changed-byte empty results without a performer-identity assertion.
They require the repository's disposable PostgreSQL runner; collection alone is not execution.
Live acceptance also requires the reviewed existing portrait schema/grants and actual enrolled
images. Do not restart the connected backend before those prerequisites are satisfied.
Source remains in the preserved mixed dirty checkout. Commit/PR and source-bound CI, owner SQL
execution, rendered acceptance and runtime activation are remaining review/acceptance work.

## Next concrete work

S2 source is recorded in [analysis capture and references](analysis-capture-reference-slice.md).
S3 source is recorded in [face selection and representations](face-representation-slice.md).
Review migration/grants/providers and retention before activation; supply the permitted corpus,
evaluate Google against a licensed face encoder and select models from held-out measurements.
S4 source prepares compatible similarity serving; S7 owns durable delivery/actual Google acceptance.
S5 source prepares grounded comparison/history and human review; S6 prepares production/passport integrity.
S7 source prepares runtime/durable delivery and UI recovery; actual Google, SQL, measured retrieval and the full rendered production/passport rehearsal remain acceptance gates.

## Remaining MVP modules — source continuation

Owner authorized the recommended order on October 5. S8 private evidence intake, S9 explicit
asset enrollment and S10 persisted issuance/approved public passports now have backend and
frontend source. See [contracts, boundaries and acceptance](evidence-assets-public-passport-slices.md).
Remaining completion is permitted recognition measurement, owner-approved runtime acceptance,
independent reviewer/production rehearsal and the approved submission package.
