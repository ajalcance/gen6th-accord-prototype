# Dependabot owner evidence and bounded remediation preparation

2026-10-13 current: PR #66 merged2c7d9722ac8da07bddb935ce5241503ae98b24db; exact-main pushCI38326263023 succeeds, app jobs skipped. Current owner inventory28 app alerts (6 critical/8 high/12 medium/2 low); no PyJWT entries, closure reasons unknown. [Full application review](application-dependency-review-2026-10-13.md) binds both states/source/contracts, all lock paths/edges and private braces;514/31 Node22 tests/lint/types pass. Metadata142 records/87 packages accepted, resultcecc1a9c352468f33d274afd6532586ad7fcd02ff339890ed1775f2e990c53c2 verified. Retain tested Vite8. Focused28-file preview passes27/31 tests/lint/types/format/DoD; owner clean clone/install/full-check batch is prepared, no publication yet; no agent install/build/Git/CI/cloud action. Preserve all prior snapshots below as history; completed helpers must not rerun.

Latest October13 local commit prepared: codex/ci-jwt-remediation at
0b619a9b06987b07f5908591f70c4a3ac9387855; review checkout clean, seven-file scope confirmed.
Owner46/46 secret canary succeeds and no commit secrets; all5 PR declarations pass independently.
Default meta-guard runs all5 checks, blocks only two guarded requirement files pending owner label.
Prepared body hash541281c811795bdc04dc360f58a2a903fd51bd97f5c24206e341376128077448 unchanged.
Owner publication is next and triggers paid PR CI. No completed helper rerun; no agent publication.

Latest October13 acceptance: bound CLI/core both1.179.0; full saved scanner logs confirm all16
rule faults (17 findings/no errors) and review scan121 targets/0 findings. Ten actual PyJWT
regressions passed. Canonical requirements-ci.in provenance was regenerated entirely offline
from acquired metadata: lock SHA256e6a498e660ea05e4b9e760291671aec89eccf2fed514cc246deb11dc163a3864;
all package/marker/hash blocks match the owner-tested candidate exactly. Only generated input
annotations/header differ. Seven review files now contain the separate repair and required docs.
Local985 guards pass/18 skipped; policy, exact-pin reconciliation and harness lint/format pass.
make harness itself lacks an isolated virtualenv; identical commands pass via existing root tools.
No full application make check claim. Prepared PR body contains every Memory impact declaration;
owner prepare-pr-owner.py --prepare fetches/checks exact accepted main and equal base trees,
creates codex/ci-jwt-remediation, commits only seven hash-bound files, scans secrets/canary and
validates declarations against the actual commit. Default meta-guard must fail solely for the
two guarded requirement files; owner label remains mandatory, never self-waived. Four offline
preparation fault tests/lint/typing pass. No push/PR creation or Actions in this checkpoint.

Latest October13 bound-version checkpoint: saved CLI output is1.179.0, core output is
semgrep-core version:1.179.0 (8fa217f125), both owner-reported exit0. Prior mismatch was external
launcher lookup. The new checkpoint stopped because its plain-version parser rejected the
core's labeled format; this is a checkpoint defect, not a scanner version failure. Parser now
requires exact CLI version or exact labeled core version with hexadecimal commit. Wrong versions,
suffixes/malformed output remain denied. Resume verifies saved logs by SHA256 and does not repeat
completed commands; only remaining bound faults/review scan execute. Fifteen offline parser/binding/
resume fault tests, lint/format and strict typing pass. Actual bound scan acceptance remains pending.

Latest October13 evidence: complete owner logs confirm66 hash-constrained wheels installed,
ten PyJWT2.15 regressions pass, 17 scanner findings cover16 rules with no parsing errors, and
review scan finds0 issues across121 targets. However semgrep-version.log reports1.176.0 while
installed metadata/module report1.179.0. Original PACKAGE_CHECK_OK is insufficient acceptance:
the helper checked exit status, not version equality. No PR preparation/publication may use it.
Read-only launcher inspection shows environment scripts appended to PATH and an existing
/opt/homebrew/bin/pysemgrep preceding the installed environment; this suggests an external
Python CLI fallback, not yet confirmed by a corrected native run. Preserve all original logs.
New check-bound-scanner-owner.py prepends only the installed environment's bin directory and
requires CLI and bundled core both1.179.0 before scanner faults/review scan. No reinstall,
download, original checkpoint rerun or CI event. Six offline binding/version fault tests,
verify-only/lint/format/strict typing pass; owner bound-scanner execution remains pending.

