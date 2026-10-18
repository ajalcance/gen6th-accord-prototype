# ADR-0052: Private calibrated similarity serving

- Status: Proposed for human PR review; S4 source prepared under the approved slice plan
- Date: 2026-10-05
- Supersedes: None; builds on ADRs 0048–0051

## Context

The approved prototype needs a complete upload-to-candidate journey for synthetic performers.
S3 supplies approved references and encrypted representations, but supplies no measured model
selection or calibrated identity threshold. Query images must not enroll themselves or expose
another studio's records. Long model/key operations can outlive authorization or catalogue state.

## Decision

Prepare an injected, default-unavailable similarity runtime and expose its full query lifecycle
in Records. Redis holds context-bound encrypted metadata-free analysis/thumbnail pixels and
selected dual representations for an absolute maximum of ten minutes. Original uploads are
inspected then discarded. Explicit clear replaces the parent with a tombstone and deletes the
ten possible representation keys atomically; reads/retries never renew the original expiry.
Actor/workspace/query/part binding prevents shared query handles. No new SQL schema is needed.

The exact baseline includes at most 128 approved version/reference pairs, using each pair's
latest generation. Current heads are the default scope; approved history is an explicit option.
Overflow fails closed rather than ranking a partial catalogue. Unprocessed/incompatible
references remain visible in the denominator. Ciphertext/integrity/provider failures fail the
request instead of becoming an empty search. Validate finite normalized vectors before cosine.
Group each persona by its maximum face cosine with deterministic ties. Whole-image cosine is
context evidence only. Return at most five above-threshold candidates for human comparison.

Only an injected, reviewed, time-bound held-out calibration policy can enable preparation/search.
It binds model/revision/dimension, detector, decoder/capture/crop/quality recipes and evidence
digest. No production policy or thresholds ship. An unresolved publisher alias is rejected.
The threshold and top-versus-runner-up margin determine abstention; values are never identity
probabilities. A deployment identifier alone does not prove fixed model weights; the owner
must review model-service drift evidence and policy validity before activation.

Authorize membership before consuming images or metadata, before decrypt/model operations and
again after long work. Re-query the approved catalogue/head/latest-generation binding before
disclosure; a change produces a conflict. Private thumbnails and comparison reauthorize.
Server observations contain no images, vectors, digests or candidate identifiers.

## Consequences and acceptance

Redis is a required injected dependency; no process-memory fallback. Configure bounded Redis
connections, retention/persistence/backups and key services before activation. Clearing removes
live Redis keys, not an assurance that external backups/provider copies were erased. A racing
encoder may leave an inaccessible child until the original expiry; the closed parent blocks use.
Crashes/concurrent preparation can repeat external cost before cache commit; S7 owns durable
dispatch/reconciliation. Query receipts and similarity results are not durable issuance records.

S3's Google detector/encoder adapters are reused with the same safe analysis/crop pipeline.
Real Google execution, permitted benchmark, Recall@1/3/5, false matches, latency/cost,
PostgreSQL/RLS and rendered-browser acceptance remain separate gates. See
[S4 implementation and evidence](../hackathon/similarity-serving-slice.md).
