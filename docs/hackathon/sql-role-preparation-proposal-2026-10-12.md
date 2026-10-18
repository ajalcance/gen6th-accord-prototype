# Production SQL role preparation — October 12

Status: **Owner-approved source unit implemented and full gate passed: 1249 backend, 93.58%; no production SQL/cloud execution.**
Follows verified SQL/Redis/migration/scanner source phases and the
[grant sequencing matrix](../runbooks/google-migration-grant-sequencing.md).

## Problem and intended result

The cloud inventory records the operator login, but no confined application SQL logins or
production grants. Existing incremental templates name the shared nonproduction `accord_runtime`
role. API, reference and compliance workloads need explicit distinct privilege profiles; proxy
IAM grants do not establish those database permissions. A prototype grant script is insufficient.

Prepare a source-bound permission inventory and candidate production-role contracts for owner
review. Map each runtime's actual queries/writes, tables/functions, tenant context and retention
operations before generating grants. Do not assume the API's privileges fit the workers.

| Runtime | Candidate SQL login | Required review |
|---|---|---|
| API | `accord_api` | Authorized persona reads/writes and required event/audit receipt access; no membership/identity provisioning or schema ownership |
| Reference worker | `accord_reference` | Stored job intent/transition, fresh creator authorization, approved reference/provider completion and server events under the intended workspace scope |
| Compliance worker | `accord_compliance` | Event ingest, audit sealing, durable detection and existing retention work; enumerate exact tables and required rows, not blanket persona privileges |
| Migration operator | Existing `accord_migrator` | Separate schema/grant owner authority, explicit migration stops and rollback limitations; never application credentials |

These are proposed profiles, not verified grants or configured logins. The inventory must resolve
evidence INSERT requirements and effective inherited privileges; comments do not grant access.
Prepared [inventory and acceptance](../runbooks/google-sql-role-preparation.md), ADR-0064, resolve
the source mapping; NOLOGIN roles, column-lock authority and PUBLIC restrictions need owner/CI proof.
Do not introduce superuser/BYPASSRLS/CREATEDB/CREATEROLE/REPLICATION or ownership authority into
runtime profiles. Existing workspace RLS and membership/identity-write prohibitions remain intact.

## Proposed implementation scope

- A cited table/function/operation inventory from current API/reference/compliance code, with
  justified required privileges and explicit denials. Keep private originals out of compliance
  access unless an existing required operation demonstrates otherwise for separate review.
- New non-deployable production-role contracts and separately reviewed SQL grant preparation
  with exact-head preconditions; retain old nonproduction templates and predicates unchanged.
  Source-only role creation preparation contains no passwords, external execution or credentials.
- Disposable PostgreSQL tests using distinct candidate roles: required operations succeed;
  foreign workspace, membership/identity modification, owner/administrative privilege, DDL and
  unintended table access deny. Test actual effective permissions/RLS, not text matching.
- Reconcile the evidence-write gap identified by the matrix against real capability operations.
  Do not resolve a denied operation by widening access without a source-bound justification.
- Update as-built/security/plan/lessons/changelog and document the proposed decision for human
  review. Full owner/CI gate plus DoD and fingerprint evidence after implementation.

Existing runtime-role guards, frozen revisions, agent policy, release workflow and gate files
are outside this unit. If the inventory finds a guard change is needed, stop for its separate
owner-reviewed proposal/PR; do not bundle it into grant preparation.

No production login creation, SQL query/test/grant/migration, password reset, secret update,
service deployment or IAM mutation belongs to this approval. Reviewed CI/signed release and
owner Cloud Shell checkpoints still apply. Tasks stays paused; Zynth remains later.
