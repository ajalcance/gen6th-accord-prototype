# Supply chain security — retained controls

## Supply chain

- **2026-10-01 remediation verified locally:** GHSA-vcvr-r3jv-pc5j and
  GHSA-82fw-gwwq-j7x9 were addressed by exact Next/eslint-config-next 16.3.8 and
  Vitest/@vitest/mocker 4.1.11 in both projects. Manifests, regenerated locks and installed
  copies agree. The owner reached startup after the complete gate in the fail-fast sequence.
  Scoped npm 11.16.0 recovered from bundled npm 10.9.8's resolver crash without weakening
  peer validation, modifying global tools or editing npm source. Human review/CI remain
  required; no cooldown, owner label, audit severity or agent permission was changed.

- Dependencies are pinned; **Dependabot** proposes grouped updates.
- **The trust services (`trust/`, Go) are a sensitive path.** A change needs the owner's label.
  - Gates: gosec (via golangci-lint), govulncheck and Semgrep Go rules (no shell, no disabled TLS verification, no MD5/SHA-1, no `math/rand`).
  - Their suppressions count in the ratchet.
  - The Go toolchain is pinned by `go.mod`, with `GOTOOLCHAIN=local`.
- **The scanners that judge a PR are hash-locked** (`requirements-ci.in` → `requirements-ci.txt`, every transitive package hashed). CI installs them with `--require-hashes`, after a canary proves pip refuses a tampered lock. A lock line with no `# via` provenance fails `check_pins`.
- CI audits dependencies (`pip-audit`, `npm audit`) and scans code (**Semgrep** dangerous-ops +
  community rules; **bandit**).
- **The audits read the whole tree, dev dependencies included.** Build and test tools run in CI
  with the checkout, and on every developer machine. Until 2026-09-25 both audits skipped them.
  The comment justifying that named two compensating controls that did not exist: Dependabot
  alerts and a daily self-test. Three high advisories in npm dev tooling had gone unseen.
  The scanner lock (`requirements-ci.txt`) is not yet audited; that is registered in PLAN.
