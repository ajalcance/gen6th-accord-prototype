# ADR-0030: Task-focused persona console and explicit interaction states

**Status:** Proposed; owner authorized local implementation on 2026-10-02. PR review remains.
**Date:** 2026-10-02
**Builds on:** ADRs 0028 and 0029.

## Context

The owner requested an element-level refinement of all five screens: placement, purpose,
copy, typography, spacing, color, interaction and responsive behavior. A security-oriented
appearance must expose evidence and decisions without implying connected monitoring.

## Decision

- Keep the five-screen fixture journey and compact shell. Use navy surfaces, blue primary
  actions, cyan inspection/focus and separate semantic state colors. Preserve system fonts,
  readable metadata, coarse-pointer targets and reduced-motion support without new packages.
- Make gallery counts filter actual local records; add grid/list presentation and state-based
  next actions. Keep the five-column maximum and responsive workspace-container thresholds.
- Separate draft storage from committed fixture versions. Inspect supplied illustration data
  inline; describe unavailable uploads as status rather than a disabled action.
- Prioritize findings after a scan. Support captured pointer dragging and a native keyboard
  slider for palette comparison. Reference selection and disclosure expose accessible states.
- Keep review blockers beside decisions and align visual and keyboard order. Assistance is
  visibly scripted, with navigable source context and explicit application of reviewer notes.
- Put recipient decisions after scope; separate current eligibility and demo role/time controls.
  Require an inline confirmation naming the version, recipient and scope before revocation.
  Changes to the record, scope or party discard pending confirmation. Browser roles stay fixtures.
- Expose public/private preview selection explicitly. Group allowlisted export-field inspection
  with unsigned download; replace repetitive verification actions with factual status/details.
- Filter and expand real tab-local activity. Do not invent prior snapshots or server receipts.
  Commands focus search, navigate results by arrow keys and expose accurate empty states.
  Drawer focus includes disclosure summaries and excludes hidden disclosure descendants.

## Boundaries and verification

No backend behavior, storage schema, persona API, identity, monitoring, signing, cloud service,
publication or licence changes. No new dependencies. UI events remain browser-only; no server
emit/detection/audit/compliance decision changes. Existing uncommitted review units stay separate.

Tests cover the added interactions and preserve the original invalidation/privacy tests.
Run frontend checks, bundle budget, full repository gate and documentation checks. Source/DOM
tests cannot certify rendered geometry, pointer hardware, browser zoom or WCAG compliance.
The browser tool currently fails during sandbox initialization; retain owner visual acceptance
as an explicit remaining gate, and never bypass the sandbox to obtain a screenshot.

## Alternatives

Decorative threat feeds, live-looking security scores and fabricated charts were rejected:
they would communicate assurance unsupported by the disconnected prototype. Full historical
version diffs were deferred because tab history does not contain immutable content snapshots.
