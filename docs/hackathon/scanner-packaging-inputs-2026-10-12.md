# Scanner source packaging preparation — checkpoint 16 log accepted

October 12, 2026. Implements the source portion of [ADR-0070](../decisions/0070-scanner-artifact-release-design.md).
Preserved branch `security/codex-agent-boundary`, HEAD `407a9f4a67611770143198d1f42d605738b01530`
and all existing dirty changes. Checkpoint 15 source binding verified before editing.

## Prepared source

- `accord.scanner.production.create_app()` constructs the actual `ScannerRuntime` directly.
  No runtime argument, fixture fallback, development provider or synthetic data selection.
  Runtime construction still denies incompatible platform/architecture/UID/account.
- `accord.scanner.seed_policy.emit_configuration()` is an asynchronous build-only emitter,
  excluded from the proposed final source allowlist. It requires root Linux/amd64 assembly,
  a fresh root-owned config directory, exact genuine CVD inputs at fixed runtime paths,
  private UID-100 data/temp directories and independently supplied seed/verifier hashes.
- No acquisition or fabricated manifest. Validate exact seed inventory and bounded no-follow
  hashes, root-owned executable verifier hash, then actual native signature checks through
  the existing cancellation-owned launcher. Recheck hashes after verification; write exact
  config bytes exclusively, the actual seeds manifest last, then existing runtime validation.
  Nonzero exit, unavailable verifier, timeout, cancellation or byte drift denies emission.
  Partial writes are not resumable; assemble again in a fresh directory. No destructive cleanup.
- [Proposed source inventory](../../deploy/google/scanner/source-files.txt) explicitly lists
  package/scanner/probe/photo-contract/decoder closure and excludes tests/build-only emitter.
  Its closure test resolves Accord imports. This is not an assembled context or final-layer proof.

The supplied hashes must eventually be bound to reviewed signed acquisition/build evidence.
Hash matching and structural unit tests alone do not establish provenance, freshness or release
acceptance. The existing runtime still verifies signatures, updates and actually loads definitions
before readiness. Genuine definition files, manifests and native executables were not created here.

## Deferred executable listener and build

The proposed all-interface native health listener triggers existing Ruff S104 and Bandit B104.
Removed that proposed executable server command from this source unit; retained only the real
ASGI factory. No suppression, computed address spelling, guard edit or substitute loopback listener.
Native sidecar probing, port 8091, one worker, disabled access logs/proxy trust and graceful shutdown
settings need a separate owner-reviewed network/guardrail decision before executable launch.

Exact signed ClamAV source, base/builder/native toolchain/package pins, Python transitive hash lock,
compile flags and notices remain unresolved. No runnable Dockerfile or guessed pin is emitted.
Future final-layer checks must include inherited layers, installed dependencies and native test
corpora. Real signatures/import/load/update/CDN failure/signals/resource measurements remain open.
The assembly emitter is not invoked by the production factory and has not run natively here.

## Local evidence and owner full gate

33 new source tests and 150 existing scanner/provider/startup tests pass: **183 passed**.
Tests use invented bytes and mocked process boundaries only inside tests; none are production seeds
or native acceptance. Ruff, Black, Bandit pass; mypy checks 414 sources. Policy/DoD and diff whitespace
checks pass. Owner saved checkpoint 16 log verifies all phases:

- Policy fault tests: 776 passed, 18 skipped; backend: 1447 passed, coverage 94.13%.
- Mypy: 414 sources; backend dependency audit passes. Trust verify/vet/lint/race passes;
  vulnerability scan reports zero called vulnerabilities, one imported and twelve required-module
  advisories whose vulnerable symbols are not called. Do not describe that as zero advisories.
- Frontend: 514 tests, successful build, 166.4 kB shared bundle within 250 kB budget.
  Docs site: 31 tests and successful build; both npm audits report zero vulnerabilities.
- Owner pasted DoD: 72 ADRs, 154 standards pass. Current source and ten input hashes match.

Saved `.cache/production-bootstrap/full-check-16.log` SHA-256:
`2be09457f2dc3f9848684c356da88e39ed417b831bbd1f138b79b21de313479f`.
The paste omits numeric command exit and full before/after binding output. Accept observed saved
phases/current binding without claiming an observed exit=0 or rerunning unchanged source tests.
The contract's Docker sandbox boundary requires owner Mac Terminal for disposable PostgreSQL.

Frozen source population: 737 files,
`b9de452a5324bfc7f14b5d19a6938caf62e3c431ca5b49cd158a70351a90dd94`.
The nine previously accepted contracts are unchanged; source inventory SHA-256:
`2d1fe08b898a748914581019cb7f49430c89f149be1e47980d956a70012e8202`.
This population is a checkpoint binding, not a complete release commit/image fingerprint.

Owner local Mac Terminal, outside Codex's sandbox, with Docker running:

```bash
cd "/path/to/gen6th-accord"
/bin/zsh .cache/production-bootstrap/run-scanner-packaging-full-checkpoint.sh
```

The helper verifies branch/HEAD/source/ten input hashes before and after, refuses to overwrite
checkpoint 16's log, unsets `ACCORD_TEST_DATABASE_URL` for disposable test databases, records
`make-check-16 exit=N`, tails the saved log and runs DoD. Report numeric exit, both source/hash
bindings and test/coverage summary. A failed gate stays failed; preserve full log for diagnosis.

Next: resolve real pinned acquisition inputs and review the separate
mandatory scanner build/sign/SBOM/assembly/network guardrail PR. No install/download/build/native
execution, migration/grant, workflow edit, signing/import or cloud mutation occurred. One production
environment, minimum workable measured sizing, Zynth later, Tasks paused, no live stubs/mock data.
