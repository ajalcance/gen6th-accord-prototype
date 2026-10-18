# S3 — Face selection and representation source

Prepared October 5, 2026. Implements the approved [slice](capture-search-slices.md) and
[ADR-0051](../decisions/0051-explicit-face-representation.md). Source preparation is distinct
from measured model selection and runtime acceptance.

## Creator journey

Records → Inspect capture and references → Inspect face processing. Profile inspection is a
read; it makes no Google call. Run face detection explicitly, choose the numbered performer
face and confirm it, then create face and whole-image representations. Boxes use the private
reference thumbnail and analysis-coordinate proportions. Actual browser geometry remains an
acceptance task. Each result binds the saved version, approved reference and source digest.

No face, provisional quality block, provider unavailable, processing, stop waiting and exact
retry are separate states. Retry reuses the request ID/selection even after close/reopen.
Stored provenance remains readable without a processing provider if its key service is ready.
Representation means encrypted vectors were stored, not that retrieval is calibrated or that
performer identity/rights/production clearance are established.
Metadata commands are bounded to 4KiB/5 seconds after session verification. Processing has a
55-second provider deadline; the studio waits up to 75 seconds under its 90-second proxy.

## Backend and provider surface

Under `/api/workspaces/{workspace_id}/personas/photos`:

- `POST /faces/query`: exact approved-reference profile, latest authorized generation and
  assembly readiness. Membership authorization precedes lookup/decrypt.
- `POST /faces/process`: request ID plus exact version/reference; no selection means detection.
  Selection requires stored generation ID plus face index. Only the version creator may process.
  No browser coordinates, actor, vectors or arbitrary image URI is accepted.

Frozen migration `0012faces` adds `persona_face_generations` with composite approved-reference
FK, forced RLS, immutable trigger and workspace/request uniqueness. Owner-only
`deploy/accord-face-runtime-grants.sql` requires that exact migration and confined runtime role.
Existing S2/portrait grants must precede it. Nothing applies these files automatically.
Downgrade requires an all-tenant role and refuses populated generations.

Detection boxes, selection/quality/model metadata and both L2-normalized vectors are sealed
together with AES-GCM and the configured wrapper. Analysis unsealing retains S2's exact AAD.
Crop bytes are transient. No raw-vector/image read endpoint or purge implementation is added.
Tracked existing `persona.portrait_inspected` events carry bounded operation/state only;
profile reads use `persona.portrait_read`. Their existing spine decisions apply.

Google adapters use existing HTTP dependencies and injected authorization; the app factory
leaves `FaceProviders` unset. Enabling photo upload does not enable face processing. A reviewed
runtime assembly must inject detector, encoder and Linux cropper explicitly. No SDK, weights,
personal credentials, model calls, cloud resources or automatic region fallback are introduced.
The image encoder baseline uses the selected region/model/dimensions in provenance; model
alias/deployment response is not immutable-weight proof. Face-specific encoder selection awaits
licensing and benchmark comparison. Cloud Vision detection is not individual identification.

## Permitted benchmark runner

`accord.personas.face_benchmark_runner` consumes two explicit bounded JSON files offline.
Manifest `assets` require ID, performer family, development/calibration/test split, reference/
query role, regenerated/lookalike/absent case, SHA-256, permission-record reference and
`synthetic: true`. Those fields are declarations requiring human verification, not machine
proof of permission. Hashes bind observations to reviewed source assets; duplicate images and
family leakage are rejected. Every split requires references and queries; test needs all cases.

Observations provide model, revision, face/whole_image role and exactly one source-bound
observation per manifest asset: asset_id, sha256, vector (null for processing failure), latency_ms
and cost_usd. A trusted image-to-observation run must produce them from the reviewed files;
the evaluator does not independently verify pixels, timing, billing or model provenance.
Test fixtures exercise arithmetic only and contain no performer-image benchmark.

From `backend`, using owner-reviewed repo-relative JSON paths:

```sh
.venv/bin/python -m accord.personas.face_benchmark_runner <manifest.json> <observations.json>
```

The runner validates compatible finite nonzero vectors, groups references by family, fits a
threshold only from calibration impostors, and reports Recall@1/3/5, strong false matches,
absent false-match rate, failed query/reference counts, maximum latency and total recorded cost.
Failures stay in recall denominators. Threshold selection is a baseline requiring independent
human review, sufficient impostors and stratified analysis; it is not production calibration.
Run the same held-out manifest separately for whole-image, Google face-crop and a licensed
face encoder. Select model/quality/crop policy only from measured evidence, with confidence
intervals and distinct pose/style/lighting/group-image strata in the acceptance report.

## Acceptance still required

Permitted synthetic-face corpus/labels/permission review, actual model processing, model and
quality selection, owner migration/grants, PostgreSQL isolation/immutability/replay tests,
Linux worker limits, wrapper/provider outages/recovery, Google workload configuration/region/
cost authorization and rendered frontend acceptance remain pending. S7 adds durable dispatch
and reconciliation; this synchronous source does not prove crash-safe billing deduplication.
S4 similarity serving must reject incompatible provider/model/crop generations and calibrate
ranking/abstention; no new similarity search or identity-probability endpoint exists in S3.

## Source validation

Final source checks on October 5:

- 71 focused backend tests pass: real Pillow crop/AES receipts, synthetic detector/encoder and
  Google MockTransport, service authorization ordering, actual private ASGI/body bounds,
  benchmark arithmetic/provenance, frozen migration SQL and unchanged spine coverage.
  These test pixels are simple fixtures, not a permitted performer corpus or accuracy result.
- All 343 frontend unit tests across 36 files pass, including 11 new face contract/UI tests.
  Existing 15 isolated ASGI-to-UI integration cases pass separately with synthetic sessions.
- Frontend lint/formatting, strict TypeScript/production build and bundle budget pass.
  Shared client bundle is 166.4kB gzip against 250kB; rendered geometry remains pending.
- `make check`: 776 guards pass, 18 skip; policy/harness and backend Ruff/Black/mypy/Bandit
  pass (234 Python files formatted, 222 typed source/test files), then pip-audit fails at its
  temporary pip-upgrade bootstrap. Full SQL/coverage and subsequent gate stages do not run.
- `make frontend` passes lint/formatting/TypeScript, then npm audit fails to resolve
  `registry.npmjs.org`. Tests/build/bundle were run separately; neither audit was bypassed.
- `make dod-check` passes with 53 ADRs/154 standards. File/function caps and whitespace pass.
  Two new PostgreSQL tests collect; they have not executed inside the Docker-restricted sandbox.

No S3 runtime was activated and no live Google request, migration/grant, dependency install,
signing or publication occurred. Source remains in the preserved mixed dirty checkout;
commit/PR/source-bound CI and owner SQL/provider/browser/benchmark acceptance remain pending.
