# Approved private braces backport

Owner approved adoption, installation in both apps and temporary maintenance on 2026-10-03.
The existing application ADR-0038 approval is preserved in docs/runbooks/private-braces-approved-decision.md; final application history retains its numbering. This is a private derivative of upstream braces 3.0.3, not an
official release. The retained MIT license covers the dependency; product licensing is unchanged.

- Archive: braces-3.0.4-accord.1.tgz, SHA-256
  2155cb703acd5f4247164321feb72df40214676b5cc7c362060f56e64e33bf7c.
- Source: source/ contains the exact ten packaged files, including license and base commit.
- Patch: depth-backport.patch, SHA-256
  54633452e16239fe127f90c12cfecf14939396d562b095f9a16ba753eea1bff4.
  Blank patch context lines are normalized for repository hygiene; reverse/apply verification
  reproduces all five packaged source files exactly. Packaged provenance retains the approved
  original patch hash a3f08706e45f1e180112f91f07a871b284b92613bccdfb2724a165ff4f96c91e.
- Copies: frontend/vendor/braces/ and docs-site/vendor/braces/ retain identical archive bytes.
  Frontend Docker copies its archive before npm ci without enlarging its build context.
- Both app manifests directly pin the artifact as a development dependency and use a scoped
  micromatch@4.0.8 -> braces -> 3.0.4-accord.1 override, deduplicating to the pinned local
  artifact. Other dependency identities are unchanged.
- Both ordinary Vitest suites test source/lock/archive identity, depth rejection and real
  micromatch/fast-glob/Next root resolution.

The owner maintains this derivative temporarily and reviews future upstream advisories against
the recorded 3.0.3 base even when version-based audit classifies the derivative differently.
Retire it only after a verified official release passes regressions, consumer checks and audit.
No audit exemption, suppression or altered lint rule accompanies this dependency.

Source inherits upstream parser/function structure. The owner approved retaining that structure
for the narrow patch; authored project tests and patch remain subject to project standards.
