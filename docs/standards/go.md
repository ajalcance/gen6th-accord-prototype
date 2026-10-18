# GO — Go standards for the trust services

`trust/` holds the code that signs and verifies: the Trust Signer, Trust Log, Anchor Job and
Public Verifier (Addendum 01 §8). A defect there changes what every record's signature means, so
it is a sensitive path: a change needs the owner's label (`scripts/meta_guard.py`). Markers are
explained in [`README.md`](README.md); the **Mechanism** column names what enforces a rule, and is
empty when nothing does.

## Gates

| ID | Rule | Enforcement | Mechanism |
|---|---|---|---|
| GO-001 | Every change passes the full gate: `go mod verify`, `go vet`, golangci-lint (with gofmt, goimports and gosec), govulncheck and `go test -race`. `make trust` and the CI `trust` job run the same commands. | `[CI]` | `.github/workflows/ci.yml`, `tests/guards/test_workflow_invariants.py` |
| GO-002 | A linter is never disabled and a finding never silenced to make code pass. `//nolint`, `#nosec` and `// nosemgrep` count as suppressions and need the owner's label; fix the code instead. | `[CI]` | `scripts/meta_guard.py` |
| GO-003 | Trust code never runs a shell, disables TLS verification, uses MD5 or SHA-1, or draws randomness from `math/rand`. `unsafe` needs a reviewed justification. | `[CI]` | `.semgrep/dangerous-ops.yml` |
| GO-004 | Errors are wrapped with `%w` and inspected with `errors.Is` / `errors.As`, never compared by string. An error crossing a package boundary is wrapped with context. | `[CI]` | `trust/.golangci.yml` |

## Design

| ID | Rule | Enforcement | Mechanism |
|---|---|---|---|
| GO-010 | Content is named by one digest form, `sha256:` followed by 64 lowercase hex characters, produced and parsed only by `trust/internal/digest`. A second encoding lets a signer and a verifier disagree about the same bytes. | `[Review]` | — |
| GO-011 | The Go version comes from `trust/go.mod` alone, and builds run with `GOTOOLCHAIN=local`, so no command downloads a different toolchain behind the pinned one. | `[Review]` | — |
| GO-012 | A new dependency is a reviewed event: it arrives pinned in `go.sum`, has cleared the 7-day cooldown, and is watched by Dependabot. The standard library is the default. | `[Review]` | — |
