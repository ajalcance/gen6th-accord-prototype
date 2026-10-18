# Scanner adapter source checkpoint 14

Owner approved the source-only next unit in the packaging review. ADR-0068 and
`accord.scanner` now prepare health/supervision around a required managed runtime.
There is no automatic launcher, runtime/image selection, daemon config or active scanner.
Tasks remains **PAUSED**. Native scanner validation/signals and release integration remain pending.

## Local evidence

- 33 new synthetic lifecycle/process/HTTP tests pass in 0.29 seconds.
- Combined with 40 existing probe/provider/command-cleanup tests: 73 passed in 1.47 seconds.
- Exact repository-wide mypy passes 404 sources; changed-code Ruff, Black and Bandit pass.
- New files/functions meet 400/50-line limits; whitespace checks pass.
- Existing scan/probe/startup/SQL/TLS/audit/retention and release/agent guards remain unchanged.
  The eight historical contract hashes are preserved; one new source-only health contract added.
- Full checkpoint-14 source phases are verified below. Synthetic children never start a process or access images,
  real definitions, credentials, original pixels or production providers.

## Bound inputs

Branch `security/codex-agent-boundary`, HEAD `407a9f4a67611770143198d1f42d605738b01530`.
Existing dirty tracked/untracked changes preserved. The helper uses the same source population
and sorted relative-path/NUL/bytes/NUL algorithm as earlier checkpoints, plus nine contracts.
This local population excludes some release inputs; it is not full release-commit evidence.

```text
source_files=727
source_sha256=b7927b423611215663b619d31cc6fb97405bff89279994b7d053fca2796efb50
scanner-health-contract.json_sha256=e884a21446d046a81c2e333b4d1c0cf7b010611941107eddf9166ce3cf60342a
```

## Verified owner result

Saved `full-check-14.log` verifies policy 776 passed/18 skipped (49.15 seconds), exact mypy
404 sources and **1351 backend passed in 279.02 seconds, 93.94% coverage**. Trust module
verification/vet/lint/race tests pass; govulncheck reports zero called vulnerabilities, with
one imported-package and twelve required-module advisories not reached by called symbols.
Frontend 514 tests/65 files and docs-site 31 tests/3 files pass; both audits report zero
vulnerabilities. Both builds and frontend bundle budget pass (166.4 kB/250 kB). Owner separate
DoD passes: 70 ADRs, eight backend modules and 154 standards.

Log SHA-256: `d8c96fe8bd3df28788721f6bee566085462f5e73c2a27f117b3e61828598430b`.
The pasted numeric exit and complete before/after output were omitted; do not claim those were
observed. Current source and all nine artifact hashes independently match the frozen helper.
Preserve the log rather than rerunning solely for a truncated paste. Local/disposable evidence
is distinct from revision-bound default-branch CI, signed releases and real scanner acceptance.

Next preparation: exact supported image/source metadata and version-specific runtime/config
design review. Image acquisition/execution, definition downloads and release workflow changes
still require their separate reviewed scopes. No source or frozen contract was changed to record
this evidence.

## Original owner local Mac Terminal

With Docker running, outside Codex's sandbox:

```bash
cd "/path/to/gen6th-accord"
zsh .cache/production-bootstrap/run-scanner-adapter-full-checkpoint.sh
```

The helper refuses to overwrite an existing checkpoint log, verifies source/contracts before and
after, unsets ACCORD_TEST_DATABASE_URL and runs the existing full gate against disposable PostgreSQL.
It prints `make-check-14 exit=...`, the log tail, all fingerprints and DoD output. No scanner is
started by these new tests. Preserve complete output and `.cache/production-bootstrap/full-check-14.log`.
Report the entire Terminal output including numeric exit and leading/trailing hashes. If it fails,
inspect the full underlying exception/SQLSTATE before choosing a fix. Never use production URLs.

## Remaining packaging acceptance

The real managed runtime must validate pinned/version-specific config and bootstrap databases,
keep load testing enabled, register partial starts before yielding and provide actual child
signal/wait semantics. This source interface proves call order, not those real implementations.
Native health port/private exposure, PID-1, startup timings, TERM/reaping, interrupted scans,
definition update/storage peaks and minimum workable resources await isolated owner rehearsal.
Scanner release changes require a separate approved guardrail PR; reviewed default-branch CI and
signed immutable artifact evidence precede owner Cloud Shell checkpoints. No cloud mutation,
resource recreation, production tests or queue resumption. Zynth remains later.
