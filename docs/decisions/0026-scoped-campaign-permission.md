# 0026. Campaign permission binds the version, review, assets and recipient

- **Status:** Proposed — implemented locally for review; owner acceptance pending
- **Date:** 2026-10-02
- **Deciders:** Repository owner

## Context

The owner approved campaign persistence independently of creation and review. A persona
approval is insufficient permission for an arbitrary campaign. The creator's authorization
and the recipient's decision must be distinct, reconstructable and safe under retries/races.
Zynth, private uploads/encryption and signing remain gated; this slice uses fictional fixtures.

## Decision

1. Store immutable offers with exact version/review references, a named workspace recipient,
   purpose, conditions and timezone-aware duration (positive, at most 366 days). Only the
   persona owner with a stored creator role and trusted human fixture context can offer use.
2. Bind 1–20 distinct assets through immutable relations. Fixture assets are server-seeded
   references with bounded labels and SHA-256 digests; composite foreign keys prohibit
   cross-workspace or cross-version bindings. No upload, scan or verified evidence hash
   ingestion is introduced. Fixture fingerprints do not establish ownership.
3. Require the latest approved review of the current version and current reviewer/recipient
   permissions when offering. A recipient must be independent of the owner and have the
   stored reviewer role. Campaign conditions remain private to the owner and named recipient.
4. Record recipient acceptance/change requests separately from creator revocation. Serialize
   transitions with the persona head lock and compare expected previous decision IDs.
   Change requests withdraw acceptance and require a new offer; revocation is final for an
   offer. The creator may revoke pending, accepted or change-requested offers.
5. Reauthorize exact retries and return their historical immutable receipts. Changed reuse
   conflicts. Recompute current fixture eligibility from the version, latest exact review,
   stored roles, latest campaign decision and server time; never infer it from replay success.
   New approvals of the same version cannot revive offers bound to an older review ID.
6. Commit offers, asset bindings, decisions and minimal server events atomically. Migration
   0005 freezes forced tenant RLS, immutable triggers and tenant/version foreign keys.
   Decision ordinals and retry keys are unique. Cold events are not FK dependencies because
   they expire after sealing. History reads use bounded stable cursors and record observations.
7. Observe review/offer/decision event and audit-entry presence through authorized reference
   inspection. Match action, actor, tenant, timestamp, resource, metadata and cold-event
   source/correlation. Missing or inconsistent evidence fails closed. Presence is neither
   verified chain integrity nor a signature; current permission is a separate status read.

## Consequences

Historical records remain readable after withdrawal, review replacement, edits or expiry.
Recipient/creator roles are rechecked; loss of a required role blocks current eligibility.
This is an internal fixture workflow, not a legal licence, verified human decision or issued
passport. No routes, real evidence processing, UI/backend connection or services are activated.
PostgreSQL tests must prove actual migration and metadata paths, races, rollback and RLS.
The earlier owner-reported 92-test result predates this slice. Full gates remain incomplete.
Owner-controlled migration/ADR review gates apply before merge; no guard is changed.

## Alternatives considered

- A single approval boolean conflates creation review with campaign permission and loses history.
- Allowing acceptance after a change request would approve an unchanged withdrawn scope.
- Embedding browser asset hashes without a trusted catalogue would authorize unbound claims.
- Updating issued records or trusting old retry receipts could revive superseded permission.
- A global public campaign query would expose private conditions to unrelated workspace members.
