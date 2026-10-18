# 0041. Real creation and database provenance inventory

- **Status:** Proposed for owner PR review; implemented locally under approved preparation
- **Date:** 2026-10-04
- **Deciders:** Repository owner

## Context

The owner approved creation/storage preparation while awaiting Zynth tenant approval, then
required real data only and review of existing database entries. Renaming an example does not
give it genuine provenance. A disconnected form must not create records through test identity.

## Decision

1. Provide an empty creation form for name, biography, human contribution and AI disclosure,
   matching the existing bounded draft contract. Initial saves use the existing version API
   with null persona ID, revision zero, a fresh request ID and explicit confirmation. Server
   identity/membership remains authoritative; no client actor, fixture or portrait is supplied.
2. Permit authoring while disconnected but deny saving without matching read/write workspace
   gateways from the verified source. Workspace/session keys isolate in-memory drafts and
   exact uncertain intents. Confirmation resets after edits/navigation. No local-storage
   restore, implicit retry, or optimistic saved record is added. Validated receipts confirm
   actual saves; starting another persona requires an explicit form reset.
3. Extract receipt-only version/review/campaign/evidence views. Move the historical sample
   workspace, selectors, scenarios and handlers into `frontend/tests/legacy-passport/`.
   Retain isolated regression coverage without an application import or fallback. Verify
   application source/imports and production chunks contain no sample workspace content.
4. Provide `deploy/accord-data-inventory.sql` for an all-tenant operator connection in a
   repeatable-read, read-only transaction. Count tables/partitions and materialized views
   across non-system schemas and report legacy boolean fixture flags if still present.
   Refuse ordinary RLS-confined roles and any populated baseline pending provenance review.
   Foreign tables require source review without reading remote rows.
   Distinguish an uninitialized database from an empty Accord schema. Never delete, relabel,
   seed or provision rows. Existing populated-history migration refusal stays intact.

## Consequences and limits

The inventory is a baseline check, not a content classifier: populated genuine records also
require review, and absence of an old fixture flag does not prove provenance. Its output is
counts only; no credentials or record bodies are printed. A clean result covers the selected
database and snapshot only. Other retained stores/backups require separate inventory.
The owner runbook also inventories Redis keyspace counts; populated queues/cache need review.
After real provisioning/creation the store is intentionally populated; inventory refusal then
does not imply corruption. Disconnected drafts never transfer automatically to another session.

Frontend/ASGI tests prove form, serialization and retry behavior, not live PostgreSQL or Zynth.
Seven PostgreSQL inventory regressions and the full gate require owner/CI execution because the
agent cannot access Docker. Rendered browser acceptance is pending. No application database,
provider, credentials, permissions or deployment was changed by the agent.
See [creation/storage preparation](../runbooks/creation-and-storage-preparation.md).

## Alternatives considered

Sample promotion, automatic deletion and a runtime-role inventory would lose provenance or
hide tenant rows. A second save endpoint would duplicate existing transaction/idempotency logic.
Removing historical tests would lose regression evidence; they stay isolated outside application
source. Asset intake, AI processing and signing remain separate work.
