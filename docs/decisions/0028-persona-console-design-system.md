# ADR-0028: Persona console, semantic tokens and fixture operations

**Status:** Proposed; owner authorized implementation, review/release gates remain.
**Date:** 2026-10-02

## Context

The owner approved a modern second pass of all five screens, investigation canvas,
AI-oriented assistance, lifecycle history, scalable tokens and mobile operations.
H1 remains browser-only. Internal backend services have no persona routes/trusted sessions.
Preview quality must not be mistaken for commercial readiness.

## Decision

- Semantic CSS tokens cover surfaces, text, borders, status, spacing, type, radii, layers
  and motion. Reuse system fonts, SVG, React/Next; introduce no runtime package.
- Responsive shell and contextual drawers use consistent focus, touch targets, empty/error
  states and reduced motion. Drawers trap focus, support Escape and restore trigger focus;
  background content is inert while open.
- Third-pass density, anchored footer and collapsible sidebar are recorded separately in
  [ADR-0029](0029-compact-persona-console.md).
- A typed reducer owns independent fixture records. Edits invalidate analysis/decisions and
  old notes. Version/history simulations stay tab-local; only bounded draft fields and
  selected fixture persist in browser storage. Approval grants/notes do not survive reload.
- Cancellable staged scans produce deterministic, labelled fixture findings and source-linked
  assistance. Geometry/palette overlays are illustrative, not facial identity checks. Edits,
  switches, interruptions and cancellation clear stale timers. Reduced motion keeps progress.
- Creator offers, recipient acceptance, withdrawal, revocation and current eligibility are
  separate. Demo role selection is scenario control, never authentication. Status derives
  from current fixture version/review, scope and simulated time window.
- Record/operations/assistant/command drawers explain internal capabilities and connection
  gaps without fabricated live backlog/receipts. Public projection/export uses a field
  allowlist and excludes private notes and any signature claim.

## Verification and boundaries

Tests cover record isolation/restoration, invalidation, actor/transition checks, scope/date
bounds, stale timers, cancellation/recovery, exports and keyboard behavior. Run frontend
lint/format/types/tests/build/bundle budget and repository gates. No heavy animation library,
external asset requests or hosted fonts. Browser/mobile accessibility and measured performance
remain required evidence; unit tests/bundle size cannot establish them.

No cloud, upload, model request, identity, signing, publication or deployment authorization.
Real adapters and service-backed end-to-end tests remain separate reviewed work. Backend
guards, audit trust and privacy boundaries are unchanged. This is not commercial release approval.