October13 continuation: owner candidate resolution succeeded; saved lock SHA256
2f085539f5492eaef6402c1accd6dd9b81bef1d28952299298bf6356daaf115a independently verified.
Saved complete resolver log reports80 packages in2.39s. All78 unrelated versions/markers/hashes
are unchanged. The candidate contains Semgrep1.179.0/PyJWT2.15.0; no tracked lock replacement yet.
Never rerun the completed resolver. The new check-packages-owner.py checkpoint has four passing
offline fault tests, verify-only/lint/typing/format checks. Owner --check creates a new scratch
environment using existing Python3.12, installs only hash-constrained binary distributions from
public PyPI, then runs ten PyJWT regressions, 16-rule scanner fault coverage and the unchanged
local ruleset on the clean review checkout. Deep JSON test uses valid JWT framing and requires
RecursionError as the DecodeError cause, preventing denial for the wrong reason. Fault source
files are inspected, never executed. Existing environment/fault files block accidental reruns;
logs are preserved. No acquired-package/native test has been executed by the agent. No CI event,
publication, live application test or cloud mutation. Linux CI and final review remain required.

2026-10-12, Asia/Manila. Owner approved the separate CI-lock remediation preparation. Candidate
inputs/checkpoint only; no tracked dependency edit, acquisition, install, CI trigger, alert
dismissal, release or cloud mutation. Production readiness remains incomplete.

## Evidence and checkout reconciliation

Owner ran authenticated gh api --paginate against open repository Dependabot alerts and supplied
21 projected records: 3 critical, 7 high, 11 medium (GitHub notice calls medium moderate).
The projection includes alert number, package, manifest, severity, GHSA and first patched version;
it does not include full vulnerable ranges, dependency scope, publication dates or exploitability.
This closes the missing owner package/advisory evidence, not any vulnerability.

GitHub file reads at merged main 759dde9b716beefd88440aa7c85373c3d3ee53f0 independently confirm
both app locks use Next16.3.5, Vitest/@vitest/mocker3.2.7 and braces3.0.3. The scanner lock uses
PyJWT2.13.0 via mcp/semgrep. PR #61 changed none of these manifests.

The dirty application checkout remains security/codex-agent-boundary at 407a9f4a67611770143198d1f42d605738b01530:
both locks already use Next16.3.8, Vitest/@vitest/mocker4.1.11 and private braces3.0.4-accord.1.
Those changes are not on main. Preserve them; do not redo or replace them with a broad upgrade.
PyJWT remains2.13.0 in the application scanner lock too. All three braces tarballs match the
approved ADR-0038 SHA2562155cb703acd5f4247164321feb72df40214676b5cc7c362060f56e64e33bf7c.
That establishes artifact identity, not current full acceptance or automated alert closure.

## All 21 owner-reported alerts

| Alerts | Package / manifest | Severity | GHSA | Owner API first patched |
| --- | --- | --- | --- | --- |
| 37,36 | braces / frontend,docs-site locks | high | GHSA-vfj7-8cjw-p6xm | null |
| 35 | PyJWT / requirements-ci.txt | medium | GHSA-gvp8-978c-rx2q | null |
| 34 | PyJWT / requirements-ci.txt | medium | GHSA-42vr-xj54-vc7v | 2.15.0 |
| 33 | PyJWT / requirements-ci.txt | medium | GHSA-jwrc-g2q2-pq5p | 2.14.0 |
| 32 | PyJWT / requirements-ci.txt | high | GHSA-9j54-fg26-wv3r | 2.14.0 |
| 31 | PyJWT / requirements-ci.txt | medium | GHSA-8wjv-2p76-3863 | 2.14.0 |
| 30 | PyJWT / requirements-ci.txt | medium | GHSA-hxm8-2xgr-2p9m | 2.14.0 |
| 29 | PyJWT / requirements-ci.txt | critical | GHSA-ffc3-869f-jxw9 | 2.14.0 |
| 28 | PyJWT / requirements-ci.txt | high | GHSA-w2cx-738m-mc7w | 2.14.0 |
| 27 | PyJWT / requirements-ci.txt | high | GHSA-9v7f-9g4p-ffgj | 2.14.0 |
| 26 | PyJWT / requirements-ci.txt | high | GHSA-p4g4-x82p-q773 | 2.14.0 |
| 25 | PyJWT / requirements-ci.txt | high | GHSA-r6x4-923q-g947 | 2.14.0 |
| 24 | PyJWT / requirements-ci.txt | medium | GHSA-2gx3-rcp4-g85q | 2.14.0 |
| 23 | PyJWT / requirements-ci.txt | medium | GHSA-w6j9-cwv2-h6wq | 2.14.0 |
| 22,21 | next / frontend,docs-site locks | critical | GHSA-vcvr-r3jv-pc5j | 16.3.6 |
| 19,9 | vitest / frontend,docs-site locks | medium | GHSA-82fw-gwwq-j7x9 | 4.1.11 |
| 18,8 | @vitest/mocker / frontend,docs-site locks | medium | GHSA-82fw-gwwq-j7x9 | 4.1.11 |

