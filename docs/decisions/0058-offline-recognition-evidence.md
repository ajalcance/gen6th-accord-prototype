# ADR-0058: Offline recognition evidence stays separate from runtime authorization

Date: 2026-10-06
Status: Accepted for the owner-authorized prototype continuation

## Context

S3 prepared a family-separated evaluator, but actual permitted images and provider observations
are still needed. Missing costs could not be represented; failed absent queries could make an
aggregate false-match rate appear reassuring. Backend evaluator output had no frontend viewer.

## Decision

Extend the existing offline evaluator with versioned typed reports, canonical input fingerprints,
per-case totals/scored/failed/abstained counts, scored false-match rates, recall at 1/3/5 and
nearest-rank p50/p95/max latency over all supplied attempts. Missing cost means unknown total;
show the known subtotal and missing-observation count. Keep failed known queries in recall.
Keep the legacy absent/all-query ratio for compatibility, alongside scored denominators.

The provisional threshold comes exclusively from calibration impostors. A perfect impostor can
produce a threshold above one, meaning abstain everywhere; it is not a deployable calibration.
This evaluator does not evaluate the production margin or issue a `CalibrationPolicy`.
Limit each split to two million reference/query comparisons and JSON inputs to 16 MiB.

An explicit CLI corpus root checks every relative asset path and SHA-256 within a 10 MiB/file,
256 MiB/corpus budget. It checks bytes, not image inspection, generation provenance, permission
validity or whether a provider actually computed the submitted vectors. Without it, binding is
explicitly unchecked. Duplicate input JSON keys fail. No asset discovery or provider calls occur.

Expose report inspection in Connection & readiness. It reads a bounded file locally, validates
shape/aggregate consistency, shows supplied evidence and human-review status, and isolates stale
reads. It neither uploads observations nor enables search, persists a report or changes runtime
policy. Browser imports are untrusted; even claimed byte checks require independent review.

## Consequences and acceptance

No new HTTP action, migration, credential, package or server telemetry action is introduced.
Offline CLI and local viewer operations are not sealed server audit facts. Actual benchmarking
still needs permitted corpus, frozen capture/encoder recipes and operating point, provider logs,
query/reference traces, sample adequacy review and independently reviewed evidence. SQL and live
Google acceptance remain separate. Synthetic arithmetic tests cannot close H3/H5.
See [workflow and validation](../hackathon/recognition-evaluation-workflow.md).
