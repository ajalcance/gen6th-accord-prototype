# ADR-0035: Expose governance concepts without implying a live connection

**Status:** Proposed; owner authorized local governance/recovery UI implementation on
2026-10-03. PR/security review and real integration remain pending.
**Date:** 2026-10-03
**Builds on:** ADRs 0015 and 0031–0034.

## Context

The backend prepares immutable versions, independent review, campaign decisions, private
evidence and audit references. The owner wants those concepts visible while Zynth remains
deferred, with useful empty/failure states and no loss of editable drafts. The home page has
no trusted session or persona API connection; browser-selected actors cannot fill that gap.

## Decision

- Add an “Evidence & decisions” panel to all five screens and quick actions. Keep version,
  review, campaign, evidence and save recovery sections separately navigable. Use the existing
  compact shell, focus trap, native disclosures, semantic colors and responsive two-column layout.
- Use a separately named fictional governance record and frozen example clock. Label the
  panel as a contract preview with no network requests. Never attach its invented IDs or history
  to the selected browser persona, saved records, server authority or verified identity.
- Exercise existing runtime gateway parsers and read/query controllers with an isolated local
  read transport, which rejects writes and has no HTTP, credential, storage or upload access. Changing read
  conditions/versions/pages clears preceding data; explicit retry is limited to transient failures.
- Keep historical review/acceptance distinct from current campaign eligibility. Reviewers must
  differ from the version creator. Audit references must bind the displayed version, actor,
  event and exact serialized timestamp in addition to existing tenant/resource/action validation.
  Reject fractional-time mismatches rather than rounding reference times through JavaScript Date.
- Display quarantined, inspection-passed, rejected and expired evidence independently.
  Inspection-passed evidence remains temporary private quarantine, not a rights determination
  or campaign asset. Expiry blocks access; it does not establish deletion or override holds.
  Display metadata only, with no private payload, storage address, key reference or download.
- Keep unsigned records explicit. “Audit pending” and “Audit entry present” describe presence,
  never chain integrity, signing or public verification.
- Recovery examples use a snapshot of the current draft with the existing mutation controller.
  Conflict comparison is read-only, permission loss offers connection details without fallback
  login, and uncertain/cancelled requests preserve the same request ID/content on explicit retry.
  No example changes a browser record, local version, approval, persistence or visibility.
- Empty states explain the prerequisite and offer actual Creation/connection navigation.
  Restoring an example changes fixture conditions only, never real permission or a service.

## Validation and remaining gates

Frontend tests cover every section, paging/version switches, exact bindings, denied/empty/
unavailable states, draft preservation, cancellation/retry and five-screen focus/access.
Current examples also validate against unchanged backend Pydantic models, without database
access. See the [governance checkpoint](../hackathon/h2-governance-ui-review.md).

Real journeys still require the ADR-0034 identity/credential/origin/CSRF/header gates. History,
evidence and write HTTP routes are not activated. Uploads require real key/inspection/retention
providers. Rendered mobile/zoom/touch/reduced-motion acceptance, current frontend audit and
revision-bound CI/owner PR labels remain separate gates. No provider, cloud, monitoring,
signing, publication, licensing or deployment activation is included.
