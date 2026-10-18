# H2 secure-core readiness — 2026-10-01

Latest evidence: 2026-10-02 (Asia/Manila). Owner-reported PostgreSQL run: 92 passed in 20.31s.
This is terminal evidence supplied by the owner, not an agent-observed run or commit-bound CI result.
The owner reset the five-hour window: 2026-10-02 06:39:23–11:39:23 Asia/Manila.
The 92-test result predates independent review/campaign persistence (ADRs 0025/0026).
Current non-database selection: 156 pass. Current PostgreSQL target: 279 tests collected,
139 non-database and 140 database; the current SQL run remains pending.

The owner accepted H1's frontend and approved persistence/observability, then independent
review and campaign slices. Zynth repository work is deferred. Implement complete behaviours
within each authorized slice; retain explicit activation and verification boundaries.

## Implemented locally, not activated

`backend/accord/personas/` contains bounded fixture contracts, PostgreSQL models, scoped
repository operations, transactional service and rejection tracking. Migration 0003 adds
membership, mutable persona heads, immutable versions and exact-retry receipts. Tenant
policies apply transaction-local workspace context; triggers reject version/receipt mutation.

Writes authorize stored membership and ownership, lock membership/head, check expected revision
and commit head/version/server-event/receipt together. Exact retries return the original
snapshot only after fresh authorization; changed payloads conflict. Reads authorize membership
and commit a minimal correlated event. Rejections roll back attempted work before storing
a bounded denial/conflict event. Database failure can prevent durable rejection evidence;
the operation fails and logs only its bounded request UUID. Write request UUIDs are retry
keys supplied with the intent; persona/version/event IDs and observation IDs are server-built.

Events enter the existing cold store directly. The audit worker seals asynchronously;
commit is not sealing. Expiry retains auditable server events lacking an audit entry.
Deletion counts come from one PostgreSQL delete/count operation, unaffected by concurrent
inserts. Receipt observation refreshes database rows so expired events are not read from
an old ORM identity-map entry.
Redis outage pauses ingestion while sealing already durable events continues. A PostgreSQL
transaction advisory lock serializes sealers even before the first audit entry exists.
Nine actions have emit/detection/audit/compliance registration. Direct writes do not deliver
events to Redis detection yet: registration is not an observed alarm.
`health.py` provides membership-scoped pending audit counts and oldest event time, using one
aggregate query and a tenant index. The observation itself is recorded after the measured
snapshot; it is not included in that response's count. No automatic monitor is activated.

Migration 0004 adds immutable version-bound review decisions with exact retry receipts,
stored reviewer permissions, trusted human fixture context, self-review denial, head locking
and expected-previous-ID ordering. Bounded history reads record observations.
Migration 0005 adds immutable campaign offers, server-seeded fixture asset references,
exact tenant/version asset bindings and independent named-recipient decisions. Change
requests withdraw acceptance; creator revocation is final for that offer. Current fixture
eligibility rechecks version, exact latest review, roles, latest decision and server time.
Historical receipts remain historical after edits, withdrawal or expiry. Campaign scope,
history and evidence are private to its owner and named recipient.
Workflow evidence inspection reports matching cold-event or audit-entry presence, validates
server attribution/references and fails closed on gaps. It does not verify chain integrity,
sign a package or determine current-use permission. All statement/scope text stays out of events.

No HTTP routes, membership grant endpoint, UI/backend connection, private-evidence encryption
or identity substitute is introduced. Existing HMAC identity is scaffolding. Current local
PostgreSQL administrator credentials do not prove RLS application isolation.
See [ADR-0024](../decisions/0024-persona-transactional-persistence.md),
[ADR-0025](../decisions/0025-version-bound-human-review.md) and
[ADR-0026](../decisions/0026-scoped-campaign-permission.md) for separate review units.

## Current verification

- 156 non-database tests pass: earlier contracts/receipt/backlog/worker/coverage checks plus
  review/campaign scope, history bounds, status consistency and workflow reference tests. These verify neither
  executing SQL nor database races. Static lint/types and Bandit pass.
