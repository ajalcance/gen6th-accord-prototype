# CI integrity checklist

Run this **quarterly**, and whenever a growth trigger fires (ADR-0018):
- CI time per PR passes about 15 minutes;
- the codebase doubles;
- a new language or service is added;
- a new automation account or AI agent gets write access;
- the first paying customer approaches.

**The principle behind every row:** a green check proves the check ran, not that it checked anything. Plant a canary, watch it fail, then trust the green.

Record the result as a dated entry in `docs/LESSONS.md`. Turn every "no" into a PLAN item.

| # | Check | How to verify here | Current control |
|---|---|---|---|
| 1 | Does the CI secret scan actually scan? | Read the `hygiene` job log for `canary — N/N` and `inspected N commit(s)` with N > 0 | `scripts/secret_scan.py` (canary in every tracked directory, fails closed) |
| 2 | Does every "no findings" check prove it read input? | For each scanner, find its denominator or canary in the log: secret scan (canary), Semgrep (rules × files), hadolint (Dockerfile count), guard tests (fault tests) | Canaries and denominators; `tests/guards/` |
| 3 | Are all tools pinned by version and hash, or by commit SHA? | Grep workflows for `pip install` without `-c`, and `curl` without a `sha256sum --check`. Check pre-commit `rev:`s are 40-hex. Run zizmor **online** (with `GH_TOKEN` set) so version comments are checked against their tags: offline it skips that audit and reports clean | `test_every_pre_commit_hook_is_pinned_to_a_commit`; `test_every_action_is_pinned_to_a_commit_with_its_exact_version`; CI zizmor refuses to run offline; binaries checksum-verified; scanners hash-locked (`requirements-ci.in` → `.txt`), installed with `--require-hashes` behind a tampered-lock canary, and every lock line needs `# via` provenance (`check_pins`) |
| 4 | Does CI test the runtime we ship? | `make guard-tests` | `tests/guards/test_runtime_alignment.py` |
| 5 | Do any checks run nowhere? | List `make` targets that sound like checks and grep the workflows for each | `scripts/check_guard_coverage.py`; `make policy` as the one list |
| 6 | Does every security-doc claim have a blocking config line? | For each "X is enforced by Y" sentence in `docs/SECURITY.md`, find the line that makes Y blocking | Manual, this checklist |
| 7 | Do path filters cover every file each suite reads? | Grep each test suite for paths outside its own directory and compare with the `changes` job filters | `test_the_docs_path_filter_covers_what_the_docs_site_publishes` (docs only, so far) |
| 8 | Are we re-testing byte-identical trees? | Compare `git rev-parse <merge>^{tree}` with the PR head's tree for recent merges | Not addressed: deferred until CI time is significant (growth trigger) |
| 9 | Are "flaky" tests really flaky? | Before re-running a flake, read its timestamps and look for boundaries (minute, bucket, page, retry) | Rule: a flake is a hypothesis about production until disproved |
| 10 | Is enforcement config protected? | In a PR, try editing `dependabot.yml`, `.gitleaks.toml`, a Semgrep rule or a workflow: the meta-guard must demand `guardrail-change` | `GUARD_FILE_RE` in `scripts/meta_guard.py`, tested |
| 11 | Is the automation identity separate from the approver? | Who can apply `guardrail-change` and merge? | **Not yet:** the agent acts through the owner's account. Stage 8 launch gate: a machine account with write access, and required code-owner review |
| 12 | Images scanned, SBOM, provenance, signature verified at deploy? | Read `release.yml` | SBOM and vulnerability scan before cosign signing. Provenance attestations and deploy-time verification arrive with the Cloud Run release path |

## Known reviewed exceptions

Each carries a written reason in place and needed the owner's `allow-suppressions` label.

| Where | Exception | Why |
|---|---|---|
| `.github/workflows/ci.yml` `static` checkout | zizmor `artipacked` | Keeps its credential for the explicit base-branch `git fetch` on a private repository |
| `.github/workflows/release.yml` `guard` checkout | zizmor `artipacked` | Same reason, for the release ancestry check |
| `.devcontainer/Dockerfile` | hadolint `DL3008` | Dev-only image, base pinned by digest. Exact apt pins break on Debian point releases |
