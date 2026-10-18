# Scanner managed runtime source checkpoint 15

Owner approved the next implementation unit and requires no live stubs or mock data.
[ADR-0069](../decisions/0069-scanner-fixed-managed-runtime.md) and the
[runtime inventory](../runbooks/google-scanner-managed-runtime.md) prepare actual filesystem
and fixed native process integration. No image/executable/definitions or cloud action occurred.
The source unit ships no fixture definitions, manifest or default production app; test fixtures
remain in tests, excluded by the existing backend Docker context. Actual image/native acceptance
and separately reviewed signed scanner release integration remain pending. Tasks **PAUSED**.

## Local verification

- 63 new mocked-process/temporary-filesystem tests pass; combined with existing scanner, provider
  and startup tests: **150 passed in 1.73 seconds**. No native subprocess is executed.
- Exact repository-wide mypy passes 410 source files; changed-code Ruff, Black and Bandit pass.
- `make policy` passes coverage wiring, Unicode, risk context, DoD, readiness, standards, local
  settings and exact dependency pin checks. This is source/document evidence, not runtime acceptance.
- New files/functions meet the 400/50-line limits; whitespace checks pass.
- Existing scanner/probe/supervision/startup, SQL/TLS/audit/retention, release/agent guards and
  all nine historical artifact hashes remain unchanged.
- Checkpoint-15 source phases are verified below; current source and all nine hashes match.
  Disposable PostgreSQL evidence is distinct from real scanner/image/native acceptance.

## Bound inputs

Branch `security/codex-agent-boundary`, HEAD `407a9f4a67611770143198d1f42d605738b01530`.
Existing mixed dirty checkout is preserved. Population uses earlier sorted path/NUL/bytes/NUL
algorithm; it excludes some packaging/release inputs and is not full release-commit evidence.

```text
source_files=733
source_sha256=76087f68b93464a86595c8b2c2a6767f4898a806a4d681fbd4bdafb3132cbe71
scanner-health-contract.json_sha256=e884a21446d046a81c2e333b4d1c0cf7b010611941107eddf9166ce3cf60342a
compliance-contract.json_sha256=e2d6e005e7df76915852b4f16643940d0b5b9e639ea9f50d081d7d4351c6ebb5
sql-runtime-roles.sql_sha256=78775fc091eb30174afec0bc2685bfe2cd4f9bca54dff36034cc698f8ed312cc
sql-runtime-grants.sql_sha256=b4933e2a6dfd6f8af53f28a16561b221e058d788785a394db076164068129dba
sql-roles-contract.json_sha256=c9f3df87329e38a674da2aa10be06285d919548007dadc1abf8651fd0936711b
sql-proxy-contract.json_sha256=2cd885091fb51e25f8dd90e6f7dddeba9861959063f9d1bcabba884a149e15d8
scanner-contract.json_sha256=f101fbd6f9c89b4c3a70530a6db7723df043a2b380190ff5ea8d9de5a7fd0292
reference-contract.json_sha256=2ca2ebece5159908e75c85eacb6a8c6365f7809e09cd1bfd11522f747001f71e
composition-contract.json_sha256=160972a80b08a623ee5e76d866794c9f617107368ca1a77a7533530f1f1f79e3
```

## Verified owner result

Saved `full-check-15.log` verifies policy 776 passed/18 skipped (44.34 seconds), exact mypy
410 sources and **1414 backend passed in 181.41 seconds, 94.10% coverage**. Trust verification,
vet/lint/race tests pass; govulncheck reports zero called vulnerabilities, with one imported-package
and twelve required-module advisories not reached by called symbols. Frontend 514 tests/65 files
and docs-site 31 tests/3 files pass; both audits report zero vulnerabilities. Both builds and
frontend bundle budget pass (166.4 kB/250 kB). Owner separate DoD passes: 71 ADRs, eight backend
modules, 154 standards.

Log SHA-256: `cac005ce94a7e0ab15b0816f556558be3a5df7ba5937df3f995c53d10c386dd2`.
Pasted numeric exit and full before/after output were omitted; do not claim those were observed.
Current fingerprints independently match the frozen helper. No rerun solely for truncated paste.
Source acceptance is recorded; native executable/config/parser/signature/update/load behavior,
real signals and image/resources remain pending. No production stub or mock data is accepted.
Next: scanner image assembly/release integration design, with a separate owner-approved guardrail
PR before release workflow changes; signed artifact and isolated real acceptance precede cloud.

## Original owner local Mac Terminal checkpoint

With Docker running, outside Codex's sandbox:

```bash
cd "/path/to/gen6th-accord"
zsh .cache/production-bootstrap/run-scanner-runtime-full-checkpoint.sh
```

The helper refuses to overwrite checkpoint 15's log, verifies source and nine artifacts before
and after, unsets ACCORD_TEST_DATABASE_URL and runs the existing full gate against disposable
PostgreSQL. It prints numeric `make-check-15 exit=...`, fingerprints, log tail and DoD; nonzero
gate/binding/DoD status denies acceptance. No new test launches native scanner processes.
Report the entire Terminal output and retain `.cache/production-bootstrap/full-check-15.log`.
If anything fails, inspect the full underlying exception/SQLSTATE before deciding a fix.

Do not point tests at production, install/download/run scanners, recreate resources, resume
Tasks or perform cloud mutations. Cloud checkpoints remain owner-run after reviewed CI, signed
immutable release evidence and real isolated runtime acceptance. Zynth sign-in remains later.
