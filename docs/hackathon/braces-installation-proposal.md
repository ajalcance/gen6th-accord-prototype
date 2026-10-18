# Braces installation checkpoint — 2026-10-03

**Owner approved the exact artifact's adoption, installation in both apps and temporary
maintenance.** ADR-0038 records the decision, within the existing 18:31:56–20:31:56 Manila
window. Source acquisition is complete. Owner validation now completes with exit status **0**.

## Current result

Both manifests and npm-generated locks pin the approved artifact. Only the root
development-dependency record and braces package record change; every other package entry
matches its saved pre-install lock. Next/React, lint configs and audit commands are unchanged.
Docs-site's installed tree is valid under both existing npm 10 and npm 11.

**Owner closeout:** the supplied run reaches the conditional ASGI bridge, passes **14 tests /
2 files** in **17.31s**, prints all three expected trailing fingerprints and ends with
**validation_exit_status=0**. The unchanged reviewed command reaches that bridge only after
both frozen installs, dependency-tree checks and full `make check` succeed. This is an
owner-reported complete local gate, not an agent-run full gate or revision-bound CI result.
The supplied excerpt begins at docs-site build; preceding detailed gate output is not included.
Agent independently rehashes all three input sets, verifies both installed braces chains and
reruns **20 installed-package regressions per app**, all passing. Dependency restoration is
resolved. The prior sandbox failures below are historical; PR/security/rendered review remains.

- Docs-site: **20 new regressions; 31 total tests pass**, plus lint, formatting, standalone
  TypeScript and production build. A type check that raced generated files was repeated
  successfully after build.
- Historical frontend failure: the frozen reinstall cleared `frontend/node_modules`. The offline
  cache lacks xmlchars 2.2.0; bundled npm subsequently crashed; the existing npm 11 retry
  failed at **ENOTFOUND registry.npmjs.org**. The owner's successful run has restored both trees.
- Earlier agent live docs-site audit failed at registry DNS. Offline npm's “found 0 vulnerabilities”
  is not a live audit pass.
- Historical agent full gate: **776 guards pass / 18 skip**, policy/documentation/harness and backend
  Ruff/Black/mypy/Bandit pass, then `make check` stops at pip-audit's **Failed to upgrade pip**
  bootstrap, before SQL/Trust/app gates. Owner's earlier **553 SQL tests / 96.96%** and
  Trust pass are separate evidence.

## Exact adopted artifact and packaging

Private **braces@3.0.4-accord.1** backports five depth guards onto published 3.0.3 source at
**74b2db2938fad48a2ea54a9c8bf27a37a62c350d**. It is not an official release. Published
parser/stringify behavior is preserved; brace/parenthesis and direct-AST depth cap at 100
and stricter limits normalize consistently. Original entry point, utilities and MIT license
are unchanged. The manifest pins existing fill-range **7.1.1** and declares **no scripts**.

`vendor/braces/` contains the frozen archive, readable exact source, patch and maintenance
record. Identical archives live inside each app's `vendor/braces/` build context.
Frontend Docker copies its archive before `npm ci`; the build context is unchanged.
No CI/release workflow, gate, scanner, lint rule or threshold was edited.

| Identity | Value |
| --- | --- |
| Archive SHA-256 | `2155cb703acd5f4247164321feb72df40214676b5cc7c362060f56e64e33bf7c` |
| npm SHA-512 integrity | `sha512-mq+bKmdbUUTDiQZqhfUAA4DnYOW5iAhcXBq7VtQ8SD4rvfSsvL5gEwWMJ4o8YNSWNlRW6toXlKNhFDHaBP0Oaw==` |
| Source patch SHA-256 | `a3f08706e45f1e180112f91f07a871b284b92613bccdfb2724a165ff4f96c91e` |

The tar is **7,185 bytes / 10 regular files**, byte-identical to the reviewed source.
Each app directly pins `braces` as a devDependency to
`file:vendor/braces/braces-3.0.4-accord.1.tgz`, with a scoped
`micromatch@4.0.8 -> braces -> 3.0.4-accord.1` override deduplicating to that local package.
A bare tarball override resolves relative to micromatch during fetch. The root dependency
avoids that mismatch. The existing npm **11.16.0** resolver generated the locks; npm 10's
unrelated platform metadata drift was rejected. Cached previews are historical.

Both normal `tests/braces-depth.test.ts` suites assert archive/source/lock/manifest identity,
100/101 boundaries, deep strings/direct ASTs, fractional/negative/non-finite settings,
published behavior and real installed micromatch/fast-glob/Next root resolution.
No in-memory injection is used in these permanent tests. Both installed suites pass **20 tests**.

## Source review and preliminary proof

The fetched fork tag resolves to **82d539e412aa2f6034dabdf3d51f5ee36036cfe7**; all nine
supplied hashes match and its tree is clean. Its default 100 cap holds, but only **7/9 groups**
pass: `invalid: false` changes the published AST shape, and `maxDepth: 0.5` accepts a parser
level which its walker refuses. Unrelated quote changes are included. This is not a bypass
above 100. The fork was not selected; direct tinyglobby substitution also changed root matches.

The adopted source passes **764 unchanged released cases** for baseline, isolated backport
and private package through Node **22.23.1**'s synchronous Mocha-global adapter, not actual
Mocha. All 12 released fixture files execute, no tests fail/skip, one additional provenance
test passes and no shell fixture helper runs. The isolated private package passes **9 groups
per app**, **10,632 behavior comparisons and 243 depth assertions each**, using test-only
in-memory consumer injection. These preliminary proofs are separate from installed tests.
AST width, expansion cardinality and malformed parent cycles are outside this depth-only fix.
Cache runners/results live in `.cache/braces-depth-review/`; prior evidence is in the
[audit checkpoint](braces-audit-review.md) and [patch evaluation](braces-patch-evaluation.md).