- Database tests cover save/reload/seal, exact/changed retries, stale revisions, authorization,
  membership role changes, concurrent requests, rollback injection, immutable triggers, RLS
  expiry, Redis outage, concurrent sealing and scoped backlog. The agent's run stopped at Docker
  setup (`Operation not permitted`); the owner subsequently reported the entire target suite passing.
  Migration tests now inspect installed RLS/policies/triggers, beyond model/schema comparison.
  They seed migrated tables to test update/delete rejection, missing/other-workspace inserts
  and scoped reads; metadata-only tests cannot prove those migration paths.
  Earlier target: 92 tests, including 46 database tests; owner reported all 92 passing.
  Current target: 279 tests, including 140 database tests awaiting a new run. New cases cover
  review/campaign races, rollback, self-review, exact asset/version binding, withdrawal,
  expiry, private history/evidence and actual migrated RLS/immutable enforcement.
  New database tests force concurrent writes during retention and rejection-record failure.
  Worker logging omits raw exception text; rejected-record failure logs only a request UUID.
- `make check` with the required Node 22 passed 776 guards (18 skipped), policy, harness and
  backend static checks, then stopped at pip-audit's network-dependent bootstrap. No clean
  full-gate or production-readiness claim is made.
- Source-size review found no violations in 69 source files. Earlier local gitleaks found no secrets in
  persona service/tests, command code or migrations. Semgrep initially failed with empty CA
  anchors. The documented `/etc/ssl/cert.pem` bundle then allowed it to scan all 36 targeted
  Python source files with nine applicable rules and zero findings (exit 0). No policy/rule/
  verification setting changed. Pip-audit still fails at bootstrap with that bundle.
- No commit/PR was created. Existing local setup, H1, planning and persistence review units
  remain uncommitted. Owner review labels cannot be applied by the agent.

## Next order and acceptance gates

1. Obtain a fresh full-gate result in the owner's terminal or CI. The owner supplied a passing
   targeted PostgreSQL result; rerun it after subsequent implementation changes.
2. Validate scoped receipt inspection (`observability.py`) and backlog observation (`health.py`), which report event
   and audit-entry presence without claiming verified chain integrity. Then implement
   reliable detection delivery/recovery; the existing engine is only a rule registry.
   Monitor retained unsealed backlog before routes become reachable.
3. Obtain current PostgreSQL proof for the independent review/campaign implementation,
   preserving its immutable version binding, permissions and stale approval protection.
4. Resume Zynth inspection when requested. Validate issuer/audience/expiry, JWKS, PKCE,
   server-side sessions, revocation and trusted membership. Do not read sibling repositories
   or credentials, register clients or activate services through this slice's authorization.
5. Apply private-data protection and restricted runtime grants. Connect the UI once trusted
   identity and the database boundary are tested. Show save/loading/error recovery and
  distinguish committed event, pending sealing and sealed audit evidence.

## Review units and owner test command

Keep prior setup/dependency work, prototype planning, H1 and H2 in separate reviews. H2 is
base storage, independent review, campaign permission and workflow evidence. See
[review/campaign handoff](h2-workflow-review.md) for paths and dependencies. Persona registration
changes under `command/` and `telemetry/`, model registration and migration protection tests
have shared hunks across these units.
Shared documentation requires selecting the matching hunks; do not stage everything on the
existing security branch. ADR/sensitive-path review labels remain owner-controlled.

Owner supplied the following targeted command and reported `92 passed in 20.31s`:

```bash
LC_ALL=en_US.UTF-8 backend/.venv/bin/pytest backend/tests/personas backend/tests/test_migrations.py -q --maxfail=1
```

No source hash accompanied that report. Bind future CI/review evidence to the reviewed revision.
With Docker running, this targets throwaway test databases, not the existing local stack:
The default PostgreSQL container can assume predefined read/write test roles. An external
test server must permit those role switches as well as database creation. No production-role
grant is requested or changed by this implementation.

```bash
cd "/path/to/gen6th-accord"
export PATH="/opt/homebrew/opt/node@22/bin:$PWD/.tools/bin:$PATH"
backend/.venv/bin/python .cache/workflow-source-evidence.py
LC_ALL=en_US.UTF-8 backend/.venv/bin/pytest backend/tests/personas backend/tests/test_migrations.py -q --maxfail=1
backend/.venv/bin/python .cache/workflow-source-evidence.py
```

Expected: 279 targeted tests pass, including migration reversal/parity and database policies.
The before/after source fingerprints must match; include them with the terminal summary.
Then run `make check`; report its final result separately. Neither command activates persona
routes, provider sessions or cloud services. Share the summary or first failure without secrets.

No cloud activation, deployment, signing, publication or visibility/licensing change.
Hack2skill acknowledgment and eligibility/source packaging remain pending.
