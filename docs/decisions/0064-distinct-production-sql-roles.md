# ADR-0064: Distinct production SQL runtime privileges

Date: 2026-10-12
Status: Accepted for owner-approved source preparation; execution/activation pending.

## Context

Cloud SQL proxy IAM does not confer SQL privileges. Existing `accord_runtime` templates are
incremental nonproduction examples, not distinct production workload profiles. The owner approved
the [role preparation unit](../hackathon/sql-role-preparation-proposal-2026-10-12.md).

## Decision

Prepare `accord_api`, `accord_reference` and `accord_compliance` separately from `accord_migrator`.
The two source SQL files require appdb, the migration operator and exactly 0018lifecycle. Role
creation refuses existing names. Grants refuse activated/administrative/inheriting roles,
runtime memberships, ownership and prior ACL dependencies. Only the creating operator's ADMIN
membership in a candidate is permitted, with INHERIT/SET FALSE ([PostgreSQL 17](https://www.postgresql.org/docs/17/role-attributes.html)); it grants no inherited
operator authority to that candidate. Creation leaves every role NOLOGIN and contains
no credential. No default privileges or old template edits.

Revoke PUBLIC CREATE on public and PUBLIC TEMPORARY on appdb: NOINHERIT alone cannot exclude
PUBLIC privileges. This affects every database user; owner review must confirm other tooling does
not depend on them. Keep CONNECT and schema USAGE. Runtime metadata provisioning and DDL deny.

Grant only the [inventoried operations](../runbooks/google-sql-role-preparation.md). API evidence
intake needs metadata, payload and inspection INSERT, correcting the old template's comment gap.
No private-payload DELETE: trusted evidence retention remains unavailable.

Existing SELECT FOR UPDATE requires UPDATE on a column. API/reference get head_revision on
personas; this is real mutable head authority, including in the reference worker. API also gets id
on private evidence/publications for existing locks; their immutable triggers still deny updates.
Do not represent these as lock-only SQL grants. A future narrower lock design needs separate review.

Reference reads encrypted analysis captures and generation receipts, not original portrait/evidence
payloads. Compliance receives only events, audit_log, detection_receipts and audit sequence USAGE.
Its event DELETE authority is table-wide; existing application retention predicates govern use.
Spine tables lack tenant RLS; API spine reads rely on existing scoped application queries. Tenant
RLS on persona records complements application authorization; database scope is not actor identity.

## Validation and consequences

New disposable migrated PostgreSQL tests apply the actual SQL with generated fixture role/database
names. They exercise existing role guards, required writes/locks, denied administrative/metadata/
original access, workspace isolation, API→reference replay and compliance retention journeys.
NOLOGIN tests assume roles from the disposable operator; they do not verify production credentials.
Execution is pending owner/CI; static acceptance alone cannot establish effective SQL permissions.

Existing role guards, frozen revisions, gate/policy/release files remain intact. No production SQL,
login, grant or resource mutation is authorized by source approval. Reviewed CI, signed release,
operator migration stops, credential provisioning and owner Cloud Shell checkpoints remain required.
Tasks remains paused, one production environment, Zynth later.
