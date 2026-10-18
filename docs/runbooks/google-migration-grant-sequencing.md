# Google migration and grant sequencing — preparation only

Reviewed source map, 2026-10-11. **Not an execution script or production approval.**
Existing templates were written for a nonproduction `accord_runtime` account; production still
needs reviewed per-runtime login/privilege design. Do not run these scripts blindly on Google SQL.

The runner performs one allowlisted Alembic upgrade and stops its private proxy afterward.
It does not create roles or apply grants. Each later owner checkpoint needs its own reviewed
job image/configuration, target revision, migration record and separately reviewed grants.
Rehearse sequencing and RLS with disposable PostgreSQL before any owner production checkpoint.

| Stop at revision | Existing grant template | Scope / prerequisite |
|---|---|---|
| `0009identity` | `accord-runtime-role.sql` | Nonproduction baseline: creates `accord_runtime`, schema USAGE, membership function EXECUTE, listed spine/persona SELECT and selected writes; no exact-head guard; not a production role template |
| `0010portraits` | `accord-portrait-runtime-grants.sql` | Exact-head guard; SELECT/INSERT portraits, payloads and version portraits |
| `0011captures` | `accord-capture-runtime-grants.sql` | Exact-head guard; adds captures/version references and repeats portrait grants |
| `0012faces` | `accord-face-runtime-grants.sql` | Exact-head guard; SELECT/INSERT face generations |
| `0013investigation` | `accord-investigation-runtime-grants.sql` | Exact-head guard; SELECT/INSERT investigations and review requests |
| `0014production` | No separate grant template | Adds bounded campaign production metadata; preserve existing campaign privilege/RLS review |
| `0015jobs` | `accord-job-runtime-grants.sql` | Exact-head guard; SELECT/INSERT jobs/transitions |
| `0016passports` | `accord-passport-runtime-grants.sql` | Exact-head guard; SELECT/INSERT assets/enrollments/issuances/publications/unpublications |
| `0017credits` | `accord-credit-runtime-grants.sql` | Exact-head guard; SELECT/INSERT credit profiles/confirmations |
| `0018lifecycle` | `accord-lifecycle-runtime-grants.sql` | Exact-head guard; SELECT/INSERT lifecycle records |

Paths above are under `deploy/`. The chain before `0009identity` is linear:
`0001spine → 0002source → 0003personas → 0004reviews → 0005campaigns → 0006detection
→ 0007evidence → 0008realrecords → 0009identity`. Subsequent stops follow the table order.
The runner accepts explicit listed revisions, never mutable `head`, downgrade or arbitrary commands.
Upgrade-to-head followed by all templates fails earlier exact-head checks; do not remove them.

All incremental templates require an existing `accord_runtime` role with no superuser,
BYPASSRLS, CREATEDB or CREATEROLE attributes. They do not establish login secrets, membership,
identity binding, NOINHERIT/NOREPLICATION, effective role inheritance or live workspace isolation.
The baseline creates those latter attributes but is explicitly dedicated-nonproduction source.
Its grants are not automatically appropriate for distinct API/reference/compliance SQL identities.

## Required separate production role review

- Migration workload identity `accord-migration` connects the private proxy; SQL operator
  `accord_migrator` is separate and never used by application engines. This does not prove its
  effective DDL/rollback privileges; Cloud SQL administrative membership is not PostgreSQL
  superuser status. Existing rollback guards remain authoritative.
- API, reference and compliance workload identities need distinct reviewed SQL privilege
  profiles and private credential delivery. Proxy IAM does not grant database permissions.
- Verify effective privileges, forced RLS, workspace predicates and all required capability
  writes on disposable SQL under each intended identity before generating production grants.
  In particular, the passport template's evidence-write comment is not executable proof:
  the baseline grants evidence tables SELECT, not INSERT. Resolve the complete evidence
  privilege contract in the separate role review; do not infer permissions from the comment.
- Define schema/grant failure recovery, backup/restore, populated-table rollback limits,
  job retry/idempotency and image/schema compatibility before owner production execution.
  Jobs do not run automatically; queue remains paused and capability flags remain unchanged.

No existing role/grant/revision file was changed by this matrix. Live schema, role and deployment
acceptance are pending; signed immutable release/import and owner checkpoints still apply.
