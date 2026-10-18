# SQL role source validation checkpoint — October 12

Prepared owner-approved ADR-0064 unit. No production SQL, login, credentials or cloud mutation.
[Inventory/limits](../runbooks/google-sql-role-preparation.md) and [decision](../decisions/0064-distinct-production-sql-roles.md).
Existing mixed dirty checkout is preserved: `security/codex-agent-boundary`,
HEAD `407a9f4a67611770143198d1f42d605738b01530`.

## Verified results and repair

Owner disposable PostgreSQL acceptance passes **32 tests in 24.04s**, verified from
`.cache/production-bootstrap/sql-role-focused-2.log`. The missing hardcoded postgres target
was replaced with the actual disposable operator; exact SQLSTATE 42501 denial remains.

Full-check-9 passes policy/harness and backend Ruff/Black, then fails at mypy: the new nested
conftest was mapped to the root conftest module. Add only `backend/tests/sql_roles/__init__.py`,
following the existing auth/personas package layout. Exact `.venv/bin/mypy .` now passes
**381 source files**; no mypy configuration, exclusion, grant, migration or guard change.
The frozen contract's status records focused success at preparation time; full acceptance follows.

Owner **full-check-10 exits 0**: **1249 backend passed in 240.79s, 93.58% coverage**;
Trust, **514 frontend**, **31 docs-site**, builds/audits and separate DoD pass.
Policy reports 776 passed/18 skipped. Go analysis reports zero reachable vulnerabilities,
with imported/module advisories still reported; this is not an all-dependency zero-advisory claim.
Source/SQL/contracts printed before/after match the current independently verified snapshot.
Log SHA-256: `a5d21090a33822879154ec5f4e8583dfcdbbc66074fc960580b642a3a3bd1274`.
SQL files and tested contracts stay frozen; record acceptance here rather than changing tested bytes.

Earlier source snapshots remain bound by their own scratch checkers/logs:
initial 703 files `902bcd865dc00981029055069080bd64c009956b9d415aed6fb8e629ba3e37f0`;
diagnostic 703 files `315bb179f118f72949f911399bd46c1d0c9ed37dbad4c7dad7d600f13d79f2eb`;
operator correction 703 files `9eda63b33d851de5627acfc4a33360ea23f0871c85dd678426f9b53cce818242`.

## Accepted full-gate checkpoint

Current package-corrected population: **704 source files**,
`275c05cf8087ecf1b6c66ff4fb5d48638025ed68d3312c5ae578ca45d569cd05`.
`.cache/production-bootstrap/roles-source-fingerprint-3.py` independently binds both SQL files
and all three contracts. This population excludes documentation/container artifacts and is not
a complete signed-release identity. Historical logs/checkers are retained.

Run in the owner's **local Mac Terminal outside Codex's sandbox**, with Docker running.
CLAUDE.md §4/ADR-0020 leaves Docker-backed tests to owner/CI; no unsandboxed agent retry.
The command explicitly unsets ACCORD_TEST_DATABASE_URL and uses pinned disposable PostgreSQL.
Full check includes the 32 role tests, so a separate repeated focused run is unnecessary.

```bash
cd "/path/to/gen6th-accord"
zsh .cache/production-bootstrap/run-role-full-checkpoint.sh
```

Report the make-check-10 exit line, before/after hashes, gate tail and DoD output.
The script retains full-check-9 and writes `.cache/production-bootstrap/full-check-10.log`.
If a test fails, preserve its complete SQL traceback/SQLSTATE before deciding a correction.
No installs, login activation, production tests or cloud changes. Tasks stays paused; Zynth later.
Reviewed CI and signed release remain required before owner production checkpoints.
Next proposed unit: [container composition/startup preparation](container-composition-proposal-2026-10-12.md).
