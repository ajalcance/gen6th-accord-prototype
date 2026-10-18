# H2 independent review and campaign handoff — 2026-10-02

These are internal fictional workflows, with no HTTP routes, UI/backend connection,
identity fallback, private uploads, signature issuance or service activation.
The owner reset the work window to 06:39:23–11:39:23 Asia/Manila on 2026-10-02.

## Review units, in dependency order

Preserve the prior setup/dependency, planning and accepted H1 changes. Do not stage the
whole dirty security branch. Git metadata is read-only to this agent; no commit/PR exists.
Each unit needs its own tests/docs and owner-controlled sensitive-path/ADR review before merge.

1. **Storage/observation:** ADR-0024, migration 0003 and earlier persona storage/worker
   changes. The owner reported its earlier 92-test target passing in 20.31s. That report
   has no supplied source hash and predates the following units.
2. **Independent review:** ADR-0025, migration 0004, `personas/review_models.py`,
   `review_policy.py`, `reviews.py`, `workflow_contracts.py`, `workflow_repository.py`,
   `workflow_events.py`; tests `test_review_contracts.py`, `test_reviews.py`,
   `test_review_safety.py`, `test_review_history.py`, `test_review_migrations.py`,
   `workflow_fixtures.py` and `review_migration_fixtures.py`. Shared transaction changes
   preserve nonhuman rejection attribution. Review/context data is fixture-only.
3. **Campaign permission:** ADR-0026, migration 0005, `personas/campaign*.py` and
   tests `test_campaign*.py`, `campaign_fixtures.py`, `test_workflow_migrations.py`.
   Offers and decisions bind the exact version/review; fixture asset relations enforce
   tenant/version boundaries. Recipient change requests withdraw use; revocation is final.
4. **Workflow evidence:** `personas/workflow_evidence*.py`, tests
   `test_workflow_evidence.py` and `test_workflow_evidence_contract.py`. Match immutable
   record attribution to a cold server event or retained audit entry. No chain/signature
   verification or current-use permission is implied by presence.

Model/action registries and documentation contain shared hunks. Select only each unit's
imports, registration/actions and matching records. Shared migration protection tests derive
the actual registered persona tables, so review can precede campaign without a campaign import.
`service.fingerprint` accepts bounded Pydantic intents for semantic retry equality only.
Never use it as an evidence fingerprint, signing key or ownership certificate.

## Behavior and verification

- Review commands have no actor/role/receipt-time fields. Stored reviewer role and trusted
  internal human fixture context are required; owners/contributors cannot review themselves.
- Persona-head locking serializes edits, reviews and campaign transitions. Expected previous
  decision IDs prevent lost updates; exact retries acknowledge historical immutable records.
- Only the owner can offer or revoke. Only the named recipient can accept/request changes.
  Campaign scope/history/evidence reads deny unrelated workspace members.
- Current fixture eligibility rechecks head, exact latest review, roles, decisions and time.
  A new approval of the same version cannot revive offers tied to an older review ID.
- Version/decision records and minimal server events commit atomically. Statements, purposes
  and conditions do not enter the event/audit stream. All nine actions have coverage decisions.
- New migrations freeze SQL independently of metadata listeners. Tests exercise both schemas,
  scoped read/write denial, immutable triggers, composite references, rollback and races.

Owner validation on source fingerprint `87487b393bfa2ce5b8ffbe1360b6e632406fb3b2b179392610a190e643fd3890`
stopped at 48 passes on mismatched expiry instants in the test fixture. Both offers now share
one scope. The owner reran the corrected source on 2026-10-02: **279 passed in 48.86s**,
with matching before/after fingerprint
`b3aa303525fca65a2d78be65817755dbddef9694c17d9411ce1d8d88ea66a8f4` (111 files).
The agent independently confirmed that fingerprint after receiving the result.

Current local evidence: 156 non-database tests pass; lint, formatting, mypy and size checks
pass. Semgrep: 36 explicit Python targets, nine applicable rules, zero findings. The current
persona/migration collection at that checkpoint was 279 tests: 139 non-database and 140
PostgreSQL cases. The subsequent [detection slice](h2-detection-review.md) has its own
expanded target and evidence. None of
the newly added SQL cases have executed in this agent sandbox; the owner-run result covers
the full target, including those cases. Full-gate completion remains
blocked at pip-audit bootstrap; do not mark this work production-ready or owner-accepted.

## Owner validation

Docker is inaccessible to the agent under CLAUDE.md §4 / ADR-0020; no unsandboxed retry is
permitted. With Docker running, this targets throwaway databases, not the active local stack:

```bash
cd "/path/to/gen6th-accord"
backend/.venv/bin/python .cache/workflow-source-evidence.py
LC_ALL=en_US.UTF-8 backend/.venv/bin/pytest backend/tests/personas backend/tests/test_migrations.py -q --maxfail=1
backend/.venv/bin/python .cache/workflow-source-evidence.py
```

The source fingerprint helper is an ignored local handoff artifact. It hashes allowlisted
backend Python/test/migration files and five explicit configuration inputs, never `.env` or
credentials. Share matching before/after hashes and the summary/first failure. This binds the
report to source bytes without claiming a commit or green CI result. Then run `make check`
with Node 22 and report the full result separately.

Zynth remains deferred. Reliable detection delivery, private-data protection, restricted
database credentials and trusted sessions precede reachable routes. Hack2skill acknowledgment,
source-package eligibility and publication approval remain pending.
