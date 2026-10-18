# Compliance lifecycle source checkpoint 13

Owner approved the lifecycle proposal. ADR-0067 prepares `accord.compliance:app`, a confined
health-only factory wrapping unchanged compliance processing. This is deployment preparation;
production activation and native container acceptance remain pending. Tasks stays **PAUSED**.

## Verified local evidence

- Branch `security/codex-agent-boundary`, HEAD `407a9f4a67611770143198d1f42d605738b01530`;
  existing mixed tracked/untracked changes preserved.
- 31 synthetic lifecycle/configuration/health tests pass; exact repository-wide mypy passes
  396 sources. Ruff, Black, Bandit, policy, DoD and diff whitespace checks pass.
- Both disposable PostgreSQL tests pass within the owner checkpoint-13 suite. They test
  confined factory/audit/detection/retention during Redis outage and active transaction rollback
  while preserving earlier ingestion commits. Early SQL exceptions retain their full traceback.
- New files/functions meet the 400/50-line limits. No existing worker, SQL-role predicate,
  migration, release workflow, security gate or agent policy was changed by this unit.

## Bound inputs

The ignored helper binds the source population used by earlier checkpoints (relative path,
NUL, bytes, NUL in sorted order) and eight deployment contracts. This is a local dirty-tree
checkpoint, not a release commit or revision-bound CI result.

```text
source_files=719
source_sha256=e5bc0137034e9573ee3f8123e1955697d64fbc76e8e2bc9919d8f9773a997965
compliance-contract.json_sha256=e2d6e005e7df76915852b4f16643940d0b5b9e639ea9f50d081d7d4351c6ebb5
```

The seven earlier SQL/scanner/reference/composition contract hashes remain unchanged.
Historical checkpoint helpers and logs are preserved.

## Verified owner result

Saved `full-check-13.log` verifies policy 776 passed/18 skipped; mypy 396 sources; backend
**1318 passed in 182.75 seconds, 93.86% coverage**, including both confined SQL lifecycle tests.
Trust module verification/vet/lint/race tests pass; govulncheck reports zero called vulnerabilities
with one imported-package and twelve required-module advisories not reached by called symbols.
Frontend 514 tests/65 files and docs-site 31 tests/3 files pass, both audits report zero
vulnerabilities, both builds and the frontend bundle budget pass. Owner separately reports DoD
green (69 ADRs, 154 standards); local DoD also verifies documentation consistency.

Log SHA-256: `6a3a362866710592c67e39aae95dccf62e5e308839961b3ef2c81da0072dcbaf`.
The pasted numeric exit and full before/after output were omitted. Current source and all eight
contract hashes independently match the frozen helper; do not claim the omitted exit was observed.
Preserve this log and do not rerun solely for the truncated paste. Real Redis TLS and native
container termination remain pending; this is source/disposable evidence.

## Original owner local Mac Terminal checkpoint

Run outside Codex's sandbox with Docker running. The helper unsets `ACCORD_TEST_DATABASE_URL`,
so the backend suite uses disposable PostgreSQL; never substitute production credentials.
It refuses to overwrite an existing checkpoint-13 log, checks fingerprints before/after,
captures the complete gate log, prints the numeric exit and runs DoD.

```bash
cd "/path/to/gen6th-accord"
zsh .cache/production-bootstrap/run-compliance-full-checkpoint.sh
```

Report the complete Terminal output, including `make-check-13 exit=...` and both fingerprints.
Full underlying failures are retained in `.cache/production-bootstrap/full-check-13.log`;
obtain the actual exception/SQLSTATE before choosing any repair. Do not rerun solely to replace
a truncated paste or change guards to obtain green.

## Remaining deployment evidence

Reviewed PR/default-branch CI and signed immutable release are still required.
The compliance SQL credential, independent base settings secret, verified Redis CA mount,
image digest, measured minimum resources and private native probe configuration are unresolved.
Real TERM with proxy drain, active SQL rollback and Redis/pool cleanup must be rehearsed in
the final topology. Cooperative deadlines are not hard process termination guarantees.
Scanner packaging, reference reconcile IAM, private routing and owner Cloud Shell checkpoints
remain separate. No cloud resources, grants, migrations, services, jobs or images were activated.