## Maintenance and audit duty

Owner accepted temporary maintenance. Review future advisories against the recorded 3.0.3
base; version-based audit may classify the derivative differently. Retire it when a verified
official release passes the same regressions, consumer checks and unchanged audit.
A new version number or these tests does not replace live audit proof. No exemption,
suppression or forced lint downgrade is applied.

## Completed owner restoration and validation command

Use **Mac Terminal**, Docker running, installed Python 3.12/Node 22 and existing npm 11.16.0.
No new resolver install or approval is needed. This block checks branch/source/artifact,
restores both frozen trees, prints their braces chains and runs the unchanged full gate
plus conditional ASGI bridge. It does not mount routes, migrate persistent owner data,
activate providers, deploy or publish.

- Backend: `375e3d8a776d68b7d77ef01477ef46eef4ada0335bffdfc1179bc89f35e1c5b2` (159 inputs).
- Frontend: `63ad1f1c0fda96c5da7a37340b4db489bb9472ac77b5025dfd0a97e04792cf7a` (131 inputs).
- Remediation: `31ff34da5e3cf44786fa2b209ab7c86fce52cf22458c64a03df34cc1250acbdc` (24 inputs);
  includes vendor sources, all archive copies, both manifests/locks/tests and frontend Dockerfile.

The same complete block is saved as `.cache/braces-owner-validation.sh`; Bash syntax and
ShellCheck pass. Its reviewed SHA-256 is
`e4d542d1f8512bc435211772f3c994debdcba729fe4f852d238d88b408931fcf`.
Run this short wrapper, or the expanded equivalent below:

```bash
cd "/path/to/gen6th-accord" &&
printf '%s  %s\n' 'e4d542d1f8512bc435211772f3c994debdcba729fe4f852d238d88b408931fcf' '.cache/braces-owner-validation.sh' | shasum -a 256 -c - &&
bash .cache/braces-owner-validation.sh
```

```bash
cd "/path/to/gen6th-accord" &&
test "$(git branch --show-current)" = "security/codex-agent-boundary" &&
test "$(/opt/homebrew/opt/node@22/bin/node .cache/npm-resolver/node_modules/npm/bin/npm-cli.js --version)" = "11.16.0" &&
test "$(backend/.venv/bin/python .cache/workflow-source-evidence.py)" = "backend_source_sha256=375e3d8a776d68b7d77ef01477ef46eef4ada0335bffdfc1179bc89f35e1c5b2 files=159" &&
test "$(backend/.venv/bin/python .cache/frontend-source-evidence.py)" = "frontend_source_sha256=63ad1f1c0fda96c5da7a37340b4db489bb9472ac77b5025dfd0a97e04792cf7a files=131" &&
test "$(backend/.venv/bin/python .cache/braces-remediation-evidence.py)" = "braces_remediation_sha256=31ff34da5e3cf44786fa2b209ab7c86fce52cf22458c64a03df34cc1250acbdc files=24" &&
(
  export PATH="$PWD/backend/.venv/bin:$PWD/.tools/bin:/opt/homebrew/opt/node@22/bin:$PATH"
  task_check_status=0
  backend/.venv/bin/python .cache/workflow-source-evidence.py
  backend/.venv/bin/python .cache/frontend-source-evidence.py
  backend/.venv/bin/python .cache/braces-remediation-evidence.py
  node .cache/npm-resolver/node_modules/npm/bin/npm-cli.js ci --prefix frontend --cache .cache/npm || task_check_status=$?
  if [ "$task_check_status" -eq 0 ]; then
    node .cache/npm-resolver/node_modules/npm/bin/npm-cli.js ci --prefix docs-site --cache .cache/npm || task_check_status=$?
  fi
  if [ "$task_check_status" -eq 0 ]; then
    node .cache/npm-resolver/node_modules/npm/bin/npm-cli.js ls braces --all --prefix frontend --cache .cache/npm || task_check_status=$?
  fi
  if [ "$task_check_status" -eq 0 ]; then
    node .cache/npm-resolver/node_modules/npm/bin/npm-cli.js ls braces --all --prefix docs-site --cache .cache/npm || task_check_status=$?
  fi
  if [ "$task_check_status" -eq 0 ]; then
    LC_ALL=en_US.UTF-8 make check || task_check_status=$?
  fi
  if [ "$task_check_status" -eq 0 ]; then
    (cd frontend && npm run test:governance-integration) || task_check_status=$?
  fi
  backend/.venv/bin/python .cache/workflow-source-evidence.py
  backend/.venv/bin/python .cache/frontend-source-evidence.py
  backend/.venv/bin/python .cache/braces-remediation-evidence.py || task_check_status=$?
  test "$(backend/.venv/bin/python .cache/frontend-source-evidence.py)" = "frontend_source_sha256=63ad1f1c0fda96c5da7a37340b4db489bb9472ac77b5025dfd0a97e04792cf7a files=131" || task_check_status=1
  test "$(backend/.venv/bin/python .cache/braces-remediation-evidence.py)" = "braces_remediation_sha256=31ff34da5e3cf44786fa2b209ab7c86fce52cf22458c64a03df34cc1250acbdc files=24" || task_check_status=1
  printf 'validation_exit_status=%s\n' "$task_check_status"
  exit "$task_check_status"
)
```

This command completed successfully in the supplied owner run; no repeat is required without
new source changes or an unresolved failure. Its reproducible expected result is:
both trees contain only **braces@3.0.4-accord.1**, unchanged gates and bridge pass, hashes match
and exit status is **0**. A failed precondition stops before installation.
PR/CI, security/ADR review and rendered acceptance remain required.
