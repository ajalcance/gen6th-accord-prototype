# Production SQL role source preparation

October 12, 2026. Owner-approved source unit, ADR-0064. **No SQL/cloud execution or login activation.**
Contract: `deploy/google/sql-roles-contract.json`; scripts: `sql-runtime-roles.sql` followed by
`sql-runtime-grants.sql` in that directory. Old incremental nonproduction templates remain intact.

## Required operation inventory

| Workload / source | Tables / operation | Boundary |
|---|---|---|
| API `repository`, `service`, `workflow_repository` | SELECT membership/identity; SELECT/INSERT personas, versions, receipts, reviews; head_revision UPDATE | Existing verified actor checks and forced workspace RLS; no membership/identity writes |
| API `photo_storage`, capture/reference services, face service | SELECT/INSERT portraits, encrypted originals, version portraits, captures/references and face generations | Authorized private intake/read; immutable receipts; no original deletion |
| API campaign/asset services | SELECT/INSERT assets, offers, campaign assets/decisions, asset enrollments | Exact-version review/recipient checks remain |
| API `evidence_service`, `lifecycle_evidence` | SELECT/INSERT private evidence, private_evidence_payloads, inspections; metadata id UPDATE for lock | Evidence INSERT is required by real intake; immutable trigger rejects mutation; retention deletion excluded |
| API investigation/credit/lifecycle services | SELECT/INSERT investigations/review requests, credit profiles/confirmations, lifecycle records | Scoped append-only statements, no provisioning authority |
| API issuance/publication services and reads | SELECT/INSERT issuances, publications/unpublications; publication id UPDATE for lock | Immutable trigger retains approved projection; public identifier gives no workspace authorization |
| API `job_service` | SELECT/INSERT face jobs/transitions | Stored owner intent, fresh creator checks and immutable transition protocol |
| API product events / audit status reads | SELECT/INSERT events; SELECT audit_log/detection_receipts | Existing application queries scope workspace; these spine tables have no RLS |
| Reference `job_worker`, `job_repository`, `face_service`, `face_storage` | SELECT personas/versions, portraits/captures, version references, jobs/transitions/generations; INSERT transitions/generations/events | Fresh stored creator checks, workspace RLS; encrypted analysis capture needed, original payloads excluded |
| Reference `face_repository` | UPDATE(head_revision) personas for SELECT FOR UPDATE; EXECUTE membership function | Real head-write authority, not lock-only; no owner/workspace column updates |
| Compliance `consumer.consume_once`, `audit.seal_new`, `detection.evaluate_once` | SELECT/INSERT events, audit_log, detection_receipts; audit sequence USAGE | Cross-workspace internal index/sealing; no persona or private-payload access |
| Compliance `consumer.purge_expired` | DELETE events; SELECT audit/detection receipts | Application retains unsealed/unevaluated history; SQL DELETE permits any event row, not only expired rows |

API/reference execute `accord_workspace_membership(uuid, varchar)`, whose existing SECURITY DEFINER
function checks workspace context and locks membership without granting membership UPDATE to callers.
All runtimes get schema USAGE/database CONNECT; no schema CREATE, temporary tables, owner role,
administrative attributes, membership or default table grants. PUBLIC CREATE/TEMP revocations affect
other tooling too and belong to owner review. No claims of actor isolation from RLS alone.

## Prepared SQL and test boundaries

Scripts require an explicitly selected appdb connection as accord_migrator and one exact revision
0018lifecycle. Existing roles fail creation. Grants reject attributes, runtime memberships, ownership
and third-party administration links; only the creating operator's ADMIN membership is permitted.
It must have INHERIT FALSE and SET FALSE, matching [PostgreSQL 17 creator behavior](https://www.postgresql.org/docs/17/role-attributes.html).
and prior role ACL dependencies; failures roll back, not reconcile unknown authority. The profiles
are prepared NOLOGIN, with no passwords. Separate owner-reviewed activation must verify effective
attributes/ACLs again after credential provisioning; this document supplies no activation command.

Tests in `backend/tests/sql_roles/` create a fresh migrated disposable database per test and unique
roles on the existing disposable test server. They use the actual source SQL, replacing only fixed
database/operator/role names with generated fixture names. Roles are assumed by the disposable
operator because NOLOGIN is deliberate. Cleanup drops grants/roles and the database.

Acceptance includes denied DDL, temp/owner assumption, metadata writes, private originals for workers,
immutable metadata changes, missing/foreign workspace reads and foreign inserts; exact-head and
unsafe-role refusal; real API job creation→reference completion/replay and compliance sealing→
detection→retention. Owner disposable acceptance **passes 32 tests in 24.04s**; full gate stopped
at duplicate conftest modules. Added package marker; exact mypy . passes 381 files. Full-check-10
now exits 0: 1249 backend, 93.58%, Trust/frontend/docs-site/builds/audits and DoD pass.
A prepared contract is not live
SQL or credential acceptance. Existing guards, migration revisions and release files are unchanged.

## Remaining owner checkpoints

First run focused disposable tests and the full local gate with ACCORD_TEST_DATABASE_URL unset;
capture complete SQLSTATE/tracebacks on failure. Verify source/SQL/contract hashes before and after.
Then review source in a PR, satisfy sensitive-path labels through the owner, green CI for the eventual
default-branch commit and signed-release evidence. Production schema/role/grant/credential steps
remain separately reviewed owner Cloud Shell checkpoints after migration stops and inventory checks.
No production tests, resource recreation, image/job/service deployment or queue resumption here.
One production environment; minimum workable sizing; Tasks paused; Zynth later.
