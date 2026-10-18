# Braces dependency audit — read-only review, 2026-10-03

## Owner audit checkpoint before remediation

Owner supplied the corrected-source run: **553 backend tests pass in 80.55s**, **96.96%
application coverage**; Trust module verification, vet, lint, vulnerability scan and race tests
pass. Frontend lint, formatting and TypeScript pass, then the unchanged high-severity audit
gate refuses five affected dependency entries. `validation_exit_status=2`; the frontend's
later tests/build/budget, docs-site gate and conditional ASGI command were not reached.

Supplied trailing fingerprints matched independently rehashed source at this checkpoint:
- Backend: `375e3d8a776d68b7d77ef01477ef46eef4ada0335bffdfc1179bc89f35e1c5b2` (159 inputs).
- Frontend: `f1d7598b8971ccbba183707e30d717af2db3a85c8698aff67841080bab25c9b0` (130 inputs).

The excerpt omits leading fingerprints and earlier gate output. Record the demonstrated
results; this is not full-gate or revision-bound CI proof. Prior complete local ASGI proof
remains separate. No source or package change follows from this review.

## Dependency and upstream findings

Before remediation, both installed trees and lockfiles contained this chain (`npm ls`):

```text
eslint-config-next@16.3.8
  @next/eslint-plugin-next@16.3.8
    fast-glob@3.3.1
      micromatch@4.0.8
        braces@3.0.3
```

All are development dependencies in these lockfiles. That classification does not waive the
repository audit gate. Docs-site's live audit was not reached; its affected dependency is present.

The [reviewed advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) covers braces through
3.0.3 and lists no patched version. The [upstream fix PR](https://github.com/micromatch/braces/pull/72)
is open as of this review. Its proposed parser/walker depth limits are not an installed or
independently certified fix here. The PR discussion reports compatibility issues; review the
actual patch and published-version regression suite before selecting any derivative.
Next's [canary plugin manifest](https://github.com/vercel/next.js/blob/canary/packages/eslint-plugin-next/package.json)
still depends on fast-glob; a canary update alone is not a demonstrated solution.

The owner's npm suggestion downgrades `eslint-config-next` to 14.2.35 with a forced breaking
change. It is not an approved compatible fix for the current Next 16.3.8 lint setup.
No forced audit fix, audit exemption, threshold change, package rename to hide the advisory,
checker edit, installation or manifest/lockfile change was performed.

## Approved preparation scope and remaining blocker

Owner approved preparing dependency remediation for frontend and docs-site. Prefer a verified fixed
release when available. If evaluating a maintained patch or replacement, freeze source and
integrity, inspect provenance/license and installer scripts, retain lint-rule coverage, and
test published behavior plus deep string/direct-AST rejection and consumer compatibility.
A local patch retaining vulnerable version metadata can still fail the existing audit; prove
both the actual correction and the original audit gate's result without suppressions.

The [patch evaluation](braces-patch-evaluation.md) records an isolated backport: 9 tests per
project pass on Node 22, with 10,632 behavior comparisons and 243 depth assertions each.
It preserves published stringify behavior and affected 3.0.3 metadata; it is not installed
and does not clear the audit finding. The owner's source fetch now permits full fork inspection;
its inconsistent fractional limits and additional parser changes prevent selecting it as-is.
Present exact package/version/source and manifest/lock changes before installation. The
existing 18:31:56–20:31:56 Manila window is unchanged. The [exact private-backport proposal](braces-installation-proposal.md)
records tested artifact bytes, manifest previews and expected lock changes. Its 764 released
cases pass in a Node test-runner adapter; 9 review groups pass per app. Owner subsequently approved
the exact private artifact's adoption, installation and temporary maintenance (ADR-0038).
Both manifests/locks now pin it. After initial sandbox cache/DNS failure, the owner restores
both locked trees and reports validation exit 0 after full make check and 14 ASGI tests with
matching input hashes. Agent verifies both installed chains and 20 regressions per app.
The linked checkpoint records complete local owner proof; preceding detailed output is omitted
from the excerpt. Revision-bound CI remains separate, and the old frontend digest is historical.
