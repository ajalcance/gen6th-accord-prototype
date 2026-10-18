# Application dependency review — October 13

Latest: PR67/68 are merged; exact-main push CI38336603073 succeeds. Owner authenticated API
reports `open_count: 0` and `alerts: []`. Dependency remediation is complete. Continue with
[application integration](application-integration-2026-10-13.md); older snapshots below are history.

Application dependency [PR #67](https://github.com/ajalcance/gen6th-accord/pull/67) is published,
head596a4341913261759f262a2a8e578e1ea8fe8dbb; exact-head CI38332273175 fails.
Frontend/docs and SAST pass. Hygiene modifies blank context lines in depth-backport.patch;
static reports984 guards passed/18 skipped/1 failure: vendor/braces/source/package.json
has no Dependabot entry. Local pre-commit guard tests missed this untracked manifest.
The hash-lock canary fails as intended and passes its gate; it is not the static failure.
Remaining skipped static checks are unproven. No rerun, merge or default-branch alert closure.
Owner approved the separate additive coverage PR on October13. Its7-file preview adds the
exact frozen package manifest plus one weekly entry with seven-day cooldown; existing entries
remain byte-for-byte equivalent. Five checkpoint tests include the original coverage guard
and missing-entry fault. Verify-only/lint/typing pass; actual committed guards remain owner-run.
No guard test, hook configuration or scanner exemption changes.
Patch hygiene repair is prepared in PR67's candidate: normalized patch hash54633452e16239fe127f90c12cfecf14939396d562b095f9a16ba753eea1bff4;
reverse/apply checks reproduce the exact five source files. Approved archive/source/provenance
and app locks are unchanged. Tests distinguish normalized patch from original provenance;
27 frontend/31 docs tests, formatting and DoD pass. Nine repair files are hash-bound separately.
Next: owner publishes coverage PR, applies guardrail-change after review, obtains exact-head
and post-merge CI. Then integrate accepted coverage into PR67 and publish the prepared hygiene
repair. Do not rerun the original application prepare/publish helpers or duplicate installs.
Coverage owner batch committed64d3ffa6a1a9d2ed21fe76d01ffaa5209df7c702 and passed guard
tests/policy, then stopped because make harness hardcodes backend/.venv/bin tools. Unchanged
harness now passes with the existing root tools via an exact temporary symlink, removed
afterward; seven committed hashes and clean checkout remain verified. Harness log SHA256
99b1c96ec4c516a557f9892690a690857e9a39becdabd861d6b76983d79f4c41.
Owner resume-owner.py binds that exact commit/evidence and performs only the remaining secret
scan, PR declaration/default meta-guard owner-label checkpoint, push and draft PR creation.
No clone, install, new commit or completed guard/policy/harness rerun. Never rerun publish-owner.py.
Owner published [PR68](https://github.com/ajalcance/gen6th-accord/pull/68) at that exact head
and applied guardrail-change. Label event [CI38334938763](https://github.com/ajalcance/gen6th-accord/actions/runs/38334938763)
passes hygiene/SAST/static/ci-complete; app/backend/Trust jobs are skipped, not acceptance.
Earlier unlabelled CI38334677609 is superseded. Owner ready/squash merge is next; verify the
new exact-main push CI before integrating coverage and the prepared patch repair into PR67.
Owner merged PR68 as4b078f3217e24b88b8cd313227d05d03704a1634; direct Actions API confirms
push CI38335333212 completed success at that exact SHA/treef28935ee77503cd478c3f3411584338137017e18.
The commit-workflow connector returned an empty list; that is superseded by the direct API.
Integration update-owner.py is prepared: exact nine repair hashes and five combined docs,
both documentation histories/common suffix preserved (PLAN399 lines), five fault tests,
verify-only/lint/typing pass. Owner batch verifies exact main CI and existing PR67, commits
repair, merges accepted main with only prepared documentation conflict resolutions, runs
unchanged full make check and Trust/DoD using a finally-removed temporary tool link, then
secret/default meta/declaration/source guards and one existing-PR update. No install, branch
replacement, force push, label, scanner acquisition/build or cloud action. New full gate is
required for the integrated commit; original prepare/publish helpers remain historical.
Owner integration succeeded at69957b955e1a2aca29ae0028d514c4fa14a1c4e9. Saved combined
make check/Trust/DoD logs pass, all five default meta checks and declarations pass, source/ten
contracts match, temporary tooling link removed and candidate clean. Exact PR CI38336138376
passes frontend/docs/hygiene/SAST/static/ci-complete; backend/Trust are skipped in that CI.
Owner merged PR67 asf466978594f9a01fd4491ba8ebb778a7c0db98a6. Exact main pushCI38336603073
passes the same applicable jobs. Application dependency remediation is merged and CI accepted.
Open-alert closure remains unverified: connector refuses the Dependabot endpoint. Next owner
read is paginated authenticated open-alert count/details; do not infer zero from branch audits.
This scaffold dependency unit does not integrate the accumulated737-file application source,
close native scanner input locks, provide signed measured Linux acceptance or deploy production.
All existing application changes and both Git checkouts are preserved.

## Verified base and boundaries

- Application: `security/codex-agent-boundary`, HEAD `407a9f4a67611770143198d1f42d605738b01530`.
- Review checkout: clean `codex/ci-jwt-remediation`, HEAD `0b619a9b06987b07f5908591f70c4a3ac9387855`.
- Connector confirms main `2c7d9722ac8da07bddb935ce5241503ae98b24db` and merged
  [PR #66](https://github.com/ajalcance/gen6th-accord/pull/66). Owner authenticated output
  binds successful push [CI 38326263023](https://github.com/ajalcance/gen6th-accord/actions/runs/38326263023)
  to that exact SHA; live job inspection confirms static/hygiene/SAST/ci-complete success.
  Application jobs were skipped, so that CI does not validate these application updates.
- The connector's two exact-main app locks equal the review checkout's committed app locks.
- Frozen source: 737 files, SHA256 `b9de452a5324bfc7f14b5d19a6938caf62e3c431ca5b49cd158a70351a90dd94`;
  all ten contract hashes match the [handoff](next-session-2026-10-12.md).
- No completed scanner helper was rerun. No branch, commit, label, PR, Actions or cloud mutation.

## Complete owner alert inventory

Latest authenticated attachment:
`<local attachment path withheld>`.
28 open: 6 critical, 8 high, 12 medium, 2 low. PyJWT does not appear in this open list;
individual closure reasons are unknown. Earlier 21-alert inventories are historical.

Each row pairs frontend/docs-site alert numbers. Scopes and ranges are owner API evidence.

| Alerts | Package | Scope | Severity | GHSA | Vulnerable range | First patched |
| --- | --- | --- | --- | --- | --- | --- |
| 57/47 | next | runtime | medium | GHSA-3w37-wq28-93x7 | >=16.3.0,<16.3.8 | 16.3.8 |
| 56/46 | next | runtime | medium | GHSA-4jqv-mc3x-m676 | >=16.0.0,<16.3.8 | 16.3.8 |
| 55/45 | next | runtime | low | GHSA-39w2-rjm5-chcv | >=16.0.0,<16.3.8 | 16.3.8 |
| 54/44 | next | runtime | medium | GHSA-f87g-xv8r-7p7x | >=16.0.0,<16.3.8 | 16.3.8 |
| 53/43 | next | runtime | medium | GHSA-mcj8-r9mp-w47p | >=16.0.0,<16.3.8 | 16.3.8 |
| 52/42 | next | runtime | high | GHSA-cjq9-62q9-8jv4 | >=16.0.0,<16.3.8 | 16.3.8 |
| 51/41 | sharp | runtime | high | GHSA-wq5f-xc86-pv6w | <0.35.5 | 0.35.5 |
| 50/40 | source-map-js | runtime | high | GHSA-68fv-2mgg-jv7q | >=1.0.0,<1.2.2 | 1.2.2 |
| 49/39 | tinypool | development | critical | GHSA-5gmw-xhrv-c9v3 | <=2.1.0 | 2.1.1 |
| 48/38 | tinypool | development | critical | GHSA-85c8-ppgw-ccpr | <2.1.2 | 2.1.2 |
| 37/36 | braces | development | high | GHSA-vfj7-8cjw-p6xm | <=3.0.3 | null |
| 22/21 | next | runtime | critical | GHSA-vcvr-r3jv-pc5j | >=16.2.0,<16.3.6 | 16.3.6 |
| 19/9 | vitest | development | medium | GHSA-82fw-gwwq-j7x9 | >=2.1.0,<4.1.11 | 4.1.11 |
| 18/8 | @vitest/mocker | development | medium | GHSA-82fw-gwwq-j7x9 | >=2.1.0,<4.1.11 | 4.1.11 |

Primary spot checks agree for [tinypool](https://github.com/advisories/GHSA-85c8-ppgw-ccpr),
[Next SSRF](https://github.com/advisories/GHSA-cjq9-62q9-8jv4) and
[braces](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm). No alert dismissal or suppression.

## Full lock and installed population

Both locks contain exactly one Next16.3.8, Sharp0.35.5, source-map-js1.2.2,
Vitest/@vitest/mocker4.1.11 and private braces3.0.4-accord.1 record.
Every package path, including nested node_modules paths, was inspected. Tinypool1.1.1 was
removed from both old locks; both new locks contain zero tinypool records and zero
dependencies/optionalDependencies/peerDependencies edges to tinypool. Vitest4 no longer
declares it. This is dependency removal evidence, not automatic alert closure.

Frontend has 544 package records: 56 changed/new and 10 removed. Docs-site has 559:
88 changed/new and 65 removed. Every changed/removed path is in the union of the old/new
Next, lint, Vitest and braces dependency closures; this does not prove every change is necessary.
Remaining records retain their complete JSON values. Docs-site detect-libc changes only
optional/devOptional classification; version, resolved URL and integrity are unchanged.

Docs-site Vite7.3.6 ->8.3.1 selects Rolldown/Lightning CSS and replaces esbuild/Rollup.
Vitest4.1.11 permits Vite6/7/8; frontend retains Vite7.3.6 via plugin-react.
The Vite8 change is avoidable scope, not a demonstrated vulnerability fix. Continue with the
existing tested, metadata-validated Vite8 tree; no additional resolution or lock change.
This routine scope choice preserves current artifacts while the owner prioritizes deployment.
The old docs-site Linux LZMA record was removed with the regenerated tree; the parser's
optional graph must be revalidated by clean Linux installation rather than Mac presence.

Installed version checks: frontend437 matches/107 absent; docs-site477 matches/82 absent;
zero version mismatches. Existing npm11.16.0 dependency-tree validation passes for both;
platform-specific optional packages remain uninstalled on Mac. This does not validate Linux.
Every new lock record retains integrity. Available cached archives verify against lock
integrities: frontend21 of56 changed records, docs-site29 of88. Remaining archive bytes
are unavailable locally; do not claim complete acquired-artifact verification.
Historical cached dates covered only11/56 and25/88 records. Owner public metadata now accepts
all142 changed registry records/87 packages: frontend55 and docs-site87, excluding the two
private local archive records. Dates precede October6 UTC; lock integrity/archive URLs match.
Saved result SHA256 `cecc1a9c352468f33d274afd6532586ad7fcd02ff339890ed1775f2e990c53c2`
is independently verified and binds the accepted offline report. Metadata is not acquired bytes.

All three private braces archives match approved SHA256
`2155cb703acd5f4247164321feb72df40214676b5cc7c362060f56e64e33bf7c`.
Preserve [ADR-0038](../decisions/0038-private-braces-depth-backport.md), patch/source/license
and consumer regressions. A private version alone cannot establish advisory remediation.

## Fresh offline checks and evidence limits

Existing approved Node22.23.1: frontend514 tests/65 files; docs-site31 tests/3 files, all pass.
Both suites include20 private braces regressions. ESLint passes for both, frontend TypeScript
passes. Both npm dependency trees validate. Scoped manifest/lock/braces-test Prettier checks
pass for both. DoD/production-marker/154 standards checks pass. Draft PR declaration syntax
contains all five records; the actual committed-diff declaration check remains pending.
These checks ran on the existing dirty application, not the future isolated PR candidate.
No new full make check, npm audit, build or package installation was performed.
Historical full-check-16 log SHA256 remains
`2be09457f2dc3f9848684c356da88e39ed417b831bbd1f138b79b21de313479f`;
retain its omitted numeric-exit limitation. It cannot substitute for final candidate evidence.

Scratch report: `.cache/production-bootstrap/app-dependency-review/offline-report.json`,
SHA256 `873e7303a6610e30925e8fc25d9f66b60f1fb8db3c21a45e0ea59a0442e13f1a`.
It records every delta/removed entry, ancestry, installed presence, cached integrity and dates.

## Completed owner checkpoint: public metadata only

Run in the owner's local Mac Terminal, outside Codex's sandbox. This queries only public npm
metadata, binds all four current app input hashes and checks every changed registry record's
exact version/date/integrity/archive URL against the October6 UTC seven-day cutoff.
It downloads no package archive and executes no package, install, build or Git command.
Six offline denial/acceptance tests and verify-only pass. Existing successful result refuses
a rerun; inspect it. Report full output, METADATA_OK/RESULT_SHA256 or the first full failure.
Owner execution succeeded; do not rerun. The original command below is historical.

```bash
cd "/path/to/gen6th-accord" &&
printf '%s\n' '0564d3117f4b8a0bd71857fc8c2db683f29dd165bf2ddf85a7d7936140f6a7ee  .cache/production-bootstrap/app-dependency-review/check-metadata-owner.py' | shasum -a 256 -c - &&
python3 .cache/production-bootstrap/app-dependency-review/check-metadata-owner.py --check
```

## Before any paid CI event

Prepared Git-free preview `.cache/production-bootstrap/app-dependency-review/preview` contains
28 focused changed files against the review tree (equal to accepted main before these edits).
It excludes the frontend governance-integration script and unrelated source/guard changes.
The existing approved braces decision is preserved as a runbook, retaining application ADR0038
and avoiding a gap/renumbering in the focused scaffold history. No new design decision is made.
Payload SHA256 `6f6655c555a9bf382ff01946ba847cb47351288c6302fa1365dde39c48ac23c6`.
Preview tests use existing app node_modules:27 frontend and31 docs-site tests pass;
lint/types/full app formatting and DoD pass. This is source preview acceptance, not clean install.

Completed owner batch, outside Codex's sandbox: `prepare-and-check-owner.py --prepare` created a
fresh local checkout from exact accepted main, preserves both existing checkouts, installs both
reviewed npm locks, then runs unchanged make check plus Trust/DoD. Node22.23.1/npm11.16.0
and existing approved backend/tool binaries are reused; no backend environment installation.
External test DB override is cleared, so SQL tests use disposable Docker PostgreSQL.
It verifies28 output hashes/population and unchanged application source/contracts afterward.
Six offline binding faults, verify-only, Ruff and strict mypy pass. No commit, push, PR, label,
Actions or cloud mutation; no scanner native build. Existing destination/logs refuse a rerun.
Owner output records both installs, make check and make trust dod-check exiting0. The final
population check found the helper's temporary backend/.venv symlink as a29th file. Only that
exact symlink was removed; its root target is preserved. All28 candidate hashes match; diff
whitespace/source-after checks now pass. No completed install or test batch was rerun.
Logs record985 guards passed/18 skipped,52 scaffold backend tests with82.81% coverage,
27 frontend/31 docs-site tests, both builds and zero npm audit vulnerabilities. Trust passes;
Go reports zero called vulnerabilities with additional uncalled dependency findings.
The original command below is historical: do not rerun it.

```bash
cd "/path/to/gen6th-accord" &&
printf '%s\n' 'daed0aefbfe9e435abc3865f0018def2add206ff0b7e4fa8befa41f70129a420  .cache/production-bootstrap/app-dependency-review/prepare-and-check-owner.py' | shasum -a 256 -c - &&
python3 .cache/production-bootstrap/app-dependency-review/prepare-and-check-owner.py --prepare
```

The existing owner-created candidate preserves both previous checkouts. It includes only
dependency manifest/lock changes, private braces source,
patch/provenance/archives/regressions, the frontend Docker archive COPY and required records.
Exclude the unrelated frontend governance-integration script, persona UI/backend/cloud code,
scanner CI lock and guard/workflow/settings changes. Do not import root wholesale.
Resolve approved decision placement without creating an ADR numbering gap or overwriting
root0021/0038; scanner0021->0072 and release0022->0073 still need final integration.
Before publication: complete release/integrity checks, unchanged audits, clean candidate tests,
full applicable gate and DoD, default meta-guard, secret scan and actual committed-diff PR
declaration. The draft PR body is preparatory only; committed-diff acceptance is not claimed.
Owner Git mutations/publication/labels/merge remain checkpoints. No gratuitous PR edit/rerun.
Production native packaging/acquisition/measurement remains incomplete; Tasks paused, one
production environment, Zynth later, application tables via Alembic, signed digest-bound release.

Next owner checkpoint: scratch `publish-owner.py --publish` reuses completed gates, binds
accepted logs/payload/body, verifies exact base/branch, commits only28 files, then runs the
unchanged secret scan, default meta-guard and actual committed-diff declaration before push
and draft PR creation. No install, test rerun, label, merge, scanner build or cloud mutation.
Six checkpoint fault tests pass; verify-only/lint/typing pass. A failure preserves the candidate;
never rerun after a commit. Report NEW_HEAD/NEW_PR or the first full error for a bounded resume.
