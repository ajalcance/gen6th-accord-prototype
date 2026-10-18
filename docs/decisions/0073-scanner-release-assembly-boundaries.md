# ADR-0073 — Mandatory scanner release assembly boundaries

Date: 2026-10-12. Status: owner-approved preparation; uncommitted implementation, pending PR/CI.

## Context

PR #60 merged artifact/config binding and fixed launch verification. Existing release publication
and promotion did not require a scanner component. Owner approved this separate guard unit after
exact squash commit 524dbbb18d9c2065af29ab1c017ce453ae93f9cf passed main push CI 38244164224.
No genuine packaging or native acceptance exists in this isolated baseline.

## Decision

Require scanner packaging before any candidate build. Build the scanner once for linux/amd64,
sign its immutable digest, produce SPDX and keep the existing high/fixable vulnerability policy.
Require native acceptance against that digest and hash twelve actual artifact/report files into
scanner-assembly.json. Validate the unchanged release evidence and mandatory scanner component,
raw manifest/config, service topology, all layer blob digests and actual archive path inventories.
Reject absent/modified/context-mismatched reports, failed native checks, missing finite measured
peaks, fixture/cache/secret paths, unverified input/definition receipts and unresolved licenses.

Candidate publication verifies every image signature before signing and publishing the assembly.
Promotion verifies release and assembly blob signatures and every image under the exact release
workflow/tag identity and existing GitHub OIDC issuer before any retag. Destination verification
does the same, verifies the destination signature and requires source/destination registry digest
equality. It never copies, builds, deploys or alters cloud resources. See the
[operator contract](../hackathon/scanner-release-integration-scope-2026-10-12.md).

## Consequences

Missing packaging/native producers block candidate release; they are intentionally mandatory.
Input/seed/config/license/native receipts remain signed producer claims: this validator does not
execute upstream signature verification, inspect seed contents or measure runtime itself. Genuine
producer implementation and owner-reviewed Linux execution must establish those facts before use.
Generated reports and tool spies live only in tests; they are not production acceptance.
All existing preflight/holds/readiness/typed confirmation and guard settings remain enforced.
No install, build, signed release, registry import, cloud mutation or production tests were run.
Minimum workable sizing follows measurements; one production environment, Zynth later, Tasks paused.

This baseline's ADRs are contiguous. At application integration retain Codex ADR-0021, map scanner
ADR-0021 to ADR-0072 and this ADR-0022 to ADR-0073; update citations without overwriting decisions.
