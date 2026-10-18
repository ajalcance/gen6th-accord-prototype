# ADR-0037: Prepare session-gated persona writes and authored-draft recovery

**Status:** Proposed; owner authorized local preparation on 2026-10-03.
Owner current-source SQL/full local gates pass; security/ADR review, PR CI, rendered
acceptance and activation remain pending.
**Date:** 2026-10-03
**Builds on:** ADRs 0024–0026 and 0032–0036.

## Context

Versions, independent reviews and campaigns have internal transactional services and typed
frontend commands. The saved source has prepared reads but rejects writes. A typed gateway
alone does not prove ASGI serialization or preserve uncertain intent across navigation.
The owner approved a two-hour write-preparation slice at 12:50:44–14:50:44 Manila. This
authorization does not activate routes, trusted credentials, providers, uploads or cloud.

## Decision

- Prepare a separate unmounted four-operation router: version save, independent review,
  scoped campaign offer and recipient decision/creator revocation. Declare strict existing
  command/receipt models. New-persona saves require expected revision zero.
- Reuse ADR-0034's mandatory verifier before database access. Actor/human classification
  comes from verified output, never command fields. Existing services recheck membership,
  ownership, independence, exact versions/reviews/assets, transitions and replay equality.
  There is no new login, grant, table, migration, policy or authoritative client event.
- Reuse transactional server actions and emit/detection/audit/compliance registrations.
  Sanitize denied/conflict/validation/unavailable errors and invalid response serialization;
  unexpected failures return 500. Responses are uncached. No draft or exception detail logs.
- Prepare a write-only HTTP transport with same-origin mode/credentials, no cache/redirects
  and no automatic POST retry. Existing read transports still reject writes. The application
  mounts no persona factory and supplies no saved source or write gateway.
- An explicitly injected same-workspace write gateway exposes structured fixture forms
  alongside loaded saved details. Review uses the fetched exact-version predecessor;
  campaign decisions use a discovered offer/current decision. Offer preparation requires
  the latest approved review and an injected bounded fixture catalogue for that version.
  Reference metadata grants no authorization; services validate assets again. Missing,
  invalid or foreign catalogues cannot be replaced with private quarantine evidence.
- Require explicit confirmation; editing or reopening clears it. Retain only authored fields
  and failed/uncertain intents in studio memory, keyed by workspace, trusted session context,
  operation and resource. Preserve browser drafts independently. Never store fetched records,
  successful receipts or credentials there or in localStorage. Other session contexts cannot
  display/retry these drafts. Browser reload discards this in-memory recovery; durable or
  cross-session recovery is not implemented.
- Cancellation immediately records uncertainty, aborts waiting and rejects late responses.
  Explicit retry preserves request ID/content after edits, navigation or gateway replacement.
  Uncertainty blocks new intent, including after a denied retry or invalid server receipt.
  Restore verified saved access before retrying that retained intent. Invalid local input is
  rejected before sending and does not create uncertainty. Conflict reloads current records for comparison, an explicit
  new base and new confirmation; no automatic merge. Access loss clears fetched content and
  retry closures while retaining authored drafts/intents.
- Validate review/decision receipt IDs and ordinal shape against the expected predecessor,
  so an old decision cannot masquerade as a new receipt. Successful storage stays unsigned
  and does not establish current campaign permission or ownership.
- Keep synthetic verifiers, process bridging, stub services and seeded catalogues under tests.
  Test HTTP DTOs/client/parsers/forms separately from real-service PostgreSQL journeys.
  The additional integration command is owner/local proof, not a newly wired CI gate.

## Gates and consequences

Before live mounting/injection: approved Zynth/provider and canonical identity mapping,
credential/origin/CSRF/TLS/header/nonce and observation review, bounded ingress/quotas/timeouts,
source-bound database/audit proof and separate owner activation. Synthetic identity and HMAC
scaffold fallback are unavailable. Evidence providers, analysis, signing, public projection,
licensing/publication and deployment remain separate gated work.

Verification and the source-checked owner command are in the
[write checkpoint](../hackathon/h2-write-preparation-review.md). Older 454-test and ADR-0036
checkpoints remain historical. Rendered desktop/mobile/zoom/keyboard/touch/reduced-motion
acceptance and revision-bound PR CI remain required. Owner PostgreSQL proof passes. Keep router,
transport/recovery/forms, test bridge/SQL journeys and ADR/docs separately reviewable from
existing dirty policy, dependency, read and evidence changes.

On October 3 the owner approved a test-fixture correction after four PostgreSQL failures:
preserve immutable member references and downgrade write roles to `viewer` before exact retry.
Retain 403/no-new-record assertions. This tests write-role loss; it does not add full membership
revocation or change any constraint, service or authority. Owner's corrected 553-test SQL
suite and Trust pass. The intermediate frontend braces audit failure is superseded by
approved ADR-0038 remediation and owner complete local validation exit 0, including 14
ASGI tests and matching backend/frontend/remediation hashes. The supplied closeout excerpt
omits preceding detailed gate output; this is owner local proof, not agent full-gate or CI proof.
The [readiness review](../hackathon/h2-pr-readiness-review.md) records remaining review units.
