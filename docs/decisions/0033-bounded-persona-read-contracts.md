# ADR-0033: Bounded persona gallery and evidence/history reads

**Status:** Proposed; owner authorized the next implementation tasks on 2026-10-02.
**Date:** 2026-10-02
**Builds on:** ADRs 0024–0027 and 0031–0032. No session/API activation.

## Context

The internal workflow and disconnected write adapters passed the owner-backed 397-test
checkpoint. The gallery still lacked an authorized listing operation; history and evidence
reads lacked frontend runtime contracts. These are prerequisites for later connection, not
permission to substitute a browser-selected actor for trusted identity.

## Decision

- List current heads only, after stored workspace membership and human-context authorization.
  Use the same workspace read boundary as existing internal version reads. Every page is
  capped at 100 records; default is 20. No unbounded dump or fabricated total count.
- Order by stable persona UUID and paginate after that UUID. One SELECT joins each persona
  to its current immutable version. Concurrent inserts before the cursor or renamed records
  appear on refresh; this is not a multi-page snapshot isolation claim.
- Search bounded current names as literal case-insensitive text. Escape SQL wildcard
  characters and bind values; do not record the search string in telemetry.
- Record every successful gallery query, including empty results, using the existing
  `persona.workspace_observed` action with `persona_gallery` resource and returned count.
  Existing detection/audit/compliance decisions apply; no action is exempted or removed.
- Expose owner-authorized private evidence metadata through a separate internal status
  function. It never needs a key provider or returns bytes/key material. Its existing
  `persona.evidence_read` observation explicitly identifies `view=metadata`.
- Add prepared frontend adapters for gallery, review/campaign history, private evidence
  status and workflow evidence. Validate item identity/workspace, ordering, duplicates,
  requested page bounds and the exact next cursor before exposing a page.
- A matching retained audit-entry reference means presence only. Incomplete references
  fail validation; no frontend `verified` or signature field is invented. Private upload
  metadata is a separate shape from workflow audit evidence.
- Keep cancellation checks before and after reads. Default transport stays disconnected;
  no HTTP routes or identity providers are mounted and no fixture UI state is relabelled live.

## Verification and remaining work

Share read wire examples with backend Pydantic validation and frontend parser tests.
PostgreSQL cases prove current-head paging, literal search, cross-workspace isolation,
membership revocation, empty-query observation and private-status authorization. Source-bound
owner/CI database validation is required for the changed tree.

Session-bound transport, UI loading/paging integration, retention/key/scanner providers,
index/query-load measurements and full audit gates remain before live use. Existing stored
role policy is reused; this decision does not add a membership-grant endpoint or owner role.
