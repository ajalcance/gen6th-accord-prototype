# ADR-0034: Prepare session-gated reads and a separate saved-record surface

**Status:** Proposed; owner authorized audit/authentication preparation and frontend read
integration on 2026-10-03. Identity/provider activation and PR/security review remain pending.
**Date:** 2026-10-03
**Builds on:** ADRs 0015 and 0032–0033.

## Context

The owner-backed 421-test checkpoint validates internal services. The console still cannot
display their records. Its browser-selected roles and the foundation's HMAC token scaffold
are not trusted persona identity. ADR-0015 forbids building a competing or fallback login;
Zynth inspection/integration remains deferred.

## Decision

- Prepare an injected session-verifier boundary, with no implementation, token minting or
  scaffold fallback. A provider must verify credentials, issuer/audience, current revocation,
  enabled account and human classification on every request. Its output includes bounded
  actor/session references and aware issuance/expiry; revalidate typed output and deny
  expired/future/ambiguous sessions. Provider absence/failure/three-second timeout is unavailable.
- Keep database membership as a separate per-request service check. No role, actor,
  verification result or server time comes from the query body. No new grants are introduced.
- Prepare an explicitly unregistered router factory for gallery and version reads. The
  application does not mount it. Use POST queries because service reads commit observations;
  no record GET route creates audit side effects (API-006). Existing registered actions apply.
- Declare bounded query and response models; strip invalid-input and dependency exception
  details from a consistent error response. Mark all responses `Cache-Control: no-store`.
- Prepare a same-origin typed HTTP adapter for these two operations only: no caching,
  redirects, implicit POST retries, token storage or unsupported writes/history operations.
  A reviewed credential/proxy bootstrap must inject the source; the home page supplies none.
- Expose “Browser fixtures” and “Saved records” separately. The latter explains its missing
  connection by default. An injected source can display bounded pages, explicit search,
  refresh, next-page navigation and read-only version details through actual runtime parsers.
  Never add portrait, review, permission, upload or signature claims to plain stored versions.
- Keep one page and one selected version in memory. Clear prior values on loading, leaving
  the list, access loss and session/workspace changes. Abort and ignore late responses; retry
  transient failures only through an explicit action. Never persist server records to localStorage.
  The trusted bootstrap must rotate `sessionKey` whenever the authenticated context changes.

## Verification and activation gates

Exercise session failures, current checks, invalid output, sanitized ASGI errors and default
route absence without Docker. Owner/CI PostgreSQL tests exercise actual query routes with an
explicit synthetic verifier: current records, actor attribution, cross-workspace denial and
membership/session loss. These tests do not verify real login or credentials.

Frontend tests exercise real gateway parsers/query state/rendered DOM using fictional wire
examples; HTTP tests exercise the shared client through a substituted network response.
Neither proves an authenticated browser journey or rendered mobile geometry.
Owner source-bound full `make check` passed on October 3: 454 backend tests / 96.55% coverage,
151 frontend tests, 11 docs-site tests, dependency audits and Go checks. Evidence is in
the [session/read checkpoint](../hackathon/h2-session-read-review.md); activation remains gated.

Before mounting/injecting: approved Zynth review and provider implementation; canonical
identity mapping; issuer/audience and revocation tests; session credential/proxy, origin/CSRF,
TLS and security-header review; quotas/timeouts; fresh database/audit proof after any new source.
Provider verification failures need the reviewed identity observation policy; this slice does
not pretend to record unauthenticated failures as trusted persona actors. Evidence providers,
analysis, signing, publication and deployment remain separately gated.
