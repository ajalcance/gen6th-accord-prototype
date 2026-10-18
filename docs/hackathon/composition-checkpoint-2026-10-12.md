# Composition source checkpoint — October 12

Owner approved preparation. [ADR-0065](../decisions/0065-production-startup-composition.md) and the
[runtime inventory](../runbooks/google-container-composition.md) describe the implemented startup
boundary and unresolved packaging. No deployment or cloud action is authorized.

## Verified local preparation

- Branch `security/codex-agent-boundary`; HEAD `407a9f4a67611770143198d1f42d605738b01530`;
  mixed dirty checkout preserved. Previous 704-file source and five SQL/scanner artifacts matched
  checkpoint 10 before this unit. No Git state write occurred.
- Add `runtime_startup.prepare_inspection`, wire inside lifecycle cleanup after role verification
  and before serving. Non-development photos require port 3310 and the existing bounded fresh
  receipt; disabled/development inspection retains its existing behavior. At-use checks unchanged.
- Add 14 synthetic startup tests; together with 26 existing scanner-probe tests, **40 passed**.
  Ruff/Black, exact `mypy .` (**383 source files**), changed-code Bandit, `make policy` and
  `make dod-check` pass. No dependency install, scanner, SQL or Google call was needed.
- New inventory/contract leaves image references, resource selections, routing and activation
  pending. Existing SQL/grant/proxy/scanner artifact bytes unchanged. Official platform documents
  checked; no live platform support or performance acceptance inferred.

## Frozen test population

706 source files, SHA-256:
`a25338feb95f53d2702d0ed959e8ac9762092c1212b667c0ca4775de96ffa0f8`.
Composition contract SHA-256:
`160972a80b08a623ee5e76d866794c9f617107368ca1a77a7533530f1f1f79e3`.
The source population is the same relative-path/NUL/content/NUL algorithm as checkpoint 10,
including the two new Python files; all six deploy artifacts are bound separately. This is a
local test binding, not a complete signed-release/commit fingerprint.

## Owner full-gate evidence — checkpoint 11

Historical owner command, run in local Mac Terminal outside Codex's sandbox with Docker:

```bash
cd "/path/to/gen6th-accord"
zsh .cache/production-bootstrap/run-composition-full-checkpoint.sh
```

The prepared helper validates branch/HEAD/source/artifacts before and after, unsets the test DB
override to use disposable PostgreSQL, runs `make check`, preserves full output in
`.cache/production-bootstrap/full-check-11.log`, prints numeric exit and the last 25 lines, then
runs `make dod-check`. It refuses to overwrite an existing checkpoint log. Preserve the completed log; do not rerun
solely to reproduce a truncated terminal paste.

The pasted output omits the numeric exit and complete before/after hashes. The agent inspected
full-check-11.log: 776 policy tests pass/18 skip; 1263 backend tests pass (172.99s), coverage 93.79%;
383-file mypy; Trust verify/vet/lint/race tests; 514 frontend and 31 docs-site tests, audits and both
builds pass. Govulncheck reports zero reachable vulnerabilities plus one imported/twelve module
advisories without called symbols. Current source and all six artifact hashes match. Owner separate
DoD passes. Every recorded phase is verified; numeric exit and full before/after output are not
independently recorded. Log SHA-256:
`fee919551331a0f37f9ad4c3b45f65fa7e8cd07fbe765e96a24b2a179d841155`.
Previous checkpoint 10 was not used to approve changed source. Container builds/probes, effective
IAM, private routing, production credentials, native startup/shutdown and resource measurements
remain separate. Reference-only factory and compliance health/TERM need owner-reviewed next units.
Do not activate Zynth, resume Tasks, run migrations/grants or deploy while checking this source.
