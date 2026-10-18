# S4 — Private calibrated similarity serving

Prepared October 5, 2026, Asia/Manila. Implements the approved S4 source journey;
actual model calibration/runtime acceptance remains pending. [ADR-0052](../decisions/0052-private-calibrated-similarity.md).

## Technology and process

1. Verified human session and current studio membership precede body consumption. Manual
   preparation validates a bounded PNG/JPEG envelope and recomputes its source digest.
2. Reuse S2 inspection: original safety scan, isolated metadata-free RGBA analysis derivative
   (up to 1024px) and display thumbnail, each independently scanned. Discard original bytes.
3. Reuse S3 detector; return bounded boxes tied to analysis dimensions/digest. No face is
   selected automatically. The UI serves the inspected thumbnail, numbers the faces and
   requires the studio to choose and explicitly confirm its intended performer.
4. Apply S3 provisional quality rules before any encoding. Normalize the selected square crop
   and separately encode crop/whole analysis, validating matching model/revision/dimensions
   and finite unit vectors. Store encrypted representations under the original query expiry.
5. Exact cosine scans at most 128 authorized approved reference pairs. Current heads are the
   default; history is explicit. Choose each pair's latest face generation; an incomplete newer
   generation cannot silently fall back to an old representation. Overflow is unavailable.
6. Compare only references compatible with the reviewed policy and source capture. Group by
   persona's highest face cosine; deterministic ties prefer newer versions. Whole-image cosine
   is displayed independently. Top threshold and runner-up margin can abstain. Return up to
   five qualifying candidates, compatible/total reference counts and explicit truncation.
7. Fresh membership and catalogue/head/generation checks precede disclosure. Comparison freshly
   loads the exact version and generation, then its approved reference thumbnail. Neither a
   search result nor a human comparison automatically grants production permission.

## Backend-to-frontend coverage

All routes are under `/api/workspaces/{workspace_id}/personas/photos/similarity`.

| Capability | Endpoint | Records UI |
| --- | --- | --- |
| Runtime/calibration readiness | POST `/readiness` | Manual check; processing unavailable, missing/expired calibration, ready |
| Inspected ephemeral detection | POST `/prepare` | Explicit Prepare; no processing on file choice; exact-intent retry |
| Safe query image | GET `/queries/{query_id}/thumbnail` | Digest-verified private preview with numbered boxes |
| Selected face / scope / calibrated search | POST `/search` | Face radio + confirmation, current/history selector, candidates or quality/empty/incompatible/no confident match |
| Ephemeral clearing | POST `/clear` | Immediate local clearing, acknowledged server clearing or explicit retry/unconfirmed status |
| Method and comparison | Existing version/reference/face reads | Face/image cosine, policy/evidence/model, fresh side-by-side approved reference |

Queries remain in injected encrypted Redis for at most ten minutes, actor/studio bound. Clearing
tombstones the parent and atomically deletes representation children. Expiry/410 clears UI and
requires fresh preparation; cancel/clear ignores late responses, revokes blob URLs and closes
known query IDs. Unmount attempts clearing; expiry bounds retention if transport fails. Browser
cancellation does not promise cancellation of external work. No SQL portrait/reference enrollment,
new migration, new dependency, process-memory fallback or persistent browser image cache exists.

## Google stack connection

Reuse injected `GoogleFaceDetector` (Vision FACE_DETECTION) on safe analysis pixels and
`GoogleImageEncoder` (Vertex multimodal embedding candidate) on normalized crop/whole analysis.
Exact local vector retrieval is the evaluation baseline before a larger Google vector index.
The policy must bind the observed service revision, processing recipes and held-out evidence;
unresolved aliases and changed incompatible generations do not rank. No real policy is shipped,
and this candidate stack has not won a face-identification benchmark. S7 retains owner-configured
service identity, real provider acceptance and durable request/cost reconciliation.

## Validation and pending acceptance

Validation on the prepared source:

- 33 new S4 backend tests pass: exact math/grouping/abstention, compatible sealed generations,
  metadata/input authorization ordering, encrypted Redis replay/expiry/tombstones, isolation,
  quality/no-face selection boundaries, catalogue changes and private ASGI responses.
  The final combined S2/S3/S4/offline-migration/spine lane passes 104 tests. No SQL execution is claimed.
- 370 frontend unit tests pass in 38 files, including 27 S4 checks. Existing isolated ASGI-to-UI tests pass
  15 tests in two files; those remain synthetic transport proof.
- Backend Ruff/Black (250 files), mypy (238 files), Bandit; frontend ESLint, Prettier, strict
  TypeScript and production build pass. Shared client bundle: 166.4 kB gzip / 250 kB budget.
  Changed source/tests satisfy the 400-line file and 50-line function caps.
- `make check` under Node 22 passes preflight, 776 guard tests (18 skipped), policy/harness
  and backend static checks, then stops at pip-audit's temporary pip-upgrade bootstrap failure.
  Full SQL/coverage/Trust/later stages did not run. `make frontend` passes lint/format/types
  then stops at npm audit DNS `ENOTFOUND registry.npmjs.org`; standalone tests/build passed.
  `make dod-check` passes: 54 ADRs and 154 standards. Commit/PR/revision-bound CI remain pending.
- Two new PostgreSQL tests collect for latest-generation exclusion, current/history scope,
  cross-workspace denial and no query enrollment; owner/CI execution is pending. A broader
  spine attempt hit the Docker sandbox boundary in four SQL fixtures; no retry outside it.

Synthetic scanner/detector/vector fixtures exercise serving with real Pillow/AES; they establish
no facial accuracy or production readiness. Existing owner gate evidence applies to earlier
source, not this changed checkout. No gate, policy, dependency pin or migration was weakened.

Pending: permitted performer corpus and held-out calibration; Recall@1/3/5, strong false matches,
latency/cost; actual PostgreSQL/runtime-role isolation; Linux worker and Google/key/scanner/Redis
acceptance; rendered geometry/keyboard/zoom/touch; full dependency audits/CI on the final source.
No credentials, installs, schema/grants, private config, restart, cloud calls/spend, signing,
submission, deployment or publication are activated by this source slice.
