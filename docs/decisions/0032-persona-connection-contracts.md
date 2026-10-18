# ADR-0032: Prepared persona transport and explicit mutation recovery

**Status:** Proposed; owner authorized preparation on 2026-10-02. Connection/PR review pending.
**Date:** 2026-10-02

## Context

The polished console is a browser fixture journey. Existing backend services enforce immutable
versions and independent decisions, but no trusted identity or persona HTTP routes exist.
Generic TypeScript response casts cannot validate those contracts at runtime.

## Decision

- Prepare a typed operation gateway for version save/load, review, campaign offer/decision and
  current eligibility. Require an explicitly injected transport; its default rejects as
  disconnected and makes no network request. Do not invent routes or reuse scaffold tokens.
- Parse commands and receipts at runtime, reject extra authority fields, validate fixture
  markers, UUIDs, bounded text/arrays, aware timestamps and exact tenant/version/scope bindings.
  Client validation supplements server enforcement; it never grants authority.
- Validate campaign eligibility against blocking reasons, linked decision actor and server
  evaluation time. Historical acceptance alone cannot become current permission.
- Keep a snapshot of mutation intent outside the editable draft. Pending prevents duplicate
  submissions. Explicit retries of network/timeout uncertainty reuse identical content and
  request ID. Conflicts require loading/reconciling the current record and a new explicit
  intent; never silently overwrite. Permission loss preserves drafts without retry loops.
- Cancellation stops waiting, not necessarily server commitment. Late responses cannot mark
  a cancelled request successful; resolving uncertainty uses the original idempotent intent.
  The shared HTTP client forwards caller cancellation and does not retry cancellations.
- Share fictional wire examples with backend Pydantic validation and frontend runtime tests.
  Contract/journey tests through an injected test transport are not authenticated network E2E.

## Boundaries

The console still uses its existing fixture reducer. Gallery listing, evidence transport,
history pagination, session-bound HTTP, real analysis and public projection/signing require
their own reviewed connection work. No UI control implies these preparatory adapters are live.
Zynth remains deferred. No credentials, cloud service or public routes are activated.