Package spelling/case is normalized here; original PyJWT spelling varied. Grouped IDs retain all
21 records. No alert is dismissed or reclassified. Null does not mean no action or safe.

## Primary advisory checks

[Next advisory](https://github.com/advisories/GHSA-vcvr-r3jv-pc5j) lists 16.3.6 as patched;
[Vitest advisory](https://github.com/advisories/GHSA-82fw-gwwq-j7x9) lists4.1.11. Prepared app
versions are beyond those floors; integration/unchanged audits/normal review remain required.
[Braces advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) lists no official patched
release. Reuse the separately reviewed depth backport and regression evidence in ADR-0038.
Its private version must not be treated as proof by version comparison alone.

[Critical PyJWT advisory](https://github.com/advisories/GHSA-ffc3-869f-jxw9) lists2.14.0;
[pre-verification parser advisory](https://github.com/advisories/GHSA-42vr-xj54-vc7v) lists2.15.0.
[Options-dict advisory](https://github.com/advisories/GHSA-gvp8-978c-rx2q) lists affected2.11–2.13
and no patched version. [PyJWT2.15 source](https://github.com/jpadilla/pyjwt/blob/2.15.0/jwt/api_jwt.py)
defensively copies options before mutation; [upstream regression tests](https://github.com/jpadilla/pyjwt/blob/2.15.0/tests/test_api_jwt.py)
cover reused options and claim verification. This is source inspection, not execution against
an acquired wheel or permission to close35. Local package regression remains required.
Remaining PyJWT patched values above are owner API evidence, not independent code verification.

## Approved bounded review unit — candidate resolution pending

Owner approved on October12. Semgrep1.177.0 and1.178.0 require PyJWT~=2.13.0, which excludes
the2.15.0 target. [Semgrep1.179 changelog](https://github.com/semgrep/semgrep/blob/v1.179.0/CHANGELOG.md)
explicitly relaxes that constraint to >=2.15.0,<3. Its [PyPI release](https://pypi.org/project/semgrep/1.179.0/)
was uploaded October2; [PyJWT2.15.0](https://pypi.org/project/PyJWT/2.15.0/) September23. Both exceed
seven days as of this preparation. MCP1.29.0 permits this target. No dependency override is used.

Scratch candidate pins Semgrep1.179.0 and PyJWT2.15.0 explicitly; 78 other packages remain frozen
through normal constraints. The existing universal Python3.12/generated-hash resolver must
produce the lock; a local checker rejects unrelated versions, markers, hashes or population
changes. The approved unit does not change scanner rules, CI commands, hash canary or thresholds.
Review checkout remains clean at571dbf72349742ec506332f0efe837f313bdf216; frozen737-file application
source and ten contracts reverified unchanged. Fetch current main and verify tree equality before
the later owner creates the separate branch; no branch mutation is part of resolution.

The offline resolver cannot complete because metadata is not cached. A new owner-only scratch
checkpoint, `.cache/production-bootstrap/pyjwt-lock-review/resolve-owner.py --resolve`, resolves
from public PyPI with keyring/config discovery disabled, no source build or Python download,
and the October5 cutoff. It writes only scratch output/logs, rejects existing output on rerun,
and does not install, edit tracked dependencies, commit, push, create a PR or start CI.
Owner's first resolution exited2: uv split the absolute constraints path at the space in
Software Applications. Original error is preserved in scratch resolve-first-path-error.log.
The helper now runs within the scratch directory using relative input/constraints/cache/output
paths. A real uv invocation in a directory containing spaces reaches the expected uncached
package failure with network disabled, proving the input files are read. Twelve checkpoint
tests, verify-only, lint/format and strict typing pass. Candidate
lock generation, hash-verified package regressions, Semgrep compatibility and final PR metadata
checks remain pending. No claim that the dependency repair or full make check has passed yet.

Prepare a separate scanner-lock remediation PR from current merged main, preserving every
existing hash/provenance/canary and unrelated pin. Review upstream PyJWT2.15.0 source, metadata,
release age and mcp/semgrep constraints; resolve the null-patched advisory with source and fault
evidence. Regenerate the hashed lock through the existing reviewed mechanism, not guessed hashes
or manual transitive edits. Acquisition/install commands remain explicit owner checkpoints.
The requirements-ci files define guards; owner approval covers this separate remediation unit.

Before publication validate the exact final PR description against the committed diff, default
meta-guard output, all applicable local checks and expected owner labels. Batch corrections before
the first paid CI event. Do not edit an open PR merely to discover missing metadata in CI.
Do not weaken audits, install with force, add suppressions or dismiss alerts to obtain green.

Integrate the already prepared app dependency fixes through their reviewed application history;
never copy the entire dirty application into the scanner-lock PR. Final ADR collision mapping
and genuine locked scanner packaging/native measured sizing remain ordered preparation work.
One production environment, Zynth later, Tasks paused; application tables use Alembic.
