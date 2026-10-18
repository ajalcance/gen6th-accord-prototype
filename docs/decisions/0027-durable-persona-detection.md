# ADR-0027: Durable internal persona detection

**Status:** Proposed; implemented for owner review, no deployment activation.
**Date:** 2026-10-02

## Context

Server persona events commit directly to PostgreSQL, bypassing Redis ingestion. The
detection catalogue defines decisions but has no evaluator. Sealing is not detection.

## Decision

Evaluate registered server persona events with a workspace in bounded batches of 100.
A transaction advisory lock shared with retention serializes workers. Primary-keyed
receipts store event/workspace, catalogue digest, time, retention flag and minimal findings
atomically. Failed batches roll back and retry through the existing poll loop. Missing
receipt discovery catches late events; completed event IDs have no duplicate effects.

Windows count the same tenant's server persona observations in
`(event time - rule window, event time]`. Equal timestamps share windows. Each qualifying
anchor records a finding, not a deduplicated incident or external notification. Counts
reflect available data during evaluation; late events do not rewrite prior receipts.
Windows preceding configured retention are flagged. Even in-retention windows cannot
certify complete ingestion or absence of threats.

Pending events and available supporting persona windows survive expiry. Retention shares
the evaluation lock and preserves unsealed audit evidence. Client data expires normally
and cannot contribute. Receipts survive cold expiry without actors, statements or private
evidence; they are operational records, not signed or tamper-evident compliance proof.

Like command events/audit tables, receipts are internal cross-tenant worker data without
RLS. No route exposes them. Aggregate reads require stored membership, explicit tenant
predicates and the existing auditable workspace-observation action. Future HTTP access
or database-role separation requires reviewed identity integration.

## Verification and consequences

Each committed batch also emits a minimal server event per workspace, in the same
transaction, with evaluated count and catalogue digest. It is registered for emit,
detection, audit and compliance; category `command` avoids recursive persona evaluation.

Migration 0006 creates receipts and workspace/time index. Existing migration tests compare
schemas and exercise downgrade/reapply. Tests cover predicates, thresholds, tenant/source
isolation, windows, late delivery, rollback/retry, concurrency, backlog authorization and
retention. PostgreSQL execution remains owner/CI work. No dependency, cloud, notification,
enforcement or identity substitute added. Rule changes affect pending events; replay of
completed evaluations is a separate decision.
