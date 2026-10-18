# Reference runtime source checkpoint — October 12

Owner approved [reference preparation](reference-runtime-proposal-2026-10-12.md).
[ADR-0066](../decisions/0066-reference-only-runtime.md) and the
[runtime inventory](../runbooks/google-reference-runtime.md) describe the prepared source.
No deployment, grant or production action is authorized.

## Prepared and verified

- Existing branch `security/codex-agent-boundary`, HEAD
  `407a9f4a67611770143198d1f42d605738b01530`; dirty checkout preserved, no Git state writes.
  Checkpoint-11 source and all six artifacts matched before this unit.
- `accord.reference:app` uses independent `reference_app`/`reference_bootstrap`, mounts only health
  and existing authenticated execute/reconcile routes. API bootstrap and existing guards unchanged.
- Production/reference proxy configuration, workspace and Linux/service presence are explicit;
  browser/photo API flags stay false. Exact full Google config fingerprint matches API job binding.
  Lazy wrapping/face/Tasks/identity assembly obtains no credentials and calls no network.
- No browser, Redis, scanner, signing or investigation provider is constructed. Job events use
  existing SQL transactions. Reconcile requires additional Tasks authority, not recorded for the
  reference identity; inventory preserves that owner checkpoint without changing IAM.
- 21 new synthetic configuration/factory tests plus existing signed OIDC/job tests: **46 pass**.
  Ruff/Black, changed-code Bandit, exact mypy . (**389 source files**), policy and DoD pass.
  One new disposable SQL factory/reconcile/completion/exact-replay test passes in checkpoint 12.

## Frozen population

712 source files, SHA-256:
`7a3b58f4de2a22ba6c42f07f280bc5a384cadc5b02ee41608a885cc757726b98`.
New reference contract SHA-256:
`2ca2ebece5159908e75c85eacb6a8c6365f7809e09cd1bfd11522f747001f71e`.
Same relative-path/NUL/content/NUL population algorithm as checkpoint 11; six new Python files.
Seven deploy artifacts are bound separately. This is local source evidence, not a signed release.

## Owner full gate 12 — recorded phase evidence

Historical owner command, run in local Mac Terminal outside Codex's sandbox with Docker:

```bash
cd "/path/to/gen6th-accord"
zsh .cache/production-bootstrap/run-reference-full-checkpoint.sh
```

Helper checks branch/HEAD/source/artifacts, unsets ACCORD_TEST_DATABASE_URL, runs `make check` on
disposable PostgreSQL, prints numeric exit and post-run hashes, preserves the complete output in
`.cache/production-bootstrap/full-check-12.log`, prints its tail and runs `make dod-check`.
It refuses to overwrite an existing log. Preserve full-check-12.log; do not rerun solely to
reproduce a truncated paste.

Owner pasted final build/DoD output and matching artifact hashes, but omitted the numeric exit and
complete before/after population output. Agent inspected the saved log: 776 policy tests pass/18 skip;
389-file mypy, 1285 backend tests pass (172.59s), coverage 93.81%; Trust verify/vet/lint/race and zero
reachable vulnerability findings; 514 frontend and 31 docs-site tests, dependency audits and both
builds pass. Govulncheck additionally lists one imported/twelve module advisories without called
symbols. Current source and all seven artifact hashes match the frozen binding. Separate owner
DoD passes. All recorded phases are verified; numeric exit/full before-and-after output are not
independently recorded. Log SHA-256:
`6a372682da28110eff01b3c8989d2024356762a471bc38c524fd817ca98b7bf7`.
This accepts prepared source tests, not effective production IAM, credentials or runtime lifecycle.

No signed image, private ingress/provider/SQL-login acceptance, IAM/credential provisioning or
native TERM/resource rehearsal is performed. Existing Dockerfile still defaults to API: final
packaging must explicitly select the reference entry point. Compliance/scanner preparation and
same-origin routing remain pending. Tasks stays paused; Zynth later; cloud changes owner-run.
