# ADR-0049 — Exact portrait search as the first serving slice

- Status: Accepted for source implementation; runtime and SQL acceptance pending
- Date: 2026-10-05
- Context: Owner approved ADR-0048 and requested implementation slices with every backend
  capability exposed in the frontend.

## Decision

Start with an actual image-query serving path using server-verified exact-file SHA-256 and the
existing inspected, encrypted, immutable portrait history. This is one evidence method within
the approved capture/search architecture, separate from future facial similarity retrieval.

Authorize the human session and studio membership before body consumption. Reuse the bounded
byte envelope; do not decode, scan, enroll or persist the query. Search only portraits bound to
versions in the authorized studio. Return the newest matching version per persona, at most 20,
with an explicit overflow flag. Historical matching versions remain legitimate evidence even
when the current version has a different or removed portrait.

Expose Records → Search by portrait, manual submission, exact-file evidence and empty/error/
retry/cancel/clear states. Inspection freshly authorizes and binds the exact historical version;
this view remains read-only. Current session changes and known permission loss clear results.

Emit the existing `persona.workspace_observed` server action with a distinct search operation
and bounded counts, reusing its audit/detection/compliance decisions. Do not log query bytes,
filenames, digests or candidate IDs. Preserve private no-store responses and sanitized failures.

## Consequences

This creates a reviewable backend-to-frontend search path without new models, dependencies,
database extensions, schema changes, cloud cost or rights/identity assertions. It uses existing
portrait metadata under existing workspace authorization; it does not decrypt original bytes.
Changing encoding, cropping or regenerating a face generally changes SHA-256 and will not match.
An empty result means no identical enrolled portrait in that studio, not absence of a performer.

The [slice plan](../hackathon/capture-search-slices.md) retains analysis capture, face selection,
model evaluation, similarity serving and actual Google integration as required follow-ups.
S1 alone is insufficient for the approved hackathon technology demonstration. Existing portrait
runtime/migration/grant prerequisites remain separately gated; this change does not activate them.

## Verification

Contract, authorization-order, real ASGI routing/error and frontend transport/state tests cover
the new path. Disposable PostgreSQL tests cover historical grouping, studio isolation, bounded
overflow and no query enrollment. Execution status belongs in the slice validation record;
synthetic HTTP/UI evidence is not a substitute for actual SQL or real-store acceptance.
