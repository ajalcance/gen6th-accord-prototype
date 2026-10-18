# ADR-0039: Default workspace gallery without sample workflows

**Status:** Proposed; owner authorized UI implementation on 2026-10-04. PR review remains.
**Date:** 2026-10-04
**Builds on:** ADRs 0030, 0034, 0036 and 0037.

## Context

The owner requested a consolidated gallery layout: remove duplicate connection controls,
move review/passport guidance above the gallery, reduce search/display control sizes and
replace demo terminology. The owner explicitly chose an empty workspace gallery until real
records connect, with no sample workflows. Removing labels while retaining seeded personas
and scripted results would misrepresent the application's current capabilities.

## Decision

- Default `PassportStudio` renders `workspace-console.tsx`, with no seeded browser records,
  sample roles, scripted scans, example governance/recovery, unsigned sample exports or
  old browser-draft restoration. Existing browser storage is left untouched.
- Reuse `SavedGallery` and the explicit `SavedPersonaSource` context for record reads. No
  source means an empty/unavailable gallery, no network requests and no fabricated counters.
  A supplied source is not itself evidence of real identity or activated security monitoring.
- Keep Actions, Workspace guide and Create persona together in the header. Name the collection
  Records and individual entries Record in visible copy/navigation/accessibility labels, as
  subsequently requested by the owner. Preserve internal query identifiers for compatibility.
  Use one Records title/search/display row; remove summary panels, repeated labels and subtitle.
  Put passport guidance in the guide's FAQ. Replace the assistant with Workspace guide,
  which explains the workflow without simulating model answers or applying reviewer notes.
  Header actions use transparent borders/backgrounds, restrained text/accent colors and visible
  hover/focus feedback, matching the minimalist footer control treatment.
- Use a compact search field and icon-based Grid/List display group with accessible labels,
  pressed states, keyboard focus and 44-pixel touch targets. Supplied saved records support
  both views; changing display does not fetch again or change record authority.
- Monitoring in the persistent footer is the connection/readiness entry point. Remove header
  session status and other summary/sidebar/banner duplicates and fictional workspace identity.
- Creation stays unavailable until an authorized creation service exists. Review, campaign
  and passport navigation directs users to saved records, without running local simulations.
  Record-bound governance remains inside the selected saved-record workflow.
- Historical scenario tests explicitly inject `initialState`; the default page supplies none.
  This is a component test seam, not a URL, runtime setting, identity fallback or activation.
  Preserve prior scenario assertions and add acceptance tests for the actual default page.

## Boundaries and verification

No backend/DTO behavior, authentication, authority fields, signing, provider, upload, retention,
deployment, security policy or guard is changed. Existing backend fixture contracts remain
internal preparation; real connection is a separate reviewed implementation/activation step.
No package installation is required. Existing prepared write/session-loss semantics remain.

Run frontend tests/static checks/build/bundle budget, full gate and documentation guards.
Default-page tests cover no samples, no automatic requests, old-storage isolation, unavailable
creation, compact toolbar/header placement, footer readiness, FAQ/focus/keyboard access and supplied
record Grid/List behavior. Report these separately from browser geometry/zoom/touch acceptance
and real authenticated end-to-end proof. Owner visual acceptance remains required.

## Alternatives

Renaming the existing sample records as workspace records was rejected because it hides
simulation. Restoring authored local drafts was offered; the owner chose the empty gallery.
Activating prepared routes or adopting an identity/scanner provider would exceed this UI scope.
