# Migration job source-preparation proposal — October 11

Status: **Owner approved source preparation; implemented, full gate passed; no cloud execution.**
Follows the accepted SQL transport in ADR-0063 and its successful full source gate.

## Problem and proposed behavior

The proxy contract contains a migration-job profile, but no runner currently waits for it or
stops it when Alembic finishes. An endless proxy sidecar could keep a Cloud Run job running.
Alembic already uses NullPool, but engine disposal currently occurs only after success.
Existing grant scripts require their own exact migration heads; running all of them after a
single upgrade to head would violate those checks. Preserve those checks.

Prepare a migration runner with a fixed operation and explicit reviewed target revision. It
validates the approved loopback transport before any connection, waits at most 60 seconds for
the fixed loopback proxy startup endpoint, and invokes Alembic through its Python API.
Startup readiness remains distinct from a successful operator SQL login.

Always request shutdown through the fixed loopback proxy admin endpoint in a finally path,
including startup timeout and migration failure. Bound health/shutdown HTTP requests; disable
redirects and environment proxy discovery. Preserve the original failure and report only
sanitized phase/error categories. A failed shutdown must fail the job even if migration succeeded.
The platform job deadline remains a separate final limit; it does not imply transaction rollback
or prove the sidecar stopped. The owner later verifies both container exits.

Keep Alembic NullPool, add a bounded asyncpg connection timeout and dispose its engine in finally.
Do not modify frozen revisions, table/RLS guards or existing exact-head grant predicates.
Do not embed credentials, discover owner configuration or accept arbitrary shell commands.

## Proposed source scope and validation

- New typed runner module and focused tests for startup success/timeout, migration failure,
  shutdown failure, failure precedence, fixed endpoint and secret-safe reporting.
- A narrowly reviewed migration-environment change for connection timeout/disposal only;
  test existing explicit test URL resolution and the disposable migration round trip.
- Extend the non-deployable job contract with runner phases and failure semantics; update
  PLAN/LESSONS/current-state/SECURITY/CHANGELOG after approval; existing ADR-0063 stays intact.
- Prepare a grant sequencing matrix from current scripts and revision dependencies, including
  confined role preconditions and separate runtime identities. The matrix is for review;
  no role creation, SQL grants, credential reset or production execution belongs to this unit.
- Full owner/CI `make check` and DoD against matching fingerprints after implementation.

## Deferred integration and owner checkpoints

Implementation: `accord.db.migration_job`, migration-environment timeout/finally disposal,
failure-path tests and the updated non-deployable proxy contract. The
[grant matrix](../runbooks/google-migration-grant-sequencing.md) records exact stops and unresolved
production role/evidence privilege review. Frozen revisions and grant checks are unchanged.

Local checks: **62 focused tests pass** (runner/environment/wire plus existing SQL transport tests),
full backend Ruff/Black/mypy and targeted Bandit pass; DoD passes (65 ADRs, 154 standards).
Owner `full-check-6` exited **0**: **1185 backend tests passed**, **93.45% coverage**, 158.23 seconds;
this includes disposable PostgreSQL/migration replay. Also passed: 776 guard tests (18 skipped),
Trust, 514 frontend and 31 docs-site tests, both builds/JS audits and DoD (65 ADRs, 154 standards).
Go analysis reports no reachable vulnerabilities, not zero imported/module advisories.
Owner printed matching source/contract fingerprints before and after the successful gate.
Full log SHA-256: `2670f996de9adfacf89f84a05bc96cd1374edbfe21863e7f3d989e53b2c30614`.
No image, proxy process or production database was contacted by these tests.

Fixed HTTP uses bounded standard-library asyncio streams; no dependency was added or installed.
Current source population: **696 files**, same fingerprint population as prior handoff:
`d2bcc4d3a7b9b447b6b1795bbd496bd501329fa66ea603145d99d23f8e9535ca`.
Updated proxy contract SHA-256:
`2cd885091fb51e25f8dd90e6f7dddeba9861959063f9d1bcabba884a149e15d8`.
Prior 692-file SQL/full-check-5 evidence remains historical for this changed source.
The owner checkpoint printed these values before/after its full run; this population still excludes
manifests, Dockerfiles and most deployment files and does not replace release evidence.

Exact verified proxy/application image digests, signed release evidence, Cloud Run job/VPC
manifests, runtime credentials/roles, platform retries/deadline and restore rehearsal stay pending.
No package install, release guard/workflow change or cloud mutation is proposed here. The queue
stays paused; Zynth remains later. This runner would provide source preparation, not a production
migration approval or database acceptance result.
Next source review: [scanner readiness and packaging](scanner-preparation-proposal-2026-10-11.md).
