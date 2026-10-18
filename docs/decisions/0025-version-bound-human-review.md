# 0025. Human review decisions bind immutable persona versions

- **Status:** Proposed — implemented locally for review; owner acceptance pending
- **Date:** 2026-10-02
- **Deciders:** Repository owner

## Context

The owner approved independent review and campaign persistence after the storage slice.
Persona edits must not inherit earlier approvals. Reviewer intent, server attribution and
durable event storage must remain distinct from browser claims or model suggestions.
Zynth integration is deferred; no real identity/session route may be substituted.

## Decision

1. Store append-only `persona_reviews`, bound by a tenant-scoped foreign key to an immutable
   version. Migration 0004 adds forced tenant RLS and update/delete rejection triggers.
2. Require a trusted internal human fixture context and the stored reviewer role. Reject
   agents/services and self-review, even if an owner's membership later becomes reviewer.
   Context classification is a fixture assumption, not verified human identity. A future
   adapter must derive identity/classification from the verified server session.
3. Lock the persona head, shared with edits, before checking the current version and latest
   review. Compare the expected previous review ID; assign a monotonic per-version ordinal.
   Racing reviewers cannot silently overwrite each other's decision.
4. Embed request ID/fingerprint in each immutable decision. Reauthorize exact retries and
   return the original receipt; reject changed reuse. A historical retry does not establish
   that approval is still current. New decisions on stale versions fail.
5. Commit the decision and minimal server event together. Track denied/conflicting attempts
   after rollback. Keep statement text out of events. Preserve nonhuman rejection attribution.
6. Provide bounded, cursor-based history reads with membership authorization and durable
   observation events. Register every action for detection, audit and compliance coverage.

## Consequences

Review history survives later decisions and edits. Campaign eligibility must use the exact
latest approved review and current version, rather than accepting a historical receipt.
Test schemas and frozen migrations must both prove the database protections on PostgreSQL.
Static/contract tests pass locally; new database cases still require owner/CI execution.
The owner's earlier 92-test result predates this slice and cannot validate migration 0004.
No routes, identity fallback, private evidence ingestion, cloud activation or signing is added.
Owner-controlled migration and ADR review gates remain required before merge.

## Alternatives considered

- Mutable approval flags erase decision history and allow stale authorization.
- Timestamps alone do not order concurrent decisions reliably; ordinals serialize under the head lock.
- Browser-supplied human/role fields or model approval bypass the trusted principal boundary.
- Connecting scaffold HMAC tokens would imply a completed identity integration that does not exist.
