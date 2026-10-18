# 0018. CI integrity: every check proves it can see what it looks for

- **Status:** Accepted
- **Date:** 2026-09-24
- **Deciders:** Albert Alcance (founder)

## Context

An audit of the Zynth Auth repository at about 500K lines found that CI did not break loudly as the codebase grew; it broke silently. The worst case was a secret scanner that had scanned nothing in CI for months while every run reported success. Every defect shared one shape: a check that reported success without doing its job, and nothing that could tell the difference.

Checking Accord against the same audit on 2026-09-24 found the same defect here. CI ran gitleaks through its pre-commit hook (`gitleaks protect --staged`), which scans the staging area. A CI checkout has nothing staged, so the CI secret scan was blind from the first commit. The same review found:
- `.gitleaks.toml` exempted every Markdown file under `docs/` and the whole `.env.example`;
- `SECURITY.md` claimed a CI secret scan that did not exist;
- a Dependabot ignore rule added in #15 did less than intended;
- the docs CI job's path filter no longer covered `docs/public/`;
- an advisory Semgrep scan's output was discarded.

## Decision

Three rules apply to every change to CI, guards, scanners and their configuration:

1. **Nothing may stop catching what it catches today.** Before removing or narrowing any check, name what it catches and where else that is still caught. When removing work, check what that work was also providing.
2. **Cost is never the reason to check less.** Savings come only from not doing the same work twice.
3. **Supply-chain trust anchors are their own decision.** Changes to signing, image provenance, build caches or pinned scanners are made in their own PR, never bundled into a speed or cost change.

And one principle for every check that can report "nothing found":

4. **Plant a canary, watch it fail, then trust the green.** A negative-result check must prove on every run that it read input: a planted positive it must find, a printed denominator, and refusal on an empty input set. A fix to a silent check is itself watched failing, row by row, before it is trusted.

First application (this ADR's PR): the CI secret scan is replaced by `scripts/secret_scan.py`. It scans commits rather than the staging area, is pinned by version and SHA-256, and runs a canary in every tracked directory. It fails closed on:
- an empty or unresolvable range;
- a missing or crashing scanner;
- a scanner that writes no report.

There is no ignore list: `.gitleaks.toml` loses its path allowlists.

Follow-ups, each in its own PR (tracked in `docs/PLAN.md`):
- pin pre-commit hooks to commit SHAs and CI tools by hash;
- protect `dependabot.yml` as enforcement config;
- fix the devcontainer tag and add runtime-drift and Dependabot-coverage tests;
- repair the docs path filter;
- make the advisory Semgrep scan diff-aware and blocking, with a kept report;
- add hadolint and zizmor;
- write the periodic CI-integrity checklist.

## Consequences

- A green CI secret scan now means gitleaks demonstrably detected a planted token in every directory and then scanned at least one commit.
- Documentation and existing Markdown can no longer hide a secret behind a path exemption. A placeholder in docs must be recognisably a placeholder value.
- Deferred until a growth trigger (CI time per PR above about 15 minutes, codebase doubling, a new language or service, a new automation identity, or the approach of the first paying customer):
  - reusing results for byte-identical trees;
  - derived path filters;
  - SLSA provenance attestations.
- Before the first external customer (Stage 8 launch gate): agents act through a separate machine account with write, not admin, and code-owner review is required on guarded paths. Until then, "only the owner applies `guardrail-change`" is enforced by agent discipline, not by GitHub.

## Alternatives considered

- **Keep the pre-commit hook in CI and add `--all-files`.** Rejected: the hook's command ignores file names, so it would still scan the staging area.
- **A `.gitleaksignore` baseline of accepted findings.** Rejected: an ignore list only grows. Full history was triaged on 2026-09-24 and was clean; a future historic finding is rotated, not listed.
- **Canary at the repository root only.** Rejected: it would not detect an allowlist widened for one directory, which is exactly what `docs/` had.
