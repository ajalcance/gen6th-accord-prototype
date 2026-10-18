# 0024. Persona versions and durable events share one PostgreSQL transaction

- **Status:** Proposed — implemented locally for review; owner acceptance pending
- **Date:** 2026-10-01
- **Deciders:** Repository owner

## Context

The owner accepted H1's frontend and authorized H2 persistence and observability,
while deferring Zynth repository work. Redis telemetry deliberately tolerates failed
delivery. That transport cannot establish durable evidence for every committed write.
The existing PostgreSQL event store and audit worker can serve this local slice without
new infrastructure, dependencies or authentication substitutes.

## Decision

1. Keep the persona service internal and fixture-only. No HTTP route, UI connection,
   membership grant endpoint or scaffold-token fallback is introduced. Future callers
   must provide an identity resolved by trusted server code.
2. Commit the mutable head, immutable version, minimal server event and immutable replay
   receipt together. A failed transaction commits none of them. Generate identifiers and
   receipt time on the server. Content stays out of events and operational logs.
   Persona/version/event IDs are server-built; write request UUIDs are client retry keys,
   validated and observed by the server, never actor identity or an approval assertion.
3. Recheck database membership for every operation, including retries. Only creators
   write their own personas; workspace members read versions. Lock membership and head
   rows, require the expected revision and reject changed reuse of a request identifier.
4. Freeze versions and replay receipts with PostgreSQL triggers. Enable and force tenant
   row-level policies on all four new tables using transaction-local workspace context.
   A future runtime role must have neither superuser nor BYPASSRLS privileges; current
   local administrator credentials do not establish active application isolation.
5. Insert server events directly into the existing cold store. The worker later seals
   them; commit is not sealing. Register emit, detection, audit and compliance decisions
   for saves, reads, access denials and write conflicts. Preserve client-event exclusions.
   Continue sealing durable records during Redis outage. Serialize sealers with a stable
   PostgreSQL transaction advisory lock, including the initially empty chain.
6. Retain auditable server events until a corresponding audit record exists, even past
   ordinary expiry. Keep only the event identifier on versions, without a foreign key
   preventing later cold-store retention. Retry receipts survive event expiry.
   Count the deleted rows atomically; refreshing receipt references must not mistake an
   ORM-cached expired event for a cold-store row.
7. Record authorization/conflict failures after rolling back attempted work. Database
   failure can prevent durable rejection evidence; emit a bounded operational failure
   containing only a bounded request UUID and propagate the failure.
   Apply that rule if rejection recording itself fails; worker errors expose only the
   exception class, excluding raw database exception details.
8. Permit workspace-authorized inspection of version/request/event references, recording
   the read. Report pending versus audit-entry presence; do not equate presence with a
   verified chain, signature, rights verdict or public passport.
9. Offer membership-scoped audit backlog count and oldest time from one aggregate query,
   with a tenant query index. Record the observation after measuring; counts exclude that
   subsequent event. This is an internal operation, not an automatic monitor or alert engine.

## Consequences

PostgreSQL availability is required for every operation. Membership locking serializes
writes by one actor within a workspace. Unsealed-event backlog needs operational monitoring
before exposing routes; retaining it protects evidence but can increase storage use.
Direct insertion does not send the event through Redis detection; a dedicated rule is
registered but no live alerting claim is made. Reliable detection delivery is a next slice.

Migration 0003 freezes its SQL independently of model definitions. Real PostgreSQL tests
must prove migrations, policies, immutable triggers, races, rollback, retention and sealing.
The sandbox cannot access Docker; offline rendering and static checks cannot replace that
evidence. On 2026-10-02 the owner reported all 92 targeted persona/migration tests passing
in 20.31s. No source hash accompanied the terminal report; full gates remain incomplete.
No production readiness, encryption, signing or verified identity is claimed.

## Alternatives considered

- Redis-only emission leaves a successful mutation without durable evidence on outage.
- A separate outbox duplicates the existing local event store for this slice. Reliable
  asynchronous detection and later Pub/Sub integration remain explicit follow-ups.
- Browser actors or HMAC scaffold tokens would bypass the unresolved identity boundary.
- Mock databases cannot verify PostgreSQL locks, RLS, triggers or migration fidelity.
