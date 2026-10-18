# Backend SQL and job recovery repair — October 11

Date: 2026-10-11, Asia/Manila. Refines ADR-0055; no new runtime design or activation.

## Verified starting point

Read-only warm-up matched branch `security/codex-agent-boundary`, HEAD
`407a9f4a67611770143198d1f42d605738b01530`, and the October 11 handoff fingerprint:
687 files, `a5bab9b47da914cf9dd3d9fa03639f55ff182c72e118f5217a1ccfe4e5fb7200`.
Existing tracked/untracked changes were preserved. The earlier owner tail reported
795 passed, 2 failed, 307 errors, 81.25% coverage; it did not contain full SQL errors.

## Underlying errors and corrections

Owner ran three focused diagnostics with the external test-server override cleared,
forcing pinned disposable Docker PostgreSQL. All exited 1 with the same failing SQL:
`CREATE FUNCTION accord_face_job_transition()`. Upgrade and roundtrip failed at
`0015jobs`; roundtrip never reached downgrade. Metadata schema creation failed in the
same function. The exception was `asyncpg.exceptions.PostgresSyntaxError`,
`syntax error at end of input`; the installed exception class maps to SQLSTATE `42601`.
The logs do not separately print its numeric SQLSTATE field.

The unparenthesized CASE expression inside an IF condition exposed its inner THEN to
the PL/pgSQL condition parser. Parenthesize the expression in `personas/job_policy.py`
and frozen migration `0015_face_jobs.py`, preserving attempt/sequence enforcement.
[PostgreSQL 17 parser](https://github.com/postgres/postgres/blob/REL_17_STABLE/src/pl/plpgsql/src/pl_gram.y).

The next owner run passed 26 cases but failed five job cases with MissingGreenlet:
queue-outage rollback expired the job object, and enqueue read its ID after dispatch.
Retain the ID before dispatch and use the command's job ID for update receipts.
Retain the worker sequence before processing so rollback cannot mask failure recording.
[SQLAlchemy rollback expiration](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#rolling-back).

The detection test omitted five registered asset/passport/publication actions.
Extend its explicit independent expected set; keep client/unknown exclusions and all
production registry, detection, audit and compliance decisions. No guard was weakened.
SQL regression cases reject an incorrect running-attempt increment and prove provider
failure recording, queue-outage retry and exact retry replay against real disposable SQL.

The first full owner rerun removed setup errors but exposed 53 behavior failures:
1053 passed, 53 failed, coverage 92.39%. Most were the campaign production constraint:
JSONB's default encoded Python None as JSON null instead of the allowed SQL NULL.
Use `JSONB(none_as_null=True)`; keep the constraint and explicitly test rejection of JSON null.
The investigation-review resource type exceeded the existing VARCHAR(32) event column;
use `persona_investigation_review` and verify persisted server attribution/operation.
The exact-file search test predated approved-reference search. ADR-0050 preserves references
when removing the display photo: test both inherited references and explicit empty replacement.
Production schema, constraints, reference policy and activation gates remain unchanged.

## Evidence

Local expanded non-database selection: **51 passed**, covering detection contracts, job SQL rendering,
service/worker orchestration, investigation-review contracts, production migration and spine coverage.
Owner repaired focused run: **32 passed in 14.29s**, exit 0. Selection includes all of
`test_migrations.py`, asset-enrollment SQL, job database, job migration and detection contract.
First full rerun passed 776 guards (18 skipped), policy/harness, backend static/security checks
and dependency audit, then failed backend behaviors above. Later Trust/frontend/docs-site phases
were not run. Owner/local DoD passed independently. Second full rerun passed **1108 backend
tests in 133.85s**, coverage **93.13%**, then passed Trust checks and frontend types/lint/format.
It stopped at npm audit: sharp 0.35.4 and source-map-js 1.2.1 have high-severity advisories.
Owner DoD again passed; frontend tests/build and docs-site gate were not reached.

Both frontend and docs-site manifests now pin sharp **0.35.5** and source-map-js **1.2.2**.
Their upstream releases contain the fixes: [sharp release](https://github.com/lovell/sharp/releases/tag/v0.35.5),
[source-map-js release](https://github.com/7rulnik/source-map-js/releases/tag/v1.2.2).
Owner used the existing npm 11.16.0 at `.cache/npm-resolver/node_modules/npm/bin/npm-cli.js`
to refresh locks and install from them. Both manifests/locks now agree on the patched versions;
the existing vendored braces override remains. Audit stays enforced; no forced upgrade or
install-script approval policy change was performed by the agent.
Third owner full `make check` exited **0**: 776 guards (18 skipped), **1108 backend passed
in 194.13s**, coverage **93.12%**, Trust, **514 frontend** and **31 docs-site** tests, both
builds and npm audits with **zero vulnerabilities**. Owner/local DoD passed.
Later [Redis CA source preparation](redis-ca-preparation-2026-10-11.md) has its own successful
fourth full gate: 1122 backend passed, 93.26% coverage; all later phases and DoD passed.

Gitignored logs under `.cache/production-bootstrap/`, SHA-256:

| Log | SHA-256 |
|---|---|
| migration-upgrade.log | `2de92401cc097fde2e8bf8f9479f7bac31638fb118c16ac6e942d1927bac18cb` |
| migration-roundtrip.log | `e7b9d2c1ca52ee6ea58d8a0fa90b740836b183ba4c606537a788721663f792c3` |
| schema-template.log | `7aed4f3bd1cf8af91c4c9206f6176380e74e3581f2a4cc5164d70802e36e117e` |
| repaired-focused.log | `a658760907a2f6a4b5c395f6a76a8399dc514153a166b2b355a440976bcafec2` |
| repaired-focused-2.log | `a076471dba5c78ca9b855c4e3cee6e29a3c73782ce608d5f33d8883da8827021` |
| full-check.log | `3549898e61165702ec4c1a85d86a61d607463c31f8e46fe184d83b17f66bbcd0` |
| dod-check.log | `67df3713f8a2b57c95c955106113acbce06e4b09a2cb650b582dfa85e576fa8e` |
| full-check-2.log | `0f559cf3dd022073ce3c462b9f47da6806c862f9a822a85faeb5f5be8890b8ec` |
| dod-check-2.log | `67df3713f8a2b57c95c955106113acbce06e4b09a2cb650b582dfa85e576fa8e` |
| full-check-3.log | `7a70bc631f20820004bfa698d62c3e26057ae725636b7aa3212f79603e0931af` |
| full-check-4.log | `321fab911ede9debfc1540b42adb0f96e63c2a1e4ce1cffeaa61bfb47956be68` |

First repair fingerprint: 687 files,
`76944737f9a8cbe093a0fadbfaa50e1be5951d94e537f3cf66cf21f61db04a42`.
After the three full-suite corrections, the same handoff population is 687 files,
`55d41e71fa3a90d59749fd450207da6f3fc7de812173b8e330e2378aaa78a1c2`.
This is a current source snapshot; the owner logs have no leading fingerprint and do not
independently bind their execution to it. It excludes manifests and most deployment files.

## Remaining sequence

Repair/dependency baseline and subsequent CA preparation are full-green. Review the
[SQL transport proposal](sql-transport-proposal-2026-10-11.md), then continue scanner/workers,
ingress and rollback packaging. No deployment design is approved by a test result.
PR review, exact-main CI and signed immutable release/import remain required before owner-run
Cloud Shell mutations. Production tests/migrations were not run. No resources, credentials,
flags, services or images were changed; the Tasks queue stays paused and Zynth setup stays later.
