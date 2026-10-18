# Braces patch evaluation — 2026-10-03

Owner approved dependency-remediation preparation for **frontend and docs-site** after the
corrected SQL run. This review continues within the existing **18:31:56–20:31:56 Manila**
window; it does not extend that window. No install or active dependency change is selected.
The [audit checkpoint](braces-audit-review.md) retains the owner gate evidence.

## Independently checked experiment

Both installed braces trees have byte-identical source, manifest and MIT license. A scratch
copy of published **braces 3.0.3** retains its original name/version, dependency manifest,
entry point, utilities and license. Five `lib/` files receive a depth-limit backport inspired
by [upstream PR 72](https://github.com/micromatch/braces/pull/72), commit
`d0d575e55e74a4e0218e5248fafb79efc3e54ebb`:

- Parser counts braces and parentheses together and refuses nesting beyond 100.
- Compile, expand and stringify cap direct AST recursion, so callers cannot skip the parser.
- Configured limits cannot raise the cap; finite fractional limits round down consistently,
  negative limits become zero, and non-finite values retain the safe default.
- Stringify forwards depth while preserving the published empty-parent behavior. The
  upstream change to parent propagation is independently reproduced as an `escapeInvalid`
  regression, including `{{a}}` and `{1..8}`.

The unchanged installed **Node 22.23.1** runs the experiment against each project's dependency
tree: **9 tests pass per project**, zero failures/skips. Each run executes **10,632 behavior
comparisons and 243 explicit depth-rejection assertions**. Covered: shallow/malformed/quoted/
escaped patterns, range limits, 100/101 boundaries, deep strings below the existing length
limit, direct ASTs up to 10,000 levels, stricter/non-finite limits, and the actual installed
micromatch/fast-glob/Next root-directory resolver. Published direct-AST stack exhaustion is
reproduced for compile, expand and stringify; the candidate rejects before stack exhaustion.

These are bounded experiment results, not the full released Mocha suite, application-wide
compatibility, a production installation, or an npm-audit pass. Expansion cardinality, AST
width and malformed parent cycles are outside this depth-only review. Test-only dependency
injection occurs in the experiment process; no installed package file is changed.

## Local review artifacts

Ignored scratch artifacts are present in `.cache/braces-depth-review/`; they are not included
in a fresh clone. Do not apply the patch to `node_modules` as a substitute for a reviewed lock.

| Artifact | SHA-256 |
| --- | --- |
| `depth-backport.patch` | `a3f08706e45f1e180112f91f07a871b284b92613bccdfb2724a165ff4f96c91e` |
| `review.cjs` | `ceec9098c9628e46d355c747681f27df87a1c771d4087c47588afc0104301f2e` |

`frontend-node22.txt` and `docs-site-node22.txt` retain the passing output and individual
candidate-file fingerprints. Re-run locally without installing anything:

```bash
BRACES_REVIEW_PROJECT=frontend NODE_PATH="$PWD/frontend/node_modules" /opt/homebrew/opt/node@22/bin/node --test .cache/braces-depth-review/review.cjs
BRACES_REVIEW_PROJECT=docs-site NODE_PATH="$PWD/docs-site/node_modules" /opt/homebrew/opt/node@22/bin/node --test .cache/braces-depth-review/review.cjs
```

## Remaining source and installation gates

The [reviewed advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) still lists **no
patched release**. Retaining 3.0.3 metadata leaves the audit finding unresolved. No invented
release, rename, exemption, forced lint downgrade or changed scanner configuration is used.

The public fork advertises `v3.0.4-pillarsdotnet.1`. Its
[stringify correction](https://github.com/pillarsdotnet/braces/commit/31d783e7631f145a49f60e9fd059c3a583e60266)
is visible. Initially the full source could not be retrieved through shell DNS or the browser
source service. **Owner source acquisition is now complete**: the tag resolves to
82d539e412aa2f6034dabdf3d51f5ee36036cfe7, all supplied hashes match, MIT is retained and no
installation lifecycle script is declared. It passes 7/9 review groups; additional parser changes
and inconsistent fractional limits remain. It is not selected. See the [installation proposal](braces-installation-proposal.md)
for the tested private artifact and complete released-case results.

Owner subsequently approved the exact private artifact, installation and temporary maintenance
(ADR-0038). Both manifests/locks now pin it; docs-site installation/31 tests/static/build pass.
Owner subsequently restores both locked trees and reports full validation exit 0 with 14 ASGI
tests and matching input hashes; agent verifies both installed chains and 20 regressions per app.
The installation checkpoint records this local proof and reproducible commands. No more source fetch
is needed; every existing audit and lint rule remains required.

Historical source-only fetch, **already completed by the owner**. It uses the
public repository, writes only a new ignored cache directory, and executes no package script.
The first precondition refuses an existing destination; do not overwrite prior review evidence.

```bash
cd "/path/to/gen6th-accord" &&
test ! -e .cache/braces-fork-review &&
git clone --single-branch --branch v3.0.4-pillarsdotnet.1 https://github.com/pillarsdotnet/braces.git .cache/braces-fork-review &&
git -C .cache/braces-fork-review rev-parse HEAD &&
git -C .cache/braces-fork-review merge-base --is-ancestor 31d783e7631f145a49f60e9fd059c3a583e60266 HEAD &&
git -C .cache/braces-fork-review status --short &&
cat .cache/braces-fork-review/package.json .cache/braces-fork-review/LICENSE &&
shasum -a 256 .cache/braces-fork-review/package.json .cache/braces-fork-review/LICENSE .cache/braces-fork-review/index.js .cache/braces-fork-review/lib/*.js
```

No app manifests, locks, installed dependencies, lint/audit configuration, Git metadata or
activation settings were changed by this evaluation. Backend/frontend fingerprints remain
the corrected-owner values at this historical evaluation. The subsequent adoption changes the
frontend fingerprint, documented in the installation checkpoint. The owner's subsequent full
local gate completes successfully; this evaluation's earlier incomplete run remains historical.

Fresh agent `make check`: **776 guards pass / 18 skips**, policy, harness and backend static/
typing/Bandit checks pass; pip-audit stops at **Failed to upgrade pip** before SQL or npm gates.
This is separate from the owner's SQL/Trust proof. `make dod-check` and `git diff --check` pass.
