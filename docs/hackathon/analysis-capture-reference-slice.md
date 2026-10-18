# S2 — Analysis capture and approved references

Owner authorized the next slice on October 5, 2026. Implements
[ADR-0050](../decisions/0050-analysis-capture-and-reference-approval.md) within the
[seven-slice plan](capture-search-slices.md). Source implementation is prepared; runtime
migration/provider and rendered acceptance remain pending.

## Capture pipeline

1. Resolve the current human session and creator membership before reading upload bytes.
2. Validate the bounded upload envelope and recompute its declared source digest.
3. Scan the original; decode in the existing bounded Linux worker. Retain its resource limits.
4. Apply source EXIF orientation and independently render metadata-free RGBA PNG derivatives:
   at most 320px for display and 1024px for analysis, without upscaling. Bound analysis to 5 MiB.
5. Scan both derivatives. Any rejected/unavailable scan or key provider prevents the write.
6. Encrypt original, thumbnail and analysis independently, then atomically commit capture,
   provenance, upload/inspection events and the existing receipt. Exact upload retries reuse it.

`persona_portrait_captures` stores the encrypted analysis and immutable generation-one
provenance: source dimensions/orientation, oriented analysis dimensions, source/analysis
digests, recipe, Pillow release, scanner receipt and timestamp. Analysis wrapping/context binds
these fields, studio and portrait. Original/thumbnail storage and seven-field upload receipt
remain compatible. Existing portraits without captures remain readable but unprepared.

## Reference approval and serving

`persona_version_references` binds an ordered, unique set of at most eight prepared portraits
to an immutable version. Registration approves the explicitly selected prepared portrait as
the first reference. Later saves inherit the prior set unless `references.action=replace` is
explicit; `upload_ids=[]` clears the new version's set. Display-photo replacement/removal does
not silently change references. The owner may reorder or remove them through a new version.

Approval verifies owner, studio, capture existence and stage expiry. Previously enrolled
portraits in the same persona can be inherited/reapproved after the 24-hour staging interval.
Another persona's expired stage does not gain that exception. Query images never become references.

New private routes under `/api/workspaces/{workspace_id}/personas/photos`:

- `POST /capture/query`: exactly one `upload_id` or `version_id`; owner-only staged lookup or
  member-authorized exact-version profile. Returns provenance and ordered references with
  `recognition=not_processed`, never encrypted material or source/analysis bytes.
- `GET /versions/{version_id}/references/{portrait_id}/thumbnail`: requires current membership
  and the exact reference binding, then verifies/decrypts only the metadata-free thumbnail.
  Responses are private/no-store with nosniff and restrictive image CSP.

Existing `/versions/save` accepts optional ordered reference intent, using the same owner/CAS,
transaction, audit and exact-request replay behavior. Default `keep` preserves legacy hashes.
S1 exact-file search now joins both primary and explicitly approved reference history, scoped
to the current studio and still grouped/bounded by persona. It is not facial similarity.

## Frontend exposure

System Capture and portrait edits show analysis preparation/provenance after successful Scan.
Records → Inspect capture and references shows primary capture, ordered reference thumbnails
and provenance, separate from recognition readiness. The reference editor offers explicit
scan/add, remove, move-earlier and clear controls; confirmed Save reference version preserves
the text/display portrait and creates new immutable history. Pending/failed/cancel/retry states
reuse the existing private read/write machinery. Uncertain saves retry the same ordered intent;
conflicts require reopening the latest record. Session/known permission loss and late results
cannot restore prior fetched images; blob URLs are revoked on close/unmount.

Backend: `capture_contracts`, `capture_models`, `capture_storage`, `capture_reads`, `capture_http`,
`reference_binding`; decoder/intake/photo read/save/policy/search and telemetry integration.
Frontend: `persona-captures.ts`, `capture-status.tsx`, `saved-captures.tsx`,
`reference-editor.tsx`, `reference-photo.tsx` and connected source/contract/photo integration.
Reference editor state, selection and authored local previews are separate small components/hooks;
previews preserve aspect ratio and are released when removed or the editor closes.

## Validation and activation

October 5 source validation:

- 73 focused backend checks pass: real Pillow pixels/orientation/metadata stripping, independent
  derivatives, hostile protocol/scan/key boundaries, AES context integrity, authorization order,
  actual private ASGI routes, exact-search scope, offline upgrade/rollback SQL and spine coverage.
  Scanner/wrapping/identity fixtures are synthetic; these are not real-provider acceptance.
- 332 frontend unit tests across 34 files pass, including 27 new capture/reference transport/UI
  cases. Existing 15 isolated ASGI-to-UI cases pass separately with synthetic sessions/receipts.
- ESLint, Prettier, strict TypeScript/production build and bundle budget pass. The shared client
  bundle is 166.4 kB gzip against 250 kB. New functions/components and files meet the 50/400 caps.
- Full `make check` passes 776 guards (18 skips), policy/harness and backend static/security
  checks, then stops at pip-audit's temporary pip-upgrade bootstrap. Final standalone mypy passes
  202 source files. SQL/coverage and later full-gate stages do not run; no full-green claim.
- `make frontend` passes static stages then npm audit fails resolving `registry.npmjs.org`.
  Final unit/build/budget checks above run separately without suppressing the audits.
- Doc consistency, local links, caps and whitespace pass. Source remains in the preserved mixed
  dirty checkout; commit/PR and matching CI acceptance remain pending.

Six new PostgreSQL cases cover approval/reorder/clear/replay and historical thumbnails, owner/
studio isolation, analysis-key outage atomicity, expired-stage versus enrolled-reference handling,
secondary-reference exact search and no wrapping-material disclosure. Six existing photo-storage
and four S1 SQL cases are collected alongside them (16 total); collection is not execution.
The Docker fixture is refused by the agent sandbox (`Operation not permitted`); no SQL assertions
ran in the attempted broader run. Owner/CI disposable PostgreSQL and rendered acceptance remain.
The ignored `.cache/portrait-search/s2-checkpoint.md` binds this record to final public source.

Migration `0011captures` and `deploy/accord-capture-runtime-grants.sql` are reviewable preparation,
not applied state. The grant script checks exact schema head and the confined runtime role;
it grants SELECT/INSERT on the five portrait tables, with no UPDATE/DELETE/role policy change.
Owner review must cover migrations 0010/0011, grants, Linux decoder, actual scanner/Vault policy,
real capture/reference creation/replay, recovery and separate reviewer browser acceptance.
Do not restart the connected backend before that schema/grant review and execution.

No dependency install, existing-data backfill, cloud/model call, resource deployment, signing
or publication occurs. Expiry remains an attachment condition, not deletion; bytes remain
subject to the separately reviewed retention/hold process. S3 follows with permitted-face
benchmarking, explicit face selection/quality and measured Google/face-encoder representations.
