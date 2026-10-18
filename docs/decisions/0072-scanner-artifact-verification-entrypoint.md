# ADR-0072 — Required-input scanner artifact verification entry point

Date: 2026-10-12. Status: approved preparation; PR #60 merged on main, application integration pending.

## Context

Application ADR-0021 records the Codex managed boundary, followed by ADRs 0022–0071.
Scanner PR #60 starts from older main with ADRs 0001–0020 and calls its decision ADR-0021.
This document preserves that scanner decision under application integration number 0072.
Its approved behavior is unchanged. Isolated numbering stays contiguous until integration;
the [reconciliation scope](../hackathon/scanner-release-integration-scope-2026-10-12.md) maps citations.

## Decision

Require raw manifest, raw image configuration, reviewed actual service JSON and independently
signature-verified immutable scanner image reference at the scanner-launch-check boundary.
Hash raw manifest bytes against that reference, then hash/size-check raw config against its
descriptor before validating Linux/amd64, fixed UID/command, native health and startup topology.
Reject indexes/artifacts, ambiguous JSON, command/environment overrides and scanner ingress.

The caller verifies signatures under the existing exact issuer/identity policy first. Never derive
the trusted expected image from the supplied manifest. Bind service bytes to reviewed signed
assembly evidence. Content binding is separate from signature and native readiness acceptance.
Use generated inputs only for tests; missing genuine deployment inputs must fail closed.
Preserve every existing guard, exclusion policy, threshold and owner approval boundary.

## Consequences

The application checkout does not yet contain this Make target or validators. PR #60 merged as
524dbbb18d9c2065af29ab1c017ce453ae93f9cf;
its original Linux CI failed before oversized CLI execution. Short case IDs are published at
36cc85addeb8; Linux guards pass with 865 passed/18 skipped, preserving the full payload and denial
assertions. Owner applied guardrail-change; fresh run 38241515740 passes including ci-complete.
Main push run 38244164224 also passes at exact squash commit 524dbbb18d9c. Full application/native
acceptance and application history integration remain pending; skipped suites are not passed suites.
Release/publication/promotion/import integration, complete genuine build locks, SBOM/signing,
assembly evidence and native acceptance remain pending. No active production release gate is
claimed here. This number mapping is documentation preparation, not a merged implementation.

At integration preserve Codex ADR-0021, retain this scanner ADR-0072 and reconcile all scanner
citations/indexes without overwriting either decision. Owner review/guardrail-change label and
exact PR/main CI remain required. One environment, measured MVP sizing, Zynth later, Tasks paused;
no production tests, mock providers, live stubs, build, cloud mutation or resource recreation.
