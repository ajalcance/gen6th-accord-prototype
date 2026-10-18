# Internal detection delivery review

This is a separate review unit after the owner-validated workflow target. Read
[ADR-0027](../decisions/0027-durable-persona-detection.md) for limits and semantics.

## Changed unit

- New command detection evaluator/model, migration 0006 and model registration.
- Worker evaluation after sealing, before retention; shared retention lock and supporting-window
  preservation. Existing client expiry and audit protections remain.
- Authorized aggregate persona detection backlog service, using the existing observation action.
- Detection predicate, delivery, concurrency, failure/retry, retention and worker integration
  tests; previous cold-expiry tests now require completed detection as well as sealing.
- Required architecture, security, roadmap, lesson and changelog records.

Do not bundle with setup/H1/storage/review/campaign changes. Git metadata remains read-only
to this agent. Migration and ADR paths require owner review; no self-applied labels.

## Verification

Owner execution on 2026-10-02: **301 passed in 50.58s**, with matching before/after
source fingerprint `7a50df9ccefa699e26d24ce4302729f332d95f3a1166666f4bba8906b4c1c082`
(120 files). The agent independently confirmed that fingerprint on receipt. This covers
the complete target, including the new PostgreSQL cases; it is owner-run evidence,
not agent Docker execution or full-gate completion.

164 non-database tests pass, including eight new predicate/orchestration checks. Fresh
`make check` passed 776 guard tests (18 skipped), policy, harness and backend static checks,
then stopped at pip-audit bootstrap. Full dependency audit and revision-bound CI are pending.
The earlier 279-test source-bound owner result does not cover detection. New PostgreSQL
cases cover tenant/source containment, thresholds, exact retries, atomic batch rollback,
late events/window boundary, concurrent workers, authorized backlog, supporting retention
and real worker orchestration during Redis outage. They cannot execute inside this sandbox.
The current target collects 301 tests: 147 non-database and 154 PostgreSQL cases.
Targeted Semgrep scanned 38 explicit Python sources with nine rules and zero findings;
targeted secret scans of command code and persona tests found no leaks.

Run with Docker active; databases are throwaway:

```bash
cd "/path/to/gen6th-accord"
backend/.venv/bin/python .cache/workflow-source-evidence.py
LC_ALL=en_US.UTF-8 backend/.venv/bin/pytest backend/tests/personas backend/tests/test_migrations.py -q --maxfail=1
backend/.venv/bin/python .cache/workflow-source-evidence.py
```

Share the test summary and both fingerprints. Matching fingerprints bind the result to
source; they do not establish full gates or approve the ADR. No live/cloud service,
notification, enforcement, authentication substitute or public endpoint is activated.

Expected checkpoint fingerprint (120 files):
`7a50df9ccefa699e26d24ce4302729f332d95f3a1166666f4bba8906b4c1c082`.
